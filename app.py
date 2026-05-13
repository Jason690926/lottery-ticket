import streamlit as st
import plotly.graph_objects as go

import sqlite3
from pathlib import Path

from query_engine import ROLLING, zone1_analysis, zone1_dual_combined, zone2_analysis

# 啟動時靜默更新資料庫（失敗不影響 app 運作）
@st.cache_resource(show_spinner=False)
def _auto_update_db():
    try:
        import update_db
        update_db.main()
    except Exception:
        pass

_auto_update_db()

st.set_page_config(
    page_title="威力彩條件篩選系統",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-title {
    text-align: center; font-size: 2.2rem; font-weight: 700;
    letter-spacing: 0.18em; color: #58a6ff;
    text-shadow: 0 0 24px #1f6feb99, 0 0 6px #58a6ff66;
    margin-bottom: 0.2rem;
}
.sub-title {
    text-align: center; color: #8b949e; font-size: 0.88rem;
    letter-spacing: 0.08em; margin-bottom: 1.2rem;
}
.info-card {
    background: #161b22; border: 1px solid #30363d;
    border-left: 3px solid #58a6ff; border-radius: 6px;
    padding: 0.7rem 1.1rem; margin: 0.4rem 0 0.8rem 0;
    font-size: 0.85rem; color: #8b949e; line-height: 1.6;
}
.warn-card {
    background: #161b22; border: 1px solid #30363d;
    border-left: 3px solid #d29922; border-radius: 6px;
    padding: 0.7rem 1.1rem; margin: 0.8rem 0 0.4rem 0;
    font-size: 0.82rem; color: #8b949e;
}
.block-header {
    font-size: 1.05rem; font-weight: 700; letter-spacing: 0.06em;
    padding: 0.5rem 1rem; border-radius: 6px; margin-bottom: 0.6rem;
    text-align: center;
}
.block-b1 { background: #1f3a5f; color: #79c0ff; border: 1px solid #1f6feb88; }
.block-b2 { background: #3a1f1f; color: #ffa657; border: 1px solid #ff6b3588; }
.section-header {
    font-size: 1.1rem; font-weight: 600; color: #58a6ff;
    border-bottom: 1px solid #21262d; padding-bottom: 0.35rem;
    margin-bottom: 0.8rem; letter-spacing: 0.05em;
}
.badge-b1 {
    display:inline-block; background:#1f6feb33; border:1px solid #1f6feb88;
    border-radius:12px; padding:0.12rem 0.65rem; font-size:0.82rem;
    color:#79c0ff; margin:0.1rem;
}
.badge-b2 {
    display:inline-block; background:#ff6b3533; border:1px solid #ff6b3588;
    border-radius:12px; padding:0.12rem 0.65rem; font-size:0.82rem;
    color:#ffa657; margin:0.1rem;
}
</style>
""", unsafe_allow_html=True)

PALETTE_B1 = ["#1f6feb", "#388bfd", "#58a6ff", "#79c0ff", "#a5d6ff", "#cae8ff"]
PALETTE_B2 = ["#e05c2a", "#f07a50", "#ffa657", "#ffbf85", "#ffd6b0", "#ffe8d4"]


def _plotly_base():
    return dict(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", size=12), margin=dict(t=50, b=40, l=45, r=20),
    )


# ── Header ─────────────────────────────────────────────────────────────────────
def _latest_draw_date() -> str:
    try:
        db = Path(__file__).parent / "lottery.db"
        conn = sqlite3.connect(db)
        date = conn.execute("SELECT MAX(draw_date) FROM draws").fetchone()[0]
        conn.close()
        return date or "—"
    except Exception:
        return "—"

st.markdown('<div class="main-title">🎯 威力彩條件篩選系統</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">POWERBALL CONDITIONAL FREQUENCY ANALYZER　｜　'
    f'滾動最近 <b style="color:#58a6ff">{ROLLING}</b> 期歷史資料　｜　'
    f'資料最新至 <b style="color:#3fb950">{_latest_draw_date()}</b></div>',
    unsafe_allow_html=True,
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  INPUT — 兩個區塊並排
# ══════════════════════════════════════════════════════════════════════════════
col_b1, col_div, col_b2 = st.columns([5, 0.2, 5])

with col_b1:
    st.markdown('<div class="block-header block-b1">🔵 第一選號區塊　本期號碼（lag-1）</div>', unsafe_allow_html=True)
    b1_z1 = st.multiselect(
        "第一區號碼（1–38，最多 6 個）",
        options=list(range(1, 39)),
        format_func=lambda x: f"{x:02d}",
        max_selections=6,
        placeholder="點選號碼…",
        key="b1_z1",
    )
    b1_z2 = st.selectbox(
        "第二區號碼（1–8）",
        options=[None] + list(range(1, 9)),
        format_func=lambda x: "── 請選擇 ──" if x is None else str(x),
        key="b1_z2",
    )

with col_b2:
    st.markdown('<div class="block-header block-b2">🟠 第二選號區塊　上一期號碼（lag-2）</div>', unsafe_allow_html=True)
    b2_z1 = st.multiselect(
        "第一區號碼（1–38，最多 6 個）",
        options=list(range(1, 39)),
        format_func=lambda x: f"{x:02d}",
        max_selections=6,
        placeholder="點選號碼…",
        key="b2_z1",
    )
    b2_z2 = st.selectbox(
        "第二區號碼（1–8）",
        options=[None] + list(range(1, 9)),
        format_func=lambda x: "── 請選擇 ──" if x is None else str(x),
        key="b2_z2",
    )

st.markdown("")
_, btn_col, _ = st.columns([3, 2, 3])
with btn_col:
    run = st.button("🔍　開始分析", use_container_width=True, type="primary")

both_z1  = bool(b1_z1 and b2_z1)
any_z1   = bool(b1_z1 or  b2_z1)
both_z2  = b1_z2 is not None and b2_z2 is not None
any_z2   = b1_z2 is not None or  b2_z2 is not None

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  SHARED RENDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _render_block_table(df, top_n, palette):
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


def _render_block_bar(df, top_n, palette, title):
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
        height=360, **_plotly_base(),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_block_line(df, label_color):
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
    fig.add_hline(y=15.8, line_dash="dash", line_color="#6e7681",
                  annotation_text="基準 15.8%", annotation_position="top right",
                  annotation_font_color="#8b949e")
    fig.update_layout(
        xaxis=dict(title="號碼（依合計排名）", gridcolor="#21262d"),
        yaxis=dict(title="頻率 %", gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
        height=280, **_plotly_base(),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_block_section(nums, label, badge_class, palette, label_color, top_n, lag=1):
    df, total_cond, T = zone1_analysis(nums, ROLLING, lag=lag)
    badges = "　".join(f'<span class="{badge_class}">#{x:02d}</span>' for x in nums)
    st.markdown(f"條件：{badges}", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("條件號碼數",    len(nums))
    k2.metric("條件出現總期次", total_cond)
    k3.metric("分析期數",      T)
    k4.metric("理論基準",      "15.8 %")
    st.markdown("")
    col_t, col_b = st.columns([1, 1])
    with col_t:
        st.markdown("**候選號碼明細表**")
        _render_block_table(df, top_n, palette)
    with col_b:
        _render_block_bar(df, top_n, palette, f"{label}　加權合計次數（前{top_n}名）")
    _render_block_line(df, label_color)
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 1 ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
if any_z1:
    st.markdown('<div class="section-header">📊 第一區分析結果</div>', unsafe_allow_html=True)

    top_n = st.slider("顯示前 N 名候選號碼", 5, 38, 15, 1)

    # Decide tabs
    if both_z1:
        tab1, tab2, tab3 = st.tabs([
            "🔵　第一區塊分析",
            "🟠　第二區塊分析",
            "⚖️　綜合加權排名",
        ])
    else:
        tabs = st.tabs(["🔵　第一區塊分析"] if b1_z1 else ["🟠　第二區塊分析"])
        tab1 = tabs[0] if b1_z1 else None
        tab2 = None    if b1_z1 else tabs[0]
        tab3 = None

    if tab1 and b1_z1:
        with tab1:
            df_b1 = _render_block_section(
                b1_z1, "第一區塊", "badge-b1", PALETTE_B1, "#58a6ff", top_n, lag=1
            )

    if tab2 and b2_z1:
        with tab2:
            st.markdown(
                '<div class="info-card">📌 <b style="color:#c9d1d9">Lag-2（隔一期）</b>：'
                '以「上一期號碼」為條件，統計歷史上間隔一期後的號碼出現頻率，'
                '與第一區塊（lag-1）預測同一個下一期。</div>',
                unsafe_allow_html=True,
            )
            df_b2 = _render_block_section(
                b2_z1, "第二區塊", "badge-b2", PALETTE_B2, "#ffa657", top_n, lag=2
            )

    if tab3 and both_z1:
        with tab3:
            st.markdown("#### ⚖️ 加權參數設定")
            wc1, wc2, _ = st.columns([2, 2, 3])
            with wc1:
                w1 = st.slider("第一區塊權重", 0, 10, 5, 1, key="comb_w1") / 10
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

            df_c = zone1_dual_combined(b1_z1, b2_z1, ROLLING, w1=w1, w2=w2)
            df_ct = df_c.head(top_n).copy()

            m1_max = df_c["B1次數"].max()
            m2_max = df_c["B2次數"].max()

            col_ct, col_sc = st.columns([1, 1])

            with col_ct:
                st.markdown("**綜合排名明細表**")
                cfg_c = {
                    "排名": st.column_config.NumberColumn("排名", width="small"),
                    "號碼": st.column_config.NumberColumn("號碼", format="%02d"),
                    "B1次數": st.column_config.ProgressColumn(
                        "B1次數", min_value=0, max_value=int(m1_max), format="%d"),
                    "B2次數": st.column_config.ProgressColumn(
                        "B2次數", min_value=0, max_value=int(m2_max), format="%d"),
                    "B1頻率%": st.column_config.NumberColumn("B1頻率%", format="%.1f %%"),
                    "B2頻率%": st.column_config.NumberColumn("B2頻率%", format="%.1f %%"),
                    "綜合分數": st.column_config.ProgressColumn(
                        "綜合分數", min_value=0.0, max_value=1.0, format="%.4f"),
                    f"近{ROLLING}期頻率%": st.column_config.NumberColumn(
                        f"近{ROLLING}期頻率%", format="%.1f %%"),
                }
                show_c = ["排名","號碼","B1次數","B2次數","綜合分數",
                          "B1頻率%","B2頻率%",f"近{ROLLING}期頻率%"]
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
                        showscale=True,
                        colorbar=dict(title="綜合分數", thickness=12, len=0.7),
                        line=dict(color="#e6edf3", width=1),
                    ),
                    name=f"前{top_n}名",
                    hovertemplate="號碼 %{text}<br>B1: %{x:.3f}  B2: %{y:.3f}<extra></extra>",
                ))
                fig_sc.update_layout(
                    xaxis=dict(title=f"第一區塊標準分（權重 {w1:.0%}）",
                               gridcolor="#21262d", range=[-0.05,1.15]),
                    yaxis=dict(title=f"第二區塊標準分（權重 {w2:.0%}）",
                               gridcolor="#21262d", range=[-0.05,1.15]),
                    legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
                    height=420, **_plotly_base(),
                )
                st.plotly_chart(fig_sc, use_container_width=True)

            # Stacked contribution bar
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
                height=310, **_plotly_base(),
            )
            st.plotly_chart(fig_cb, use_container_width=True)

    st.markdown(
        '<div class="warn-card">⚠️ <b style="color:#d29922">統計說明</b>：'
        '本系統基於歷史次數統計，所有條件頻率差異均未達統計顯著水準（31,396 項檢定 FDR 顯著 0 項）。'
        '本工具為有系統的選號參考，不具備預測能力。</div>',
        unsafe_allow_html=True,
    )

elif run:
    st.info("請至少填入一個選號區塊的第一區號碼")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 2
# ══════════════════════════════════════════════════════════════════════════════
if any_z2:
    st.markdown('<div class="section-header">🎲 第二區分析結果</div>', unsafe_allow_html=True)

    z2_tabs = []
    z2_labels = []
    if b1_z2 is not None:
        z2_labels.append(f"🔵 第一區塊（#{b1_z2}）")
    if b2_z2 is not None:
        z2_labels.append(f"🟠 第二區塊（#{b2_z2}）")
    if both_z2:
        z2_labels.append("⚖️ 合併比較")

    z2_tabs = st.tabs(z2_labels)
    tab_idx = 0

    def _render_z2(cond, tab, label_color):
        df2z, n_c2 = zone2_analysis(cond, ROLLING)
        count_col = f"#{cond}次數"
        freq_col  = f"#{cond}頻率%"
        ov_col    = f"近{ROLLING}期頻率%"
        k1, k2, k3 = tab.columns(3)
        k1.metric("條件樣本期數", n_c2)
        k2.metric("分析期數", ROLLING)
        k3.metric("理論基準", "12.5 %")
        ct, cc = tab.columns([1, 1])
        with ct:
            tab.dataframe(df2z, column_config={
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
            fig.add_hline(y=12.5, line_dash="dash", line_color="#6e7681",
                          annotation_text="基準 12.5%", annotation_position="top right",
                          annotation_font_color="#8b949e")
            fig.update_layout(
                xaxis=dict(title="第二區號碼（依條件頻率排序）", gridcolor="#21262d"),
                yaxis=dict(title="頻率 %", gridcolor="#21262d"),
                legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
                height=340, **_plotly_base(),
            )
            tab.plotly_chart(fig, use_container_width=True)
        return df2z

    if b1_z2 is not None:
        with z2_tabs[tab_idx]:
            df2_b1 = _render_z2(b1_z2, z2_tabs[tab_idx], "#58a6ff")
        tab_idx += 1

    if b2_z2 is not None:
        with z2_tabs[tab_idx]:
            df2_b2 = _render_z2(b2_z2, z2_tabs[tab_idx], "#ffa657")
        tab_idx += 1

    if both_z2:
        with z2_tabs[tab_idx]:
            st.markdown("#### 兩個區塊第二區頻率合併比較")
            df2_b1_cmp, n_c_b1 = zone2_analysis(b1_z2, ROLLING)
            df2_b2_cmp, n_c_b2 = zone2_analysis(b2_z2, ROLLING)

            # ── 排名合併表 ────────────────────────────────────────────
            ov_col = f"近{ROLLING}期頻率%"
            merged_z2 = (
                df2_b1_cmp[["號碼", f"#{b1_z2}次數", f"#{b1_z2}頻率%", ov_col]]
                .merge(
                    df2_b2_cmp[["號碼", f"#{b2_z2}次數", f"#{b2_z2}頻率%"]],
                    on="號碼",
                )
            )
            merged_z2["平均頻率%"] = (
                (merged_z2[f"#{b1_z2}頻率%"] + merged_z2[f"#{b2_z2}頻率%"]) / 2
            ).round(1)
            merged_z2 = merged_z2.sort_values("平均頻率%", ascending=False).reset_index(drop=True)
            merged_z2.insert(0, "排名", range(1, 9))

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
                    use_container_width=True,
                    hide_index=True,
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
                fig_cmp.add_hline(y=12.5, line_dash="dash", line_color="#6e7681",
                                  annotation_text="基準 12.5%", annotation_font_color="#8b949e")
                fig_cmp.update_layout(
                    barmode="group",
                    xaxis=dict(title="第二區號碼（號碼順序）", gridcolor="#21262d"),
                    yaxis=dict(title="頻率 %", gridcolor="#21262d"),
                    legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
                    height=360, **_plotly_base(),
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

elif run:
    st.info("請選擇至少一個區塊的第二區號碼")
