"""共用 UI helper：palette、plotly base、第一區渲染、加權合併、第二區渲染。

威力彩（ui_powerball）與大樂透（ui_lotto649）兩個分頁共用這裡的所有元件，
差異全部透過傳入的 LotteryConfig（cfg）表達，不複製邏輯。
"""

import streamlit as st
import plotly.graph_objects as go

from query_engine import (
    ROLLING, zone1_analysis, zone1_dual_combined, zone2_analysis,
    latest_two_draws,
)


PALETTE_B1 = ["#1f6feb", "#388bfd", "#58a6ff", "#79c0ff", "#a5d6ff", "#cae8ff"]
PALETTE_B2 = ["#e05c2a", "#f07a50", "#ffa657", "#ffbf85", "#ffd6b0", "#ffe8d4"]


def plotly_base():
    return dict(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", size=12), margin=dict(t=50, b=40, l=45, r=20),
    )


# ── 第一區：表 / 長條 / 折線 / section ──────────────────────────────────────────
def render_block_table(df, top_n, palette):
    count_cols = [c for c in df.columns if "次數" in c]
    show_cols  = ["排名", "號碼"] + count_cols + ["合計頻率%", f"近{ROLLING}期頻率%"]
    cfg = {
        "排名": st.column_config.NumberColumn("排名", width="small"),
        "號碼": st.column_config.NumberColumn("號碼", format="%02d"),
        "合計次數": st.column_config.ProgressColumn(
            "合計次數", min_value=0, max_value=int(df["合計次數"].max()), format="%d"
        ),
        "合計頻率%": st.column_config.NumberColumn("合計頻率%", format="%.1f %%"),
        f"近{ROLLING}期頻率%": st.column_config.NumberColumn(f"近{ROLLING}期頻率%", format="%.1f %%"),
    }
    for c in count_cols:
        cfg[c] = st.column_config.NumberColumn(c, format="%d")
    st.dataframe(df.head(top_n)[show_cols], column_config=cfg,
                 use_container_width=True, hide_index=True,
                 height=min(38, top_n) * 35 + 50)


def render_block_bar(df, top_n, palette, title):
    df_top = df.head(top_n)
    single_cols = [c for c in df_top.columns if "次數" in c and c != "合計次數"]
    fig = go.Figure()
    for i, col in enumerate(single_cols):
        fig.add_trace(go.Bar(
            name=col.replace("次數", ""), x=[f"{int(n):02d}" for n in df_top["號碼"]],
            y=df_top[col], marker_color=palette[i % len(palette)],
            hovertemplate="%{x}號　%{y}次<extra>" + col + "</extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13)),
        barmode="stack",
        xaxis=dict(title="號碼", gridcolor="#21262d"),
        yaxis=dict(title="出現次數", gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d",
                    orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0),
        height=360, **plotly_base(),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_block_line(df, label_color, baseline_pct):
    x_all = [f"{int(n):02d}" for n in df["號碼"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_all, y=df["合計頻率%"], mode="lines+markers",
        name="條件頻率%", line=dict(color=label_color, width=2), marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=x_all, y=df[f"近{ROLLING}期頻率%"], mode="lines+markers",
        name=f"近{ROLLING}期整體", line=dict(color="#f78166", width=1.5, dash="dot"),
        marker=dict(size=4),
    ))
    fig.add_hline(y=baseline_pct, line_dash="dash", line_color="#6e7681",
                  annotation_text=f"基準 {baseline_pct}%", annotation_position="top right",
                  annotation_font_color="#8b949e")
    fig.update_layout(
        xaxis=dict(title="號碼（依合計排名）", gridcolor="#21262d"),
        yaxis=dict(title="頻率 %", gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
        height=280, **plotly_base(),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_block_section(nums, label, badge_class, palette, label_color, top_n,
                         baseline_pct, cfg, lag=1):
    df, total_cond, T = zone1_analysis(nums, ROLLING, lag=lag, cfg=cfg)
    badges = "　".join(f'<span class="{badge_class}">#{x:02d}</span>' for x in nums)
    st.markdown(f"條件：{badges}", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("條件號碼數",    len(nums))
    k2.metric("條件出現總期次", total_cond)
    k3.metric("分析期數",      T)
    k4.metric("理論基準",      f"{baseline_pct} %")
    st.markdown("")
    col_t, col_b = st.columns([1, 1])
    with col_t:
        st.markdown("**候選號碼明細表**")
        render_block_table(df, top_n, palette)
    with col_b:
        render_block_bar(df, top_n, palette, f"{label}　加權合計次數（前{top_n}名）")
    render_block_line(df, label_color, baseline_pct)
    return df


# ── 綜合加權排名 ────────────────────────────────────────────────────────────────
def render_combined(b1_z1, b2_z1, top_n, cfg):
    st.markdown("#### ⚖️ 加權參數設定")
    wc1, wc2, _ = st.columns([2, 2, 3])
    with wc1:
        w1 = st.slider("第一區塊權重", 0, 10, 5, 1, key=f"{cfg.name}_comb_w1") / 10
    with wc2:
        w2 = round(1.0 - w1, 1)
        st.metric("第二區塊權重", f"{w2:.1f}")

    st.markdown(
        f'<div class="info-card">'
        f'當前比重：<b style="color:#58a6ff">第一區塊 {w1:.0%}</b>　'
        f'<b style="color:#ffa657">第二區塊 {w2:.0%}</b>　｜　'
        f'各區塊次數標準化至 [0,1] 後依比重加總。'
        f'</div>',
        unsafe_allow_html=True,
    )

    df_c = zone1_dual_combined(b1_z1, b2_z1, ROLLING, w1=w1, w2=w2, cfg=cfg)
    df_ct = df_c.head(top_n).copy()
    m1_max = df_c["B1次數"].max()
    m2_max = df_c["B2次數"].max()

    col_ct, col_sc = st.columns([1, 1])
    with col_ct:
        st.markdown("**綜合排名明細表**")
        cfg_c = {
            "排名": st.column_config.NumberColumn("排名", width="small"),
            "號碼": st.column_config.NumberColumn("號碼", format="%02d"),
            "B1次數": st.column_config.ProgressColumn("B1次數", min_value=0, max_value=int(m1_max), format="%d"),
            "B2次數": st.column_config.ProgressColumn("B2次數", min_value=0, max_value=int(m2_max), format="%d"),
            "B1頻率%": st.column_config.NumberColumn("B1頻率%", format="%.1f %%"),
            "B2頻率%": st.column_config.NumberColumn("B2頻率%", format="%.1f %%"),
            "綜合分數": st.column_config.ProgressColumn("綜合分數", min_value=0.0, max_value=1.0, format="%.4f"),
            f"近{ROLLING}期頻率%": st.column_config.NumberColumn(f"近{ROLLING}期頻率%", format="%.1f %%"),
        }
        show_c = ["排名","號碼","B1次數","B2次數","綜合分數","B1頻率%","B2頻率%",f"近{ROLLING}期頻率%"]
        st.dataframe(df_ct[show_c], column_config=cfg_c,
                     use_container_width=True, hide_index=True,
                     height=min(38, top_n)*35+50)

    with col_sc:
        st.markdown("**B1 vs B2 分佈圖（泡泡大小 = 綜合分數）**")
        df_c["_b1n"] = df_c["B1次數"] / m1_max if m1_max > 0 else 0
        df_c["_b2n"] = df_c["B2次數"] / m2_max if m2_max > 0 else 0
        in_top = df_c["排名"] <= top_n

        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(
            x=df_c.loc[~in_top, "_b1n"], y=df_c.loc[~in_top, "_b2n"],
            mode="markers+text",
            text=[f"{int(n):02d}" for n in df_c.loc[~in_top, "號碼"]],
            textposition="top center", textfont=dict(size=9, color="#6e7681"),
            marker=dict(size=df_c.loc[~in_top,"綜合分數"]*55+6,
                        color="#21262d", line=dict(color="#30363d", width=1)),
            name="排名外",
            hovertemplate="號碼 %{text}<br>B1: %{x:.3f}  B2: %{y:.3f}<extra></extra>",
        ))
        fig_sc.add_trace(go.Scatter(
            x=df_c.loc[in_top, "_b1n"], y=df_c.loc[in_top, "_b2n"],
            mode="markers+text",
            text=[f"{int(n):02d}" for n in df_c.loc[in_top, "號碼"]],
            textposition="top center", textfont=dict(size=10, color="#e6edf3"),
            marker=dict(
                size=df_c.loc[in_top,"綜合分數"]*60+10,
                color=df_c.loc[in_top,"綜合分數"],
                colorscale=[[0,"#1f6feb"],[0.5,"#39d353"],[1,"#ffa657"]],
                showscale=True, colorbar=dict(title="綜合分數", thickness=12, len=0.7),
                line=dict(color="#e6edf3", width=1),
            ),
            name=f"前{top_n}名",
            hovertemplate="號碼 %{text}<br>B1: %{x:.3f}  B2: %{y:.3f}<extra></extra>",
        ))
        fig_sc.update_layout(
            xaxis=dict(title=f"第一區塊標準分（權重 {w1:.0%}）", gridcolor="#21262d", range=[-0.05,1.15]),
            yaxis=dict(title=f"第二區塊標準分（權重 {w2:.0%}）", gridcolor="#21262d", range=[-0.05,1.15]),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            height=420, **plotly_base(),
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown(f"**綜合貢獻分解（前 {top_n} 名）**")
    fig_cb = go.Figure()
    fig_cb.add_trace(go.Bar(
        x=[f"{int(n):02d}" for n in df_ct["號碼"]],
        y=(df_ct["B1次數"] / m1_max * w1).round(4),
        name=f"第一區塊（{w1:.0%}）", marker_color="#1f6feb",
        hovertemplate="%{x}號　B1貢獻 %{y:.3f}<extra></extra>",
    ))
    fig_cb.add_trace(go.Bar(
        x=[f"{int(n):02d}" for n in df_ct["號碼"]],
        y=(df_ct["B2次數"] / m2_max * w2).round(4),
        name=f"第二區塊（{w2:.0%}）", marker_color="#ffa657",
        hovertemplate="%{x}號　B2貢獻 %{y:.3f}<extra></extra>",
    ))
    fig_cb.update_layout(
        barmode="stack",
        xaxis=dict(title="號碼（依綜合分數排名）", gridcolor="#21262d"),
        yaxis=dict(title="加權標準化分數", gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
        height=310, **plotly_base(),
    )
    st.plotly_chart(fig_cb, use_container_width=True)


# ── 第二區（威力彩第二區 / 大樂透特別號）────────────────────────────────────────
def render_zone2_section(b1_z2, b2_z2, both_z2, cfg):
    st.markdown('<div class="section-header">🎲 第二區分析結果</div>', unsafe_allow_html=True)

    z2_labels = []
    if b1_z2 is not None: z2_labels.append(f"🔵 第一區塊（#{b1_z2}）")
    if b2_z2 is not None: z2_labels.append(f"🟠 第二區塊（#{b2_z2}）")
    if both_z2:           z2_labels.append("⚖️ 合併比較")

    z2_tabs = st.tabs(z2_labels)
    tab_idx = 0

    if b1_z2 is not None:
        with z2_tabs[tab_idx]:
            _z2_single(b1_z2, "#58a6ff", cfg)
        tab_idx += 1

    if b2_z2 is not None:
        with z2_tabs[tab_idx]:
            _z2_single(b2_z2, "#ffa657", cfg)
        tab_idx += 1

    if both_z2:
        with z2_tabs[tab_idx]:
            _z2_compare(b1_z2, b2_z2, cfg)


def _z2_single(cond, label_color, cfg):
    df2z, n_c2 = zone2_analysis(cond, ROLLING, cfg=cfg)
    count_col = f"#{cond}次數"
    freq_col  = f"#{cond}頻率%"
    ov_col    = f"近{ROLLING}期頻率%"
    k1, k2, k3 = st.columns(3)
    k1.metric("條件樣本期數", n_c2)
    k2.metric("分析期數", ROLLING)
    k3.metric("理論基準", f"{cfg.z2_baseline_pct} %")
    ct, cc = st.columns([1, 1])
    with ct:
        st.dataframe(df2z, column_config={
            "排名": st.column_config.NumberColumn("排名", width="small"),
            count_col: st.column_config.ProgressColumn(
                count_col, min_value=0, max_value=int(df2z[count_col].max()), format="%d"),
            freq_col:  st.column_config.NumberColumn(freq_col,  format="%.1f %%"),
            ov_col:    st.column_config.NumberColumn(ov_col,    format="%.1f %%"),
        }, use_container_width=True, hide_index=True)
    with cc:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="條件頻率%", x=[str(w) for w in df2z["號碼"]], y=df2z[freq_col],
            marker=dict(color=df2z[freq_col],
                        colorscale=[[0,"#1f3a5f"],[0.5,label_color],[1,"#ffa657"]]),
            text=[f"{v:.1f}%" for v in df2z[freq_col]], textposition="outside",
            textfont=dict(color="#e6edf3", size=12),
        ))
        fig.add_trace(go.Scatter(
            name=ov_col, x=[str(w) for w in df2z["號碼"]], y=df2z[ov_col],
            mode="lines+markers", line=dict(color="#f78166", width=2, dash="dot"),
            marker=dict(size=7),
        ))
        fig.add_hline(y=cfg.z2_baseline_pct, line_dash="dash", line_color="#6e7681",
                      annotation_text=f"基準 {cfg.z2_baseline_pct}%", annotation_position="top right",
                      annotation_font_color="#8b949e")
        fig.update_layout(
            xaxis=dict(title="第二區號碼（依條件頻率排序）", gridcolor="#21262d"),
            yaxis=dict(title="頻率 %", gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            height=340, **plotly_base(),
        )
        st.plotly_chart(fig, use_container_width=True)


def _z2_compare(b1_z2, b2_z2, cfg):
    st.markdown("#### 兩個區塊第二區頻率合併比較")
    df2_b1_cmp, _ = zone2_analysis(b1_z2, ROLLING, cfg=cfg)
    df2_b2_cmp, _ = zone2_analysis(b2_z2, ROLLING, cfg=cfg)

    ov_col = f"近{ROLLING}期頻率%"
    merged_z2 = (
        df2_b1_cmp[["號碼", f"#{b1_z2}次數", f"#{b1_z2}頻率%", ov_col]]
        .merge(df2_b2_cmp[["號碼", f"#{b2_z2}次數", f"#{b2_z2}頻率%"]], on="號碼")
    )
    merged_z2["平均頻率%"] = (
        (merged_z2[f"#{b1_z2}頻率%"] + merged_z2[f"#{b2_z2}頻率%"]) / 2
    ).round(1)
    merged_z2 = merged_z2.sort_values("平均頻率%", ascending=False).reset_index(drop=True)
    merged_z2.insert(0, "排名", range(1, cfg.z2_max + 1))

    col_zt, col_zc = st.columns([1, 1])
    with col_zt:
        st.markdown("**合併排名表（依平均頻率排序）**")
        st.dataframe(
            merged_z2,
            column_config={
                "排名": st.column_config.NumberColumn("排名", width="small"),
                f"#{b1_z2}次數":  st.column_config.ProgressColumn(
                    f"B1 #{b1_z2}次數", min_value=0,
                    max_value=int(merged_z2[f"#{b1_z2}次數"].max()), format="%d"),
                f"#{b2_z2}次數":  st.column_config.ProgressColumn(
                    f"B2 #{b2_z2}次數", min_value=0,
                    max_value=int(merged_z2[f"#{b2_z2}次數"].max()), format="%d"),
                f"#{b1_z2}頻率%": st.column_config.NumberColumn(f"B1頻率%", format="%.1f %%"),
                f"#{b2_z2}頻率%": st.column_config.NumberColumn(f"B2頻率%", format="%.1f %%"),
                "平均頻率%":      st.column_config.NumberColumn("平均頻率%", format="%.1f %%"),
                ov_col:           st.column_config.NumberColumn(ov_col, format="%.1f %%"),
            },
            use_container_width=True, hide_index=True,
        )
    with col_zc:
        st.markdown("**B1 vs B2 頻率比較圖**")
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(
            name=f"B1 #{b1_z2}（lag-1）",
            x=[str(w) for w in df2_b1_cmp.sort_values("號碼")["號碼"]],
            y=df2_b1_cmp.sort_values("號碼")[f"#{b1_z2}頻率%"],
            marker_color="#1f6feb",
            hovertemplate="%{x}號　%{y:.1f}%<extra>B1</extra>",
        ))
        fig_cmp.add_trace(go.Bar(
            name=f"B2 #{b2_z2}（lag-2）",
            x=[str(w) for w in df2_b2_cmp.sort_values("號碼")["號碼"]],
            y=df2_b2_cmp.sort_values("號碼")[f"#{b2_z2}頻率%"],
            marker_color="#ffa657",
            hovertemplate="%{x}號　%{y:.1f}%<extra>B2</extra>",
        ))
        fig_cmp.add_hline(y=cfg.z2_baseline_pct, line_dash="dash", line_color="#6e7681",
                          annotation_text=f"基準 {cfg.z2_baseline_pct}%",
                          annotation_font_color="#8b949e")
        fig_cmp.update_layout(
            barmode="group",
            xaxis=dict(title="第二區號碼（號碼順序）", gridcolor="#21262d"),
            yaxis=dict(title="頻率 %", gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            height=360, **plotly_base(),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)


# ── 自動帶入最新/上一期號碼（draw_id 哨兵機制）────────────────────────────────
def seed_inputs(cfg, key_prefix: str) -> tuple[str, str, str, str]:
    """
    在 widget 建立『之前』呼叫。依 draw_id 哨兵決定是否種子化 4 個 widget。
    僅在「沒種過」或「最新 draw_id 改變（新一期）」時寫入 session_state，
    否則 no-op（保留使用者手改值）。
    回傳 (latest_id, latest_date, prev_id, prev_date)；無資料回 ("","","","")。
    """
    latest, prev, latest_id = latest_two_draws(cfg)
    p = key_prefix
    if latest is None:
        return ("", "", "", "")

    if st.session_state.get(f"{p}_seeded_id") != latest_id:
        st.session_state[f"{p}_b1_z1"] = list(latest["z1"])
        st.session_state[f"{p}_b1_z2"] = latest["z2"]
        st.session_state[f"{p}_b2_z1"] = list(prev["z1"]) if prev else []
        st.session_state[f"{p}_b2_z2"] = prev["z2"] if prev else None
        st.session_state[f"{p}_seeded_id"] = latest_id

    return (
        latest_id,
        latest["draw_date"],
        prev["draw_id"] if prev else "",
        prev["draw_date"] if prev else "",
    )


def reset_seed(key_prefix: str) -> None:
    """重設按鈕的 on_click callback：清哨兵，下一輪 seed_inputs 會重新種子。"""
    st.session_state.pop(f"{key_prefix}_seeded_id", None)


def render_seed_caption(info: tuple[str, str, str, str]) -> None:
    """顯示帶入提示。info 為 seed_inputs 的回傳值。"""
    latest_id, latest_date, prev_id, prev_date = info
    if not latest_id:
        st.caption("⚠️ 尚無開獎資料，未自動帶入。")
        return
    msg = f"🔄 已自動帶入最新一期 {latest_id}（{latest_date}）為第一區塊"
    if prev_id:
        msg += f"、上一期 {prev_id}（{prev_date}）為第二區塊"
    msg += "。手動修改後可按「↻ 帶回最新期」復原。"
    st.caption(msg)
