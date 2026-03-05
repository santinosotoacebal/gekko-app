"""
app.py  —  GEKKO v2 · Swing Trading Intelligence
Run with:  streamlit run app.py
"""
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GEKKO · Swing Trading",
    page_icon="assets/favicon.png" if False else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Typography: native system stack, no external font load ── */
html, body, [class*="css"], [class*="st-"] {
    font-family: system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

/* ── Hide Streamlit chrome ── */
#MainMenu        { visibility: hidden; }
footer           { visibility: hidden; }
header           { visibility: hidden; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Page layout ── */
.main .block-container {
    padding: 0 3.5rem 3rem 3.5rem;
    max-width: 1480px;
}

/* ── Top nav bar ── */
.top-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.4rem 0 1.2rem 0;
    border-bottom: 1px solid #E8EDF4;
    margin-bottom: 0;
}
.nav-brand {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0A1628;
    letter-spacing: -0.02em;
}
.nav-brand span { color: #2E6DA4; font-weight: 300; }
.nav-meta {
    font-size: 0.76rem;
    color: #A8B8C8;
    letter-spacing: 0.01em;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1.5px solid #E8EDF4;
    padding: 0;
    margin-bottom: 2rem;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.85rem 1.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: #8FA8C0;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    margin-bottom: -1.5px;
    letter-spacing: 0.01em;
    transition: color 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #1C2B3A; }
.stTabs [aria-selected="true"] {
    color: #0A1628 !important;
    border-bottom: 2px solid #2E6DA4 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"]    { display: none; }

/* ── Buttons (primary) ── */
.stButton > button {
    background: #0A1628 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.75rem !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s ease, box-shadow 0.15s ease !important;
    box-shadow: 0 1px 4px rgba(10,22,40,0.18) !important;
}
.stButton > button:hover {
    background: #1C3456 !important;
    box-shadow: 0 3px 10px rgba(10,22,40,0.22) !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1.5px solid #D8E3EE !important;
    padding: 0.6rem 0.9rem !important;
    font-size: 0.9rem !important;
    color: #0A1628 !important;
    background: #FFFFFF !important;
    transition: border 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2E6DA4 !important;
    box-shadow: 0 0 0 3px rgba(46,109,164,0.10) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #B0C0D0 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E8EDF4 !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.35rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04), 0 0 0 0 transparent !important;
}
[data-testid="metric-container"] label {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8FA8C0 !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: #2E6DA4 !important;
    border-radius: 4px !important;
}

/* ── Dividers ── */
hr { border-color: #E8EDF4 !important; margin: 1.6rem 0 !important; }

/* ── Expander ── */
details summary {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #4A6680 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Success / Error messages ── */
.stAlert { border-radius: 10px !important; font-size: 0.875rem !important; }

/* ── Custom classes ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9EB2C4;
    margin-bottom: 0.75rem;
}

/* Ticker cards (Radar) */
.ticker-card {
    background: #FFFFFF;
    border: 1px solid #E8EDF4;
    border-radius: 14px;
    padding: 1.5rem 1.2rem 1.3rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.ticker-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.07);
    transform: translateY(-2px);
}
.ticker-rank   { font-size: 0.68rem; font-weight: 600; color: #B0C0D0;
                 letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.4rem; }
.ticker-symbol { font-size: 1.55rem; font-weight: 700; color: #0A1628;
                 letter-spacing: -0.025em; }
.ticker-price  { font-size: 1rem; font-weight: 500; color: #4A6680; margin: 0.2rem 0 0.15rem; }
.prob-value    { font-size: 2rem; font-weight: 700; color: #2E6DA4; line-height: 1; margin: 0.7rem 0 0.1rem; }
.prob-label    { font-size: 0.68rem; color: #9EB2C4; letter-spacing: 0.08em; text-transform: uppercase; }
.badge {
    display: inline-block;
    margin-top: 0.8rem;
    padding: 3px 13px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-buy  { background: #EBF5F0; color: #1A6B44; }
.badge-sell { background: #FDECEA; color: #B53026; }
.badge-hold { background: #FDF5E4; color: #9A6B10; }

/* Expert cards (Deep Analysis) */
.expert-card {
    background: #F7F9FC;
    border: 1px solid #E8EDF4;
    border-radius: 12px;
    padding: 1.3rem 1.35rem;
    height: 100%;
}
.expert-title {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9EB2C4;
    margin-bottom: 0.5rem;
}
.expert-signal        { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.6rem; }
.signal-buy           { color: #1A6B44; }
.signal-sell          { color: #B53026; }
.signal-neutral       { color: #9A6B10; }
.expert-details       { font-size: 0.82rem; color: #4A6680; line-height: 1.85; }
.expert-details b     { color: #2A3F55; }

/* Verdict box */
.verdict-box {
    border-radius: 14px;
    padding: 2.2rem 2.5rem;
}
.verdict-buy  { background: #F0FAF4; border-left: 4px solid #27AE60; }
.verdict-sell { background: #FEF2F2; border-left: 4px solid #E53E3E; }
.verdict-hold { background: #FFFBF0; border-left: 4px solid #D97706; }
.verdict-eyebrow {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #9EB2C4; margin-bottom: 0.35rem;
}
.verdict-decision { font-size: 2.8rem; font-weight: 800; letter-spacing: -0.035em; line-height: 1.1; }
.verdict-buy  .verdict-decision { color: #1A6B44; }
.verdict-sell .verdict-decision { color: #B53026; }
.verdict-hold .verdict-decision { color: #9A6B10; }
.verdict-meta { display: flex; gap: 2.8rem; margin-top: 1.1rem; flex-wrap: wrap; }
.verdict-meta-item {}
.verdict-meta-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #9EB2C4;
}
.verdict-meta-value { font-size: 1.5rem; font-weight: 700; color: #0A1628; }
</style>
""",
    unsafe_allow_html=True,
)

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from modules.data_fetcher      import get_stock_data, get_stock_info, get_sp500_universe, bulk_download
from modules.technical_experts import analyze_macd, analyze_rsi, analyze_obv, analyze_bollinger, analyze_macro
from modules.sentiment_expert  import analyze_news_sentiment
from modules.ensemble          import calculate_final_decision, calculate_stop_loss


# ── CACHE ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    return get_stock_data(ticker, period)

@st.cache_data(ttl=300, show_spinner=False)
def _stock_info(ticker: str) -> dict:
    return get_stock_info(ticker)

@st.cache_data(ttl=300, show_spinner=False)
def _news_sentiment(ticker: str) -> dict:
    return analyze_news_sentiment(ticker)

@st.cache_data(ttl=86400, show_spinner=False)
def _sp500_universe():
    return get_sp500_universe()


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _delta_color(veredicto: str) -> str:
    v = veredicto.lower()
    if v.startswith("alcista"):
        return "normal"
    if v.startswith("bajista"):
        return "inverse"
    return "off"


# ── SPLASH SCREEN ────────────────────────────────────────────────────────────
_SPLASH_HTML = """
<style>
.splash-overlay {
    position: fixed;
    inset: 0;
    background: #FFFFFF;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 99999;
}
.splash-word {
    font-family: system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #111111;
    letter-spacing: 0.5em;
    text-indent: 0.5em;          /* compensates letter-spacing so it looks centred */
    text-transform: uppercase;
    animation: splashIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.splash-rule {
    width: 32px;
    height: 2px;
    background: #2E6DA4;
    margin-top: 1.6rem;
    border-radius: 2px;
    animation: splashIn 0.7s 0.15s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes splashIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
}
</style>
<div class="splash-overlay">
    <div class="splash-word">GEKKO</div>
    <div class="splash-rule"></div>
</div>
"""

if not st.session_state.get("app_loaded"):
    _placeholder = st.empty()
    _placeholder.markdown(_SPLASH_HTML, unsafe_allow_html=True)
    time.sleep(2.2)
    _placeholder.empty()
    st.session_state.app_loaded = True
    st.rerun()

# ── TOP NAV ───────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='top-nav'>"
    "<div class='nav-brand'>GEKKO<span> v2</span></div>"
    "<div class='nav-meta'>Datos: yfinance &nbsp;·&nbsp; Sentimiento: FinBERT (simulado)"
    "&nbsp;·&nbsp; No constituye asesoramiento financiero</div>"
    "</div>",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_radar, tab_analysis = st.tabs(["Radar de Oportunidades", "Análisis Profundo"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RADAR
# ══════════════════════════════════════════════════════════════════════════════
with tab_radar:
    st.markdown(
        "<div style='margin-bottom:0.25rem'>"
        "<span style='font-size:1.75rem;font-weight:700;color:#0A1628;letter-spacing:-0.03em'>"
        "Radar de Oportunidades</span></div>"
        "<div style='font-size:0.9rem;color:#6B8199;margin-bottom:1.8rem'>"
        "Escanea el S&amp;P 500 completo y filtra oportunidades con 5 expertos técnicos "
        "y análisis de sentimiento con FinBERT.</div>",
        unsafe_allow_html=True,
    )

    # Stats strip
    s1, s2, s3, _ = st.columns([1, 1, 1, 4])
    s1.metric("Universo",      "S&P 500")
    s2.metric("Filtro Técnico", "5 Expertos score ≥ 2")
    s3.metric("Filtro IA",      "Sentimiento Positivo")

    st.divider()

    btn_col, _ = st.columns([2, 6])
    scan_clicked = btn_col.button("Escanear Mercado", use_container_width=True)

    if scan_clicked:
        st.session_state.pop("radar_results", None)
        st.session_state.pop("radar_meta",    None)

        with st.status("Iniciando escaneo del S&P 500...", expanded=True) as _status:

            # ── Load universe ──────────────────────────────────────────────────
            _status.update(label="Obteniendo lista del S&P 500...")
            sp_tickers, sp_sectors = _sp500_universe()

            # ── Phase 1: bulk download + technical filter ──────────────────────
            _status.update(
                label=f"Fase 1: Descargando {len(sp_tickers)} acciones en bloque..."
            )
            raw = bulk_download(sp_tickers)

            def _score(v: str) -> int:
                v = v.lower()
                if v.startswith("alcista"): return 1
                if v.startswith("bajista"): return -1
                return 0

            phase1 = []
            for t in sp_tickers:
                try:
                    df_t = raw[t].dropna(subset=["Close"])
                    if len(df_t) < 30:
                        continue
                    macd_r  = analyze_macd(df_t)
                    rsi_r   = analyze_rsi(df_t)
                    obv_r   = analyze_obv(df_t)
                    boll_r  = analyze_bollinger(df_t)
                    macro_r = analyze_macro(df_t)
                    math_score = (
                        _score(macd_r["veredicto"])  +
                        _score(rsi_r["veredicto"])   +
                        _score(obv_r["veredicto"])   +
                        _score(boll_r["veredicto"])  +
                        _score(macro_r["veredicto"])
                    )
                    if math_score >= 2:
                        phase1.append({
                            "ticker":     t,
                            "sector":     sp_sectors.get(t, "S&P 500"),
                            "price":      round(float(df_t["Close"].iloc[-1]), 2),
                            "rsi":        rsi_r["valor"],
                            "math_score": math_score,
                        })
                except Exception:
                    continue

            # Keep top 10 by strongest consensus (highest math score)
            phase1.sort(key=lambda x: x["math_score"], reverse=True)
            finalists = phase1[:10]

            # ── Phase 2: FinBERT sentiment filter ─────────────────────────────
            winners = []
            for idx, c in enumerate(finalists, 1):
                _status.update(
                    label=(
                        f"Fase 2: Analizando sentimiento "
                        f"({idx}/{len(finalists)}) — {c['ticker']}..."
                    )
                )
                news_r = _news_sentiment(c["ticker"])
                if news_r["valor"] > 0:
                    c["news_score"]     = news_r["valor"]
                    c["news_veredicto"] = news_r["veredicto"]
                    c["total_score"]    = c["math_score"] + 1  # +1 FinBERT
                    winners.append(c)

            _status.update(
                label=f"Escaneo completo — {len(winners)} oportunidades detectadas",
                state="complete",
            )

        st.session_state["radar_results"] = winners
        st.session_state["radar_meta"] = {
            "total":     len(sp_tickers),
            "phase1":    len(phase1),
            "finalists": len(finalists),
            "winners":   len(winners),
        }

    # ── Display results ────────────────────────────────────────────────────────
    if "radar_results" in st.session_state:
        meta    = st.session_state.get("radar_meta", {})
        winners = st.session_state["radar_results"]

        if meta:
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3, m4, _ = st.columns([1, 1, 1, 1, 2])
            m1.metric("Universo",      f"{meta.get('total', 0):,} acciones")
            m2.metric("Fase 1",        f"{meta.get('phase1', 0)} candidatos")
            m3.metric("Finalistas",    f"{meta.get('finalists', 0)} acciones")
            m4.metric("Oportunidades", f"{meta.get('winners', 0)} ganadoras")

        st.divider()

        if not winners:
            st.markdown(
                "<div style='padding:2rem 0;text-align:center;color:#6B8199;"
                "font-size:0.9rem'>"
                "El filtro triple no encontró oportunidades claras en este momento. "
                "Inténtalo en otro horario de mercado.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='section-label'>Oportunidades Detectadas</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            for i in range(0, len(winners), 3):
                row  = winners[i:i+3]
                cols = st.columns(len(row), gap="medium")
                for col, w in zip(cols, row):
                    with col:
                        st.markdown(
                            f"""
                            <div style="background:#FBFBFC;border:1px solid #E8EDF4;
                                        border-radius:16px;padding:1.8rem 2rem;
                                        box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                                <div style="font-size:0.68rem;font-weight:600;
                                            letter-spacing:0.1em;text-transform:uppercase;
                                            color:#9EB2C4;margin-bottom:0.3rem;">
                                    {w.get('sector', 'S&P 500')}
                                </div>
                                <div style="font-size:2rem;font-weight:800;color:#0A1628;
                                            letter-spacing:-0.03em;line-height:1.1;
                                            margin-bottom:0.15rem;">
                                    {w['ticker']}
                                </div>
                                <div style="font-size:1.15rem;font-weight:500;color:#4A6680;
                                            margin-bottom:1.4rem;">
                                    ${w['price']:,.2f}
                                </div>
                                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                                    <div>
                                        <div style="font-size:0.65rem;font-weight:600;
                                                    letter-spacing:0.1em;text-transform:uppercase;
                                                    color:#9EB2C4;">Score</div>
                                        <div style="font-size:1.45rem;font-weight:700;
                                                    color:#2E6DA4;">{w['total_score']}/6</div>
                                    </div>
                                    <div>
                                        <div style="font-size:0.65rem;font-weight:600;
                                                    letter-spacing:0.1em;text-transform:uppercase;
                                                    color:#9EB2C4;">RSI</div>
                                        <div style="font-size:1.45rem;font-weight:700;
                                                    color:#0A1628;">{w['rsi']:.1f}</div>
                                    </div>
                                    <div>
                                        <div style="font-size:0.65rem;font-weight:600;
                                                    letter-spacing:0.1em;text-transform:uppercase;
                                                    color:#9EB2C4;">Sentimiento</div>
                                        <div style="font-size:1.45rem;font-weight:700;
                                                    color:#1A6B44;">+{w['news_score']}</div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                if i + 3 < len(winners):
                    st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALISIS PROFUNDO
# ══════════════════════════════════════════════════════════════════════════════
with tab_analysis:
    st.markdown(
        "<div style='margin-bottom:0.25rem'>"
        "<span style='font-size:1.75rem;font-weight:700;color:#0A1628;letter-spacing:-0.03em'>"
        "Análisis Profundo</span></div>"
        "<div style='font-size:0.9rem;color:#6B8199;margin-bottom:1.8rem'>"
        "Análisis técnico, de osciladores y de sentimiento con veredicto del ensemble.</div>",
        unsafe_allow_html=True,
    )

    inp_col, btn_col, _ = st.columns([2, 1, 5])
    ticker_raw = inp_col.text_input(
        "Ticker", value="AAPL", label_visibility="collapsed"
    )
    analyse = btn_col.button("Analizar", use_container_width=True)

    # Seed session on first load with the default value
    if "analysis_ticker" not in st.session_state:
        st.session_state["analysis_ticker"] = "AAPL"

    if analyse and ticker_raw.strip():
        st.session_state["analysis_ticker"] = ticker_raw.strip().upper()

    ticker = st.session_state["analysis_ticker"]

    # ── Fetch data ────────────────────────────────────────────────────────────
    with st.spinner(f"Cargando {ticker}..."):
        info = _stock_info(ticker)
        df   = _stock_data(ticker, period="6mo")

    if not info or df.empty:
        st.warning(f"Ticker **{ticker}** no encontrado. Verifica el símbolo e inténtalo de nuevo.")
        st.stop()

    st.divider()

    # ── Company & price header ────────────────────────────────────────────────
    h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    h1.metric("Empresa",          info["name"])
    h2.metric("Precio Actual",    f"${info['price']:,.2f}", f"{info['delta']:+.2f}%")
    h3.metric("Maximo 6 meses",   f"${float(df['Close'].max()):,.2f}")
    h4.metric("Minimo 6 meses",   f"${float(df['Close'].min()):,.2f}")
    h5.metric("Volumen Promedio", f"{int(df['Volume'].mean()):,}")

    st.divider()

    # ── Section 1: Candlestick chart ──────────────────────────────────────────
    st.markdown("<div class='section-label'>Grafico de Velas</div>", unsafe_allow_html=True)

    close = df["Close"]
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#2ecc71", width=1), fillcolor="#2ecc71"),
        decreasing=dict(line=dict(color="#e74c3c", width=1), fillcolor="#e74c3c"),
        name="OHLC",
        showlegend=False,
        hovertext=ticker,
    ))

    # SMA overlays
    fig.add_trace(go.Scatter(
        x=df.index, y=sma20,
        line=dict(color="#E8901A", width=1.5, dash="dot"),
        name="SMA 20",
        hovertemplate="SMA20 $%{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=sma50,
        line=dict(color="#7B5EA7", width=1.5, dash="dot"),
        name="SMA 50",
        hovertemplate="SMA50 $%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            rangeslider_visible=False,
            tickfont=dict(size=11, color="#9EB2C4"),
            linecolor="#E8EDF4",
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickprefix="$",
            tickfont=dict(size=11, color="#9EB2C4"),
            side="right",
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            font=dict(size=11, color="#6B8199"), bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Section 2: Expert verdicts ────────────────────────────────────────────
    st.markdown("<div class='section-label'>Veredicto de Expertos</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    macd_r  = analyze_macd(df)
    rsi_r   = analyze_rsi(df)
    obv_r   = analyze_obv(df)
    boll_r  = analyze_bollinger(df)
    macro_r = analyze_macro(df)

    with st.spinner("Analizando titulares con FinBERT..."):
        news_r = _news_sentiment(ticker)

    # ── Row 1 ─────────────────────────────────────────────────────────────────
    r1_1, r1_2, r1_3 = st.columns(3, gap="medium")
    with r1_1:
        st.metric(
            label="Experto Tendencia — MACD",
            value=f"{macd_r['valor']:.2f}",
            delta=macd_r["veredicto"],
            delta_color=_delta_color(macd_r["veredicto"]),
        )
    with r1_2:
        st.metric(
            label="Experto Oscilador — RSI",
            value=f"{rsi_r['valor']:.1f}",
            delta=rsi_r["veredicto"],
            delta_color=_delta_color(rsi_r["veredicto"]),
        )
    with r1_3:
        st.metric(
            label="Experto Noticias — FinBERT",
            value=str(news_r["valor"]),
            delta=news_r["veredicto"],
            delta_color=_delta_color(news_r["veredicto"]),
        )

    st.write("")

    # ── Row 2 ─────────────────────────────────────────────────────────────────
    r2_1, r2_2, r2_3 = st.columns(3, gap="medium")
    with r2_1:
        st.metric(
            label="Experto Volumen — OBV",
            value=f"{obv_r['valor']:+.1f}%",
            delta=obv_r["veredicto"],
            delta_color=_delta_color(obv_r["veredicto"]),
        )
    with r2_2:
        st.metric(
            label="Experto Volatilidad — Bollinger",
            value=f"{boll_r['valor']:.1f}%",
            delta=boll_r["veredicto"],
            delta_color=_delta_color(boll_r["veredicto"]),
        )
    with r2_3:
        st.metric(
            label="Experto Macro — SMA 50/200",
            value=f"{macro_r['valor']:+.2f}%",
            delta=macro_r["veredicto"],
            delta_color=_delta_color(macro_r["veredicto"]),
        )

    st.divider()

    # ── Section 3: Final verdict ──────────────────────────────────────────────
    st.markdown("<div class='section-label'>Veredicto Final del Ensemble</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    final   = calculate_final_decision(
        macd_r["veredicto"], rsi_r["veredicto"], news_r["veredicto"],
        obv_r["veredicto"],  boll_r["veredicto"], macro_r["veredicto"],
    )
    sl      = calculate_stop_loss(df, info["price"])

    st.markdown(
        f"""
        <div style="
            background: #FBFBFC;
            border: 1px solid #E8EDF4;
            border-radius: 16px;
            padding: 2.8rem 3rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: #9EB2C4;
                margin-bottom: 0.7rem;
            ">VEREDICTO GEKKO</div>
            <div style="
                font-size: 3.6rem;
                font-weight: 800;
                letter-spacing: -0.04em;
                line-height: 1;
                color: {final['color']};
                margin-bottom: 1.1rem;
            ">{final['decision']}</div>
            <div style="
                font-size: 0.95rem;
                color: #6B8199;
                font-weight: 400;
            ">Nivel de Riesgo Sugerido (Stop Loss): <strong style="color:#0A1628">${sl:,.2f}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
