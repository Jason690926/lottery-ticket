"""威力彩分頁：input + 第一區分析 + 第二區分析。

邏輯全部委派給 ui_shared 的共用元件，本檔只負責威力彩專屬的 input 與
版面（cfg=POWERBALL、widget key 前綴 pb_）。
"""

import sqlite3
from pathlib import Path

import streamlit as st

from query_engine import ROLLING, POWERBALL
from ui_shared import (
    PALETTE_B1, PALETTE_B2,
    render_block_section, render_combined, render_zone2_section,
    seed_inputs, reset_seed, render_seed_caption,
)


def _latest_draw_date() -> str:
    try:
        db = Path(__file__).parent / "lottery.db"
        conn = sqlite3.connect(db)
        date = conn.execute("SELECT MAX(draw_date) FROM draws").fetchone()[0]
        conn.close()
        return date or "—"
    except Exception:
        return "—"


def render():
    cfg = POWERBALL
    seed_info = seed_inputs(cfg, "pb")

    st.markdown(
        f'<div class="sub-title">POWERBALL CONDITIONAL FREQUENCY ANALYZER　｜　'
        f'滾動最近 <b style="color:#58a6ff">{ROLLING}</b> 期歷史資料　｜　'
        f'資料最新至 <b style="color:#3fb950">{_latest_draw_date()}</b></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── INPUT ──
    col_b1, col_div, col_b2 = st.columns([5, 0.2, 5])
    with col_b1:
        st.markdown('<div class="block-header block-b1">🔵 第一選號區塊　本期號碼（lag-1）</div>', unsafe_allow_html=True)
        b1_z1 = st.multiselect(
            "第一區號碼（1–38，最多 6 個）",
            options=list(range(1, cfg.z1_max + 1)),
            format_func=lambda x: f"{x:02d}",
            max_selections=6, placeholder="點選號碼…", key="pb_b1_z1",
        )
        b1_z2 = st.selectbox(
            "第二區號碼（1–8）",
            options=[None] + list(range(1, cfg.z2_max + 1)),
            format_func=lambda x: "── 請選擇 ──" if x is None else str(x),
            key="pb_b1_z2",
        )
    with col_b2:
        st.markdown('<div class="block-header block-b2">🟠 第二選號區塊　上一期號碼（lag-2）</div>', unsafe_allow_html=True)
        b2_z1 = st.multiselect(
            "第一區號碼（1–38，最多 6 個）",
            options=list(range(1, cfg.z1_max + 1)),
            format_func=lambda x: f"{x:02d}",
            max_selections=6, placeholder="點選號碼…", key="pb_b2_z1",
        )
        b2_z2 = st.selectbox(
            "第二區號碼（1–8）",
            options=[None] + list(range(1, cfg.z2_max + 1)),
            format_func=lambda x: "── 請選擇 ──" if x is None else str(x),
            key="pb_b2_z2",
        )

    render_seed_caption(seed_info)
    st.markdown("")
    _, c_run, c_reset, _ = st.columns([2, 2, 2, 2])
    with c_run:
        run = st.button("🔍　開始分析", use_container_width=True, type="primary", key="pb_run")
    with c_reset:
        st.button("↻　帶回最新期", use_container_width=True, key="pb_reset",
                  on_click=reset_seed, args=("pb",))

    both_z1  = bool(b1_z1 and b2_z1)
    any_z1   = bool(b1_z1 or  b2_z1)
    both_z2  = b1_z2 is not None and b2_z2 is not None
    any_z2   = b1_z2 is not None or  b2_z2 is not None

    st.divider()

    # ── ZONE 1 ──
    if any_z1:
        st.markdown('<div class="section-header">📊 第一區分析結果</div>', unsafe_allow_html=True)
        top_n = st.slider("顯示前 N 名候選號碼", 5, cfg.z1_max, 15, 1, key="pb_topn")

        if both_z1:
            tab1, tab2, tab3 = st.tabs([
                "🔵　第一區塊分析", "🟠　第二區塊分析", "⚖️　綜合加權排名",
            ])
        else:
            tabs = st.tabs(["🔵　第一區塊分析"] if b1_z1 else ["🟠　第二區塊分析"])
            tab1 = tabs[0] if b1_z1 else None
            tab2 = None    if b1_z1 else tabs[0]
            tab3 = None

        if tab1 and b1_z1:
            with tab1:
                render_block_section(
                    b1_z1, "第一區塊", "badge-b1", PALETTE_B1, "#58a6ff",
                    top_n, cfg.z1_baseline_pct, cfg, lag=1,
                )

        if tab2 and b2_z1:
            with tab2:
                st.markdown(
                    '<div class="info-card">📌 <b style="color:#c9d1d9">Lag-2（隔一期）</b>：'
                    '以「上一期號碼」為條件，統計歷史上間隔一期後的號碼出現頻率，'
                    '與第一區塊（lag-1）預測同一個下一期。</div>',
                    unsafe_allow_html=True,
                )
                render_block_section(
                    b2_z1, "第二區塊", "badge-b2", PALETTE_B2, "#ffa657",
                    top_n, cfg.z1_baseline_pct, cfg, lag=2,
                )

        if tab3 and both_z1:
            with tab3:
                render_combined(b1_z1, b2_z1, top_n, cfg)

        st.markdown(
            '<div class="warn-card">⚠️ <b style="color:#d29922">統計說明</b>：'
            '本系統基於歷史次數統計，所有條件頻率差異均未達統計顯著水準（31,396 項檢定 FDR 顯著 0 項）。'
            '本工具為有系統的選號參考，不具備預測能力。</div>',
            unsafe_allow_html=True,
        )
    elif run:
        st.info("請至少填入一個選號區塊的第一區號碼")

    st.divider()

    # ── ZONE 2 ──
    if any_z2:
        render_zone2_section(b1_z2, b2_z2, both_z2, cfg)
    elif run:
        st.info("請選擇至少一個區塊的第二區號碼")
