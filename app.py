import streamlit as st

import ui_powerball
import ui_lotto649


# ── 啟動時靜默更新資料庫（失敗不影響 app 運作）──
@st.cache_resource(show_spinner=False)
def _auto_update_db():
    for mod in ("update_db",):  # Task 16 會加 update_db_lotto649
        try:
            __import__(mod).main()
        except Exception:
            pass

_auto_update_db()

st.set_page_config(
    page_title="樂透條件篩選系統",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──
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

st.markdown('<div class="main-title">🎯 樂透條件篩選系統</div>', unsafe_allow_html=True)

# ── 頂層彩種 tab ──
tab_pb, tab_lt = st.tabs(["🎯　威力彩", "🍀　大樂透"])

with tab_pb:
    ui_powerball.render()

with tab_lt:
    ui_lotto649.render()
