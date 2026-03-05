"""
technical_experts.py
--------------------
Pure-Python technical indicator calculations.
No Streamlit dependency — safe to import anywhere.
"""
import numpy as np
import pandas as pd
from modules.data_fetcher import get_stock_data


# ── INDICATORS ────────────────────────────────────────────────────────────────

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_macd(
    series: pd.Series,
    fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast   = series.ewm(span=fast,   adjust=False).mean()
    ema_slow   = series.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    series: pd.Series, period: int = 20, std_dev: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    middle = series.rolling(period).mean()
    std    = series.rolling(period).std()
    return middle + std * std_dev, middle, middle - std * std_dev


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


# ── TREND EXPERT ──────────────────────────────────────────────────────────────

def get_technical_verdict(ticker: str) -> dict:
    """
    Analyse ticker with trend-following indicators.
    Returns a standardised dict: score ∈ [-3, +3], signal, detail fields.
    """
    df = get_stock_data(ticker, period="1y")

    if df.empty or len(df) < 30:
        return _neutral_verdict("Datos insuficientes")

    close = df["Close"]
    score = 0.0

    # ── RSI ──
    rsi_val = float(calculate_rsi(close).iloc[-1])
    if rsi_val < 30:
        rsi_label, score = "Sobrevendido", score + 1.0
    elif rsi_val > 70:
        rsi_label, score = "Sobrecomprado", score - 1.0
    else:
        rsi_label = "Neutral"

    # ── MACD ──
    _, _, hist = calculate_macd(close)
    h_now, h_prev = float(hist.iloc[-1]), float(hist.iloc[-2])
    if h_now > 0 and h_prev <= 0:
        macd_label, score = "Cruce Alcista", score + 1.0
    elif h_now < 0 and h_prev >= 0:
        macd_label, score = "Cruce Bajista", score - 1.0
    elif h_now > 0:
        macd_label, score = "Momentum Positivo", score + 0.5
    else:
        macd_label, score = "Momentum Negativo", score - 0.5

    # ── Bollinger Bands ──
    upper, _, lower = calculate_bollinger_bands(close)
    bb_pct = (close.iloc[-1] - float(lower.iloc[-1])) / max(
        float(upper.iloc[-1]) - float(lower.iloc[-1]), 1e-9
    ) * 100
    if bb_pct < 15:
        bb_label, score = "Cerca de Banda Inferior", score + 0.5
    elif bb_pct > 85:
        bb_label, score = "Cerca de Banda Superior", score - 0.5
    else:
        bb_label = f"Rango Medio ({bb_pct:.0f}%)"

    # ── SMA Trend ──
    sma50  = float(calculate_sma(close, 50).iloc[-1])
    sma200 = float(calculate_sma(close, min(200, len(close))).iloc[-1])
    price  = float(close.iloc[-1])
    if price > sma50 > sma200:
        trend_label, score = "Tendencia Alcista", score + 1.0
    elif price < sma50 < sma200:
        trend_label, score = "Tendencia Bajista", score - 1.0
    elif price > sma50:
        trend_label, score = "Por Encima SMA50", score + 0.5
    else:
        trend_label = "Por Debajo SMA50"

    if score >= 1.5:
        signal = "COMPRAR"
    elif score <= -1.5:
        signal = "VENDER"
    else:
        signal = "NEUTRAL"

    return {
        "score":       round(score, 2),
        "signal":      signal,
        "rsi":         round(rsi_val, 1),
        "rsi_label":   rsi_label,
        "macd_label":  macd_label,
        "bb_label":    bb_label,
        "trend_label": trend_label,
        "sma50":       round(sma50, 2),
        "sma200":      round(sma200, 2),
    }


# ── OSCILLATOR EXPERT ─────────────────────────────────────────────────────────

def get_oscillator_verdict(ticker: str) -> dict:
    """
    Analyse ticker with oscillator-based indicators.
    Returns standardised dict: score ∈ [-2, +2].
    """
    df = get_stock_data(ticker, period="3mo")

    if df.empty or len(df) < 20:
        return _neutral_verdict("Datos insuficientes")

    close  = df["Close"]
    volume = df["Volume"]
    score  = 0.0

    # ── Stochastic RSI ──
    rsi    = calculate_rsi(close)
    lo14   = rsi.rolling(14).min()
    hi14   = rsi.rolling(14).max()
    rng    = (hi14 - lo14).replace(0, np.nan)
    stoch  = float(((rsi - lo14) / rng * 100).fillna(50).iloc[-1])

    if stoch < 20:
        stoch_label, score = "Zona de Compra", score + 1.0
    elif stoch > 80:
        stoch_label, score = "Zona de Venta", score - 1.0
    else:
        stoch_label = f"Neutral ({stoch:.0f})"

    # ── ADX proxy (normalised trend strength) ──
    rets = close.pct_change().dropna()
    roll_mean = rets.rolling(14).mean().iloc[-1]
    roll_std  = rets.rolling(14).std().iloc[-1]
    adx_proxy = float(
        min(abs(roll_mean / roll_std) * 50, 100) if (roll_std and roll_std > 0) else 25
    )
    direction = 1 if roll_mean > 0 else -1
    if adx_proxy > 25:
        score += 0.5 * direction
        adx_label = f"Tendencia Fuerte ({adx_proxy:.0f})"
    else:
        adx_label = f"Mercado Lateral ({adx_proxy:.0f})"

    # ── Volume ──
    vol_avg  = float(volume.rolling(20).mean().iloc[-1])
    vol_now  = float(volume.iloc[-1])
    vol_ratio = vol_now / vol_avg if vol_avg > 0 else 1.0
    if vol_ratio > 1.5:
        vol_label, score = f"Volumen Alto {vol_ratio:.1f}x", score + 0.5
    elif vol_ratio < 0.6:
        vol_label = f"Volumen Bajo {vol_ratio:.1f}x"
    else:
        vol_label = f"Volumen Normal {vol_ratio:.1f}x"

    if score >= 1.0:
        signal = "COMPRAR"
    elif score <= -1.0:
        signal = "VENDER"
    else:
        signal = "NEUTRAL"

    return {
        "score":       round(score, 2),
        "signal":      signal,
        "stoch_rsi":   round(stoch, 1),
        "stoch_label": stoch_label,
        "adx":         round(adx_proxy, 1),
        "adx_label":   adx_label,
        "vol_ratio":   round(vol_ratio, 2),
        "vol_label":   vol_label,
    }


# ── PUBLIC ANALYSIS FUNCTIONS (accept DataFrame directly) ────────────────────

def analyze_macd(df: pd.DataFrame) -> dict:
    """
    Compute MACD(12, 26, 9) from an OHLCV DataFrame.

    Veredicto:
        MACD > Signal  →  'Alcista'
        MACD <= Signal →  'Bajista'

    Returns {"valor": float, "señal": float, "veredicto": str}.
    """
    close = df["Close"]
    macd_line, signal_line, _ = calculate_macd(close)
    valor     = round(float(macd_line.iloc[-1]),   4)
    señal     = round(float(signal_line.iloc[-1]), 4)
    veredicto = "Alcista" if valor > señal else "Bajista"
    return {"valor": valor, "señal": señal, "veredicto": veredicto}


def analyze_rsi(df: pd.DataFrame, periods: int = 14) -> dict:
    """
    Compute RSI(periods) from an OHLCV DataFrame.

    Veredicto:
        RSI < 30  →  'Alcista (Sobrevendido)'
        RSI > 70  →  'Bajista (Sobrecomprado)'
        else      →  'Neutral'

    Returns {"valor": float, "veredicto": str}.
    """
    close = df["Close"]
    rsi_series = calculate_rsi(close, period=periods)
    valor = round(float(rsi_series.iloc[-1]), 2)
    if valor < 30:
        veredicto = "Alcista (Sobrevendido)"
    elif valor > 70:
        veredicto = "Bajista (Sobrecomprado)"
    else:
        veredicto = "Neutral"
    return {"valor": valor, "veredicto": veredicto}


def analyze_obv(df: pd.DataFrame) -> dict:
    """
    On-Balance Volume vs its 20-period SMA.

    Alcista if OBV > OBV_SMA20 (money flowing in).
    Bajista otherwise.

    valor = % deviation of OBV from its SMA20.
    Returns {"valor": float, "veredicto": str}.
    """
    close     = df["Close"]
    volume    = df["Volume"]
    direction = np.sign(close.diff().fillna(0))
    obv       = (direction * volume).cumsum()
    obv_sma20 = obv.rolling(20).mean()

    obv_now = float(obv.iloc[-1])
    sma_now = float(obv_sma20.iloc[-1])

    denom = abs(sma_now) if abs(sma_now) > 0 else 1.0
    valor = round((obv_now - sma_now) / denom * 100, 1)

    veredicto = "Alcista" if obv_now > sma_now else "Bajista"
    return {"valor": valor, "veredicto": veredicto}


def analyze_bollinger(df: pd.DataFrame) -> dict:
    """
    Bollinger Bands (SMA20, 2 std-dev) position.

    Alcista  if price < lower band (extreme oversold).
    Bajista  if price > upper band (extreme overbought).
    Neutral  otherwise.

    valor = BB %B position (0 = lower band, 100 = upper band).
    Returns {"valor": float, "veredicto": str}.
    """
    close               = df["Close"]
    upper, middle, lower = calculate_bollinger_bands(close)

    price = float(close.iloc[-1])
    u     = float(upper.iloc[-1])
    l     = float(lower.iloc[-1])
    width = u - l

    bb_pct = round((price - l) / width * 100, 1) if width > 0 else 50.0

    if price < l:
        veredicto = "Alcista"
    elif price > u:
        veredicto = "Bajista"
    else:
        veredicto = "Neutral"

    return {"valor": bb_pct, "veredicto": veredicto}


def analyze_macro(df: pd.DataFrame) -> dict:
    """
    SMA50 vs SMA200 trend (Golden / Death Cross).

    Alcista if SMA50 > SMA200 (Golden Cross).
    Bajista if SMA50 < SMA200 (Death Cross).

    valor = spread (SMA50 - SMA200) as % of current price.
    Returns {"valor": float, "veredicto": str}.
    """
    close  = df["Close"]
    price  = float(close.iloc[-1])
    sma50  = float(calculate_sma(close, min(50,  len(close))).iloc[-1])
    sma200 = float(calculate_sma(close, min(200, len(close))).iloc[-1])

    spread    = round((sma50 - sma200) / max(price, 0.01) * 100, 2)
    veredicto = "Alcista" if sma50 > sma200 else "Bajista"
    return {"valor": spread, "veredicto": veredicto}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _neutral_verdict(reason: str) -> dict:
    return {
        "score": 0, "signal": "NEUTRAL",
        "rsi": 50.0,   "rsi_label":   reason,
        "macd_label":  reason, "bb_label": reason,
        "trend_label": reason, "sma50": 0.0, "sma200": 0.0,
        "stoch_rsi":   50.0, "stoch_label": reason,
        "adx":         25.0, "adx_label": reason,
        "vol_ratio":   1.0,  "vol_label": reason,
    }
