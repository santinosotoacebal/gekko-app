"""
sentiment_expert.py
-------------------
Two-tier sentiment analysis:

  1. get_sentiment_score(ticker)      — fast deterministic simulation,
                                        used by ensemble.py for the final verdict.

  2. analyze_news_sentiment(ticker)   — real FinBERT inference via HuggingFace
                                        Transformers, used in the UI expert panel.
                                        Falls back to a neutral result if the model
                                        is not installed or no headlines are found.
"""
import numpy as np
import pandas as pd
import streamlit as st

# ── Optional transformers import ──────────────────────────────────────────────
try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_OK = True
except ImportError:
    _TRANSFORMERS_OK = False


# ── Model loader (cached for the entire Streamlit session) ────────────────────

@st.cache_resource(show_spinner=False)
def load_finbert():
    """
    Load ProsusAI/finbert once and keep it in memory for the session.
    Returns None if transformers / torch are not installed.
    """
    if not _TRANSFORMERS_OK:
        return None
    return hf_pipeline("sentiment-analysis", model="ProsusAI/finbert")


# ── News sentiment (real FinBERT) ─────────────────────────────────────────────

def _extract_title(item: dict) -> str:
    """Handle both yfinance v1 {'title': ...} and v2 {'content': {'title': ...}} shapes."""
    if "title" in item:
        return str(item["title"])
    content = item.get("content", {})
    if isinstance(content, dict):
        return str(content.get("title", ""))
    return ""


def analyze_news_sentiment(ticker: str) -> dict:
    """
    Fetch up to 10 recent headlines for *ticker* via yfinance,
    classify each with FinBERT, and return an aggregated verdict.

    Scoring:
        positive headline → +1
        negative headline → -1
        neutral  headline →  0

    Veredicto:
        score > 0  →  'Alcista'
        score < 0  →  'Bajista'
        score == 0 →  'Neutral'

    Returns {"valor": int, "veredicto": str, "titulos": list[str]}.
    """
    import yfinance as yf

    # ── Collect titles ────────────────────────────────────────────────────────
    try:
        raw = yf.Ticker(ticker).news[:10]
        titles = [_extract_title(item) for item in raw]
        titles = [t.strip() for t in titles if t.strip()]
    except Exception:
        titles = []

    if not titles:
        return {"valor": 0, "veredicto": "Neutral (Sin noticias)", "titulos": []}

    # ── Load model ────────────────────────────────────────────────────────────
    model = load_finbert()
    if model is None:
        return {
            "valor": 0,
            "veredicto": "Neutral (instala transformers y torch)",
            "titulos": titles,
        }

    # ── Inference ─────────────────────────────────────────────────────────────
    try:
        results = model(titles, truncation=True, max_length=512)
    except Exception as exc:
        return {"valor": 0, "veredicto": f"Neutral (error: {exc})", "titulos": titles}

    # ── Aggregate ─────────────────────────────────────────────────────────────
    score = 0
    for r in results:
        label = r["label"].lower()
        if label == "positive":
            score += 1
        elif label == "negative":
            score -= 1

    if score > 0:
        veredicto = "Alcista"
    elif score < 0:
        veredicto = "Bajista"
    else:
        veredicto = "Neutral"

    return {"valor": score, "veredicto": veredicto, "titulos": titles[:5]}


# ── Simulated sentiment (used by ensemble.py) ─────────────────────────────────

_HEADLINES: dict = {
    "AAPL":  ["Apple supera estimaciones de ingresos en Q4", "iPhone 16 bate récord de pre-órdenes"],
    "MSFT":  ["Microsoft Azure crece 29% interanual", "Copilot impulsa adopción empresarial"],
    "NVDA":  ["NVIDIA anuncia GPU H200 para centros de datos", "Demanda de IA eleva guías de NVDA"],
    "AMZN":  ["AWS reporta márgenes históricos", "Amazon Prime supera 200M de suscriptores"],
    "META":  ["Meta AI integrada en WhatsApp y Instagram", "Ventas de publicidad crecen 22%"],
    "TSLA":  ["Tesla reduce precios en mercados clave", "Producción del Cybertruck bajo expectativas"],
    "GOOGL": ["Google lanza Gemini Ultra 2.0", "Ingresos de Search crecen a doble dígito"],
    "AMD":   ["AMD gana contratos con grandes hiperescaladores", "EPYC 5 lidera en benchmarks de servidor"],
}
_DEFAULT_HEADLINES = [
    "Analistas elevan precio objetivo del activo",
    "Resultados superan estimaciones del consenso",
]


def get_sentiment_score(ticker: str) -> dict:
    """
    Deterministic simulated FinBERT scores.
    Stable within a trading day, used by the ensemble for the final verdict.
    """
    today_int = int(pd.Timestamp.now().strftime("%Y%m%d"))
    seed = (sum(ord(c) for c in ticker) * 31 + today_int) % (2 ** 31)
    rng  = np.random.default_rng(seed)

    positive = round(float(rng.uniform(0.30, 0.68)), 3)
    negative = round(float(rng.uniform(0.08, 0.35)), 3)
    neutral  = round(max(0.0, 1.0 - positive - negative), 3)
    net      = round(positive - negative, 3)

    if net > 0.18:
        signal, score, verdict = "POSITIVO",  1, "COMPRAR"
    elif net < -0.10:
        signal, score, verdict = "NEGATIVO", -1, "VENDER"
    else:
        signal, score, verdict = "NEUTRAL",   0, "NEUTRAL"

    return {
        "score":     score,
        "signal":    signal,
        "verdict":   verdict,
        "positive":  positive,
        "negative":  negative,
        "neutral":   neutral,
        "net":       net,
        "headlines": _HEADLINES.get(ticker, _DEFAULT_HEADLINES)[:2],
        "model":     "FinBERT (simulado)",
    }
