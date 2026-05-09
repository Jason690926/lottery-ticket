import streamlit as st
import plotly.graph_objects as go

from query_engine import ROLLING, zone1_analysis, zone1_combined, zone2_analysis

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
    text-align: center;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #58a6ff;
    text-shadow: 0 0 24px #1f6feb99, 0 0 6px #58a6ff66;
    margin-bottom: 0.2rem;
}
.sub-title {
    text-align: center;
    color: #8b949e;
    font-size: 0.88rem;
    letter-spacing: 0.08em;
    margin-bottom: 1.2rem;
}
.info-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 6px;
    padding: 0.7rem 1.1rem;
    margin: 0.4rem 0 1rem 0;
    font-size: 0.85rem;
    color: #8b949e;
    line-height: 1.6;
}
.warn-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #d29922;
    border-radius: 6px;
    padding: 0.7rem 1.1rem;
    margin: 0.8rem 0 0.4rem 0;
    font-size: 0.82rem;
    color: #8b949e;
}
.section-header {
    font-size: 1.15rem;
    font-weight: 600;
    color: #58a6ff;
    border-bottom: 1px solid #21262d;
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
    letter-spacing: 0.05em;
}
.badge {
    display: inline-block;
    background: #1f6feb33;
    border: 1px solid #1f6feb88;
    border-radius: 12px;
    padding: 0.15rem 0.7rem;
    font-size: 0.82rem;
    color: #79c0ff;
    margin: 0.1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎯 威力彩條件篩選系統</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">POWERBALL CONDITIONAL FREQUENCY ANALYZER　｜　'
    f'滾動最近 <b style="color:#58a6ff">{ROLLING}</b> 期歷史資料</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="info-card">'
    '📌 <b style="color:#c9d1d9">使用方式</b>：輸入本期開出號碼 →'
    '  <b>Module 1</b> 查下一期頻率（lag-1）、'
    '  <b>Module 2</b> 查隔一期頻率（lag-2）、'
    '  <b>綜合加權</b> 合併兩模組排名。'
    '</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── Input ──────────────────────────────────────────────────────────────────────
col_z1, _, col_z2 = st.columns([5, 0.15, 2])

with col_z1:
    st.markdown('<div class="section-header">第一區　1–38 選 6</div>', unsafe_allow_html=True)
    z1_input = st.multiselect(
        "本期第一區號碼（最多 6 個）",
        options=list(range(1, 39)),
        format_func=lambda x: f"{x:02d}",
        max_selections=6,
        placeholder="點選號碼…",
    )

with col_z2:
    st.markdown('<div class="section-header">第二區　1–8 選 1</div>', unsafe_allow_html=True)
    z2_input = st.selectbox(
        "本期第二區號碼",
        options=[None] + list(range(1, 9)),
        format_func=lambda x: "── 請選擇 ──" if x is None else f"  {x}",
    )

st.markdown("")
_, btn_col, _ = st.columns([3, 2, 3])
with btn_col:
    run = st.button("🔍　開始分析", use_container_width=True, type="primary")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 1 — Tabs
# ══════════════════════════════════════════════════════════════════════════════
PALETTE = ["#1f6feb", "#388bfd", "#58a6ff", "#79c0ff", "#a5d6ff", "#cae8ff"]


def _plotly_base():
    return dict(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3", size=12),
        margin=dict(t=50, b=40, l=45, r=20),
    )


def _render_z1_tab(df: pd.DataFrame, total_cond: int, T: int, top_n: int, tab_key: str):
    """Shared rendering logic for M1 and M2 tabs."""
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("條件號碼數", len(z1_input))
    k2.metric("條件出現總期次", total_cond)
    k3.metric("分析期數", T)
    k4.metric("理論基準頻率", "15.8 %")

    st.markdown("")
    df_top = df.head(top_n).copy()

    col_tbl, col_bar = st.columns([1, 1])

    with col_tbl:
        st.markdown("**候選號碼明細表**")
        count_cols = [c for c in df_top.columns if "次數" in c]
        show_cols = ["排名", "號碼"] + count_cols + ["合計頻率%", f"近{ROLLING}期頻率%"]
        col_cfg = {
            "排名": st.column_config.NumberColumn("排名", width="small"),
            "號碼": st.column_config.NumberColumn("號碼", format="%02d"),
            "合計次數": st.column_config.ProgressColumn(
                "合計次數", min_value=0, max_value=int(df["合計次數"].max()), format="%d"
            ),
            "合計頻率%": st.column_config.NumberColumn("合計頻率%", format="%.1f %%"),
            f"近{ROLLING}期頻率%": st.column_config.NumberColumn(
                f"近{ROLLING}期頻率%", format="%.1f %%"
            ),
        }
        for c in count_cols:
            col_cfg[c] = st.column_config.NumberColumn(c, format="%d")
        st.dataframe(
            df_top[show_cols], column_config=col_cfg,
            use_container_width=True, hide_index=True,
            height=min(38, top_n) * 35 + 50,
        )

    with col_bar:
        st.markdown("**加權合計次數（堆疊長條）**")
        single_cols = [c for c in count_cols if c != "合計次數"]
        x_labels = [f"{int(n):02d}" for n in df_top["號碼"]]
        fig = go.Figure()
        for i, col in enumerate(single_cols):
            fig.add_trace(go.Bar(
                name=col.replace("次數", ""),
                x=x_labels, y=df_top[col],
                marker_color=PALETTE[i % len(PALETTE)],
                hovertemplate="%{x}號　%{y}次<extra>" + col + "</extra>",
            ))
        fig.update_layout(
            barmode="stack",
            xaxis=dict(title="號碼", gridcolor="#21262d"),
            yaxis=dict(title="出現次數", gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d",
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=390,
            **_plotly_base(),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Frequency line chart
    st.markdown("**條件頻率% vs 近期整體頻率%（全 38 號，依合計排名排序）**")
    x_all = [f"{int(n):02d}" for n in df["號碼"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=x_all, y=df["合計頻率%"],
        mode="lines+markers", name="條件合計頻率%",
        line=dict(color="#39d353", width=2), marker=dict(size=5),
        hovertemplate="%{x}號　%{y:.1f}%<extra>條件頻率</extra>",
    ))
    fig2.add_trace(go.Scatter(
        x=x_all, y=df[f"近{ROLLING}期頻率%"],
        mode="lines+markers", name=f"近{ROLLING}期整體頻率%",
        line=dict(color="#f78166", width=1.8, dash="dot"), marker=dict(size=4),
        hovertemplate="%{x}號　%{y:.1f}%<extra>整體頻率</extra>",
    ))
    fig2.add_hline(y=15.8, line_dash="dash", line_color="#6e7681",
                   annotation_text="理論基準 15.8%", annotation_position="top right",
                   annotation_font_color="#8b949e")
    if top_n < 38:
        fig2.add_vline(x=top_n - 0.5, line_dash="dot", line_color="#d29922",
                       annotation_text=f"前{top_n}名", annotation_font_color="#d29922")
    fig2.update_layout(
        xaxis=dict(title="號碼（依合計次數排名）", gridcolor="#21262d"),
        yaxis=dict(title="頻率 %", gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
        height=300,
        **_plotly_base(),
    )
    st.plotly_chart(fig2, use_container_width=True)


if z1_input:
    badges = "　".join(f'<span class="badge">#{x:02d}</span>' for x in z1_input)
    st.markdown(
        f'<div class="section-header">📊 第一區分析結果　條件：{badges}</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs([
        "📈　Module 1 — 下一期（lag-1）",
        "📉　Module 2 — 隔一期（lag-2）",
        "⚖️　綜合加權排名",
    ])

    top_n = st.slider("顯示前 N 名候選號碼", 5, 38, 15, 1, key="top_n")

    with tab1:
        df1, total1, T1 = zone1_analysis(z1_input, ROLLING, lag=1)
        _render_z1_tab(df1, total1, T1, top_n, "m1")

    with tab2:
        df2, total2, T2 = zone1_analysis(z1_input, ROLLING, lag=2)
        st.markdown(
            '<div class="info-card">📌 <b style="color:#c9d1d9">Lag-2</b>：'
            '條件為「本期含 x」，統計的是<b>隔一期</b>（跳過下一期）各號出現頻率。'
            '</div>',
            unsafe_allow_html=True,
        )
        _render_z1_tab(df2, total2, T2, top_n, "m2")

    with tab3:
        st.markdown("#### 加權參數設定")
        w_col1, w_col2, _ = st.columns([2, 2, 3])
        with w_col1:
            w1 = st.slider("Module 1 權重（lag-1）", 0, 10, 6, 1, key="w1") / 10
        with w_col2:
            w2 = round(1.0 - w1, 1)
            st.metric("Module 2 權重（lag-2）", f"{w2:.1f}")

        st.markdown(
            f'<div class="info-card">'
            f'當前比重：<b style="color:#58a6ff">M1 = {w1:.0%}</b>　'
            f'<b style="color:#ffa657">M2 = {w2:.0%}</b>　｜　'
            f'各模組次數先標準化至 [0,1]，再依比重加總得綜合分數。'
            f'</div>',
            unsafe_allow_html=True,
        )

        df_comb = zone1_combined(z1_input, ROLLING, w1=w1, w2=w2)
        df_top_c = df_comb.head(top_n).copy()

        col_ct, col_sc = st.columns([1, 1])

        with col_ct:
            st.markdown("**綜合排名明細表**")
            col_cfg_c = {
                "排名": st.column_config.NumberColumn("排名", width="small"),
                "號碼": st.column_config.NumberColumn("號碼", format="%02d"),
                "M1次數": st.column_config.ProgressColumn(
                    "M1次數", min_value=0, max_value=int(df_comb["M1次數"].max()), format="%d"
                ),
                "M2次數": st.column_config.ProgressColumn(
                    "M2次數", min_value=0, max_value=int(df_comb["M2次數"].max()), format="%d"
                ),
                "M1頻率%": st.column_config.NumberColumn("M1頻率%", format="%.1f %%"),
                "M2頻率%": st.column_config.NumberColumn("M2頻率%", format="%.1f %%"),
                "綜合分數": st.column_config.ProgressColumn(
                    "綜合分數", min_value=0.0, max_value=1.0, format="%.4f"
                ),
                f"近{ROLLING}期頻率%": st.column_config.NumberColumn(
                    f"近{ROLLING}期頻率%", format="%.1f %%"
                ),
            }
            show_c = ["排名", "號碼", "M1次數", "M2次數", "綜合分數",
                      "M1頻率%", "M2頻率%", f"近{ROLLING}期頻率%"]
            st.dataframe(
                df_top_c[show_c], column_config=col_cfg_c,
                use_container_width=True, hide_index=True,
                height=min(38, top_n) * 35 + 50,
            )

        with col_sc:
            st.markdown("**M1 vs M2 分佈圖（泡泡大小 = 綜合分數）**")
            # Normalise for scatter axes
            m1_max = df_comb["M1次數"].max()
            m2_max = df_comb["M2次數"].max()
            df_comb["_m1n"] = df_comb["M1次數"] / m1_max if m1_max > 0 else 0
            df_comb["_m2n"] = df_comb["M2次數"] / m2_max if m2_max > 0 else 0

            in_top = df_comb["排名"] <= top_n
            fig_sc = go.Figure()
            # Non-top numbers (grey)
            fig_sc.add_trace(go.Scatter(
                x=df_comb.loc[~in_top, "_m1n"],
                y=df_comb.loc[~in_top, "_m2n"],
                mode="markers+text",
                text=[f"{int(n):02d}" for n in df_comb.loc[~in_top, "號碼"]],
                textposition="top center",
                textfont=dict(size=9, color="#6e7681"),
                marker=dict(
                    size=df_comb.loc[~in_top, "綜合分數"] * 60 + 6,
                    color="#21262d", line=dict(color="#30363d", width=1),
                ),
                name="排名外",
                hovertemplate="號碼 %{text}<br>M1: %{x:.3f}<br>M2: %{y:.3f}<extra></extra>",
            ))
            # Top-N numbers (coloured)
            fig_sc.add_trace(go.Scatter(
                x=df_comb.loc[in_top, "_m1n"],
                y=df_comb.loc[in_top, "_m2n"],
                mode="markers+text",
                text=[f"{int(n):02d}" for n in df_comb.loc[in_top, "號碼"]],
                textposition="top center",
                textfont=dict(size=10, color="#e6edf3"),
                marker=dict(
                    size=df_comb.loc[in_top, "綜合分數"] * 60 + 10,
                    color=df_comb.loc[in_top, "綜合分數"],
                    colorscale=[[0, "#1f6feb"], [0.5, "#39d353"], [1, "#ffa657"]],
                    showscale=True,
                    colorbar=dict(title="綜合分數", thickness=12, len=0.7),
                    line=dict(color="#e6edf3", width=1),
                ),
                name=f"前{top_n}名",
                hovertemplate="號碼 %{text}<br>M1: %{x:.3f}<br>M2: %{y:.3f}<extra></extra>",
            ))
            fig_sc.update_layout(
                xaxis=dict(title=f"M1 標準化分數（lag-1，權重 {w1:.0%}）",
                           gridcolor="#21262d", range=[-0.05, 1.15]),
                yaxis=dict(title=f"M2 標準化分數（lag-2，權重 {w2:.0%}）",
                           gridcolor="#21262d", range=[-0.05, 1.15]),
                legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
                height=430,
                **_plotly_base(),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        # Combined bar chart
        st.markdown(f"**綜合分數排名（前 {top_n} 名）**")
        fig_cb = go.Figure()
        fig_cb.add_trace(go.Bar(
            x=[f"{int(n):02d}" for n in df_top_c["號碼"]],
            y=df_top_c["M1次數"] / m1_max * w1,
            name=f"M1 貢獻（{w1:.0%}）",
            marker_color="#1f6feb",
            hovertemplate="%{x}號　M1貢獻 %{y:.3f}<extra></extra>",
        ))
        fig_cb.add_trace(go.Bar(
            x=[f"{int(n):02d}" for n in df_top_c["號碼"]],
            y=df_top_c["M2次數"] / m2_max * w2,
            name=f"M2 貢獻（{w2:.0%}）",
            marker_color="#ffa657",
            hovertemplate="%{x}號　M2貢獻 %{y:.3f}<extra></extra>",
        ))
        fig_cb.update_layout(
            barmode="stack",
            xaxis=dict(title="號碼（依綜合分數排名）", gridcolor="#21262d"),
            yaxis=dict(title="加權標準化分數", gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            height=320,
            **_plotly_base(),
        )
        st.plotly_chart(fig_cb, use_container_width=True)

    st.markdown(
        '<div class="warn-card">'
        '⚠️ <b style="color:#d29922">統計說明</b>：本系統條件頻率基於歷史次數統計。'
        '研究確認（31,396 項檢定 FDR 顯著 0 項），所有條件頻率差異均未達統計顯著水準。'
        '本工具提供有系統的選號參考，不具備預測能力。'
        '</div>',
        unsafe_allow_html=True,
    )

elif run:
    st.info("請先選擇第一區號碼")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 2
# ══════════════════════════════════════════════════════════════════════════════
if z2_input is not None:
    df2z, n_c2 = zone2_analysis(z2_input, ROLLING)

    st.markdown('<div class="section-header">🎲 第二區分析結果</div>', unsafe_allow_html=True)
    st.markdown(
        f'條件號碼：<span class="badge" style="border-color:#ffa65788;color:#ffa657">'
        f'第二區 #{z2_input}</span>',
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("條件樣本期數", n_c2)
    k2.metric("分析期數", ROLLING)
    k3.metric("理論基準頻率", "12.5 %")

    st.markdown("")
    col_t2, col_c2 = st.columns([1, 1])
    count_col   = f"#{z2_input}次數"
    freq_col    = f"#{z2_input}頻率%"
    overall_col = f"近{ROLLING}期頻率%"

    with col_t2:
        st.markdown("**第二區下期頻率排名**")
        st.dataframe(
            df2z,
            column_config={
                "排名": st.column_config.NumberColumn("排名", width="small"),
                count_col: st.column_config.ProgressColumn(
                    count_col, min_value=0, max_value=int(df2z[count_col].max()), format="%d"
                ),
                freq_col:    st.column_config.NumberColumn(freq_col,    format="%.1f %%"),
                overall_col: st.column_config.NumberColumn(overall_col, format="%.1f %%"),
            },
            use_container_width=True, hide_index=True,
        )

    with col_c2:
        st.markdown("**條件頻率% vs 整體頻率%**")
        fig_z2 = go.Figure()
        fig_z2.add_trace(go.Bar(
            name="條件頻率%",
            x=[str(w) for w in df2z["號碼"]],
            y=df2z[freq_col],
            marker=dict(
                color=df2z[freq_col],
                colorscale=[[0, "#1f3a5f"], [0.5, "#1f6feb"], [1, "#ffa657"]],
            ),
            text=[f"{v:.1f}%" for v in df2z[freq_col]],
            textposition="outside",
            textfont=dict(color="#e6edf3", size=12),
        ))
        fig_z2.add_trace(go.Scatter(
            name=f"近{ROLLING}期整體頻率%",
            x=[str(w) for w in df2z["號碼"]],
            y=df2z[overall_col],
            mode="lines+markers",
            line=dict(color="#f78166", width=2, dash="dot"),
            marker=dict(size=7),
        ))
        fig_z2.add_hline(y=12.5, line_dash="dash", line_color="#6e7681",
                         annotation_text="理論基準 12.5%", annotation_position="top right",
                         annotation_font_color="#8b949e")
        fig_z2.update_layout(
            xaxis=dict(title="第二區號碼（依條件頻率排序）", gridcolor="#21262d"),
            yaxis=dict(title="頻率 %", gridcolor="#21262d"),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d"),
            height=360,
            **_plotly_base(),
        )
        st.plotly_chart(fig_z2, use_container_width=True)

elif run:
    st.info("請先選擇第二區號碼")
