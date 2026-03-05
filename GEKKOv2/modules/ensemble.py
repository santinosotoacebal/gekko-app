"""
ensemble.py
-----------
Weighted-voting ensemble that combines the three expert modules.

Also provides `simulate_radar_scan` — a fast, fully-simulated scan
used by the Radar mode so the UI never blocks on 20 yfinance calls.
"""
import numpy as np
import pandas as pd

from modules.technical_experts import get_technical_verdict, get_oscillator_verdict
from modules.sentiment_expert  import get_sentiment_score
from modules.data_fetcher      import BASE_PRICES, TECH_TICKERS


# ── WEIGHTS ───────────────────────────────────────────────────────────────────
WEIGHTS = {"technical": 0.45, "oscillators": 0.35, "sentiment": 0.20}
MAX_TECH_SCORE = 3.5   # practical maximum |score| from get_technical_verdict
MAX_OSC_SCORE  = 2.0   # practical maximum |score| from get_oscillator_verdict


# ── DEEP ANALYSIS ENSEMBLE ────────────────────────────────────────────────────

def get_ensemble_verdict(ticker: str) -> dict:
    """
    Fetch real indicator data for *ticker* and return full verdict dict.
    Called only in Análisis Profundo mode.
    """
    technical   = get_technical_verdict(ticker)
    oscillators = get_oscillator_verdict(ticker)
    sentiment   = get_sentiment_score(ticker)

    # Normalise each score to [-1, +1]
    tech_norm = np.clip(technical["score"]   / MAX_TECH_SCORE, -1, 1)
    osc_norm  = np.clip(oscillators["score"] / MAX_OSC_SCORE,  -1, 1)
    sent_norm = float(np.clip(sentiment["score"], -1, 1))

    weighted = (
        tech_norm  * WEIGHTS["technical"]  +
        osc_norm   * WEIGHTS["oscillators"] +
        sent_norm  * WEIGHTS["sentiment"]
    )
    weighted = round(float(weighted), 4)

    # Map weighted score [-1,+1] → probability [0,100]
    probability = round((weighted + 1) / 2 * 100, 1)

    if weighted >= 0.18:
        decision   = "COMPRAR"
        risk_level = "BAJO"    if weighted > 0.40 else "MEDIO"
        confidence = min(int(probability), 95)
    elif weighted <= -0.18:
        decision   = "VENDER"
        risk_level = "ALTO"
        confidence = min(int(100 - probability), 95)
    else:
        decision   = "MANTENER"
        risk_level = "MEDIO"
        confidence = 50

    return {
        "decision":    decision,
        "confidence":  confidence,
        "probability": probability,
        "weighted":    weighted,
        "risk_level":  risk_level,
        "technical":   technical,
        "oscillators": oscillators,
        "sentiment":   sentiment,
    }


# ── DIRECT VERDICT FUNCTIONS (consume UI-level expert outputs) ───────────────

def calculate_final_decision(
    macd_verdict: str,
    rsi_verdict: str,
    finbert_verdict: str,
    obv_verdict: str,
    bollinger_verdict: str,
    macro_verdict: str,
) -> dict:
    """
    Point-based voting from 6 expert signals (score range -6 to +6).

    Scoring rule:
        'Alcista*'  →  +1
        'Neutral*'  →   0
        'Bajista*'  →  -1

    Decisions:
        score >= +4        →  COMPRA FUERTE   (#1A5C35)
        score == +2 or +3  →  COMPRAR         (#1A6B44)
        score -1 to +1     →  MANTENER        (#4A6680)
        score == -2 or -3  →  VENDER          (#B53026)
        score <= -4        →  VENTA FUERTE    (#8B1A12)

    Returns {"decision", "score", "positive_count", "probability", "color"}.
    """
    def _to_score(v: str) -> int:
        v = v.lower()
        if v.startswith("alcista"):
            return 1
        if v.startswith("bajista"):
            return -1
        return 0

    scores = [
        _to_score(macd_verdict),
        _to_score(rsi_verdict),
        _to_score(finbert_verdict),
        _to_score(obv_verdict),
        _to_score(bollinger_verdict),
        _to_score(macro_verdict),
    ]
    total          = sum(scores)
    positive_count = sum(1 for s in scores if s > 0)
    probability    = round(positive_count / 6 * 100, 1)

    if total >= 4:
        decision, color = "COMPRA FUERTE", "#1A5C35"
    elif total >= 2:
        decision, color = "COMPRAR",       "#1A6B44"
    elif total >= -1:
        decision, color = "MANTENER",      "#4A6680"
    elif total >= -3:
        decision, color = "VENDER",        "#B53026"
    else:
        decision, color = "VENTA FUERTE",  "#8B1A12"

    return {
        "decision":       decision,
        "score":          total,
        "positive_count": positive_count,
        "probability":    probability,
        "color":          color,
    }


def calculate_stop_loss(df: pd.DataFrame, current_price: float) -> float:
    """
    ATR-based stop loss for a long position.

    ATR = 14-period Average True Range
    Stop Loss = current_price - 1.5 × ATR

    Returns the stop-loss price rounded to 2 decimal places.
    """
    high       = df["High"]
    low        = df["Low"]
    prev_close = df["Close"].shift(1)

    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    atr = float(true_range.rolling(14).mean().iloc[-1])
    return round(current_price - 1.5 * atr, 2)


# ── SIMULATED RADAR SCAN ──────────────────────────────────────────────────────

def simulate_radar_scan(tickers=None) -> list:
    """
    Deterministic simulated scan (no network calls).
    Scores shift daily so results feel fresh each session.
    Returns ALL tickers sorted by probability (caller slices top-N).
    """
    if tickers is None:
        tickers = TECH_TICKERS

    today_int = int(pd.Timestamp.now().strftime("%Y%m%d"))
    results   = []

    for ticker in tickers:
        seed = (sum(ord(c) for c in ticker) * 31 + today_int) % (2 ** 31)
        rng  = np.random.default_rng(seed)

        base  = BASE_PRICES.get(ticker, 100.0)
        price = round(base * float(rng.uniform(0.93, 1.07)), 2)
        chg   = round(float(rng.uniform(-2.8, 4.5)), 2)
        prob  = round(float(rng.uniform(38, 94)), 1)
        vol   = round(float(rng.uniform(0.7, 2.8)), 2)

        if prob >= 68:
            signal = "COMPRAR"
        elif prob <= 42:
            signal = "VENDER"
        else:
            signal = "MANTENER"

        results.append({
            "ticker":       ticker,
            "price":        price,
            "change_pct":   chg,
            "probability":  prob,
            "signal":       signal,
            "vol_factor":   vol,
        })

    results.sort(key=lambda x: x["probability"], reverse=True)
    return results
