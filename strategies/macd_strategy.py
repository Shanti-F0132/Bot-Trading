"""
macd_strategy.py  –  v2.0
"""

import pandas as pd


def macd_strategy(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    price_col: str = "close",
) -> pd.DataFrame:
    if price_col not in df.columns:
        alt = price_col.capitalize()
        if alt in df.columns:
            df = df.rename(columns={alt: price_col})
        else:
            raise KeyError(f"Columna '{price_col}' no encontrada. Disponibles: {list(df.columns)}")

    df = df.copy()
    ema_fast = df[price_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[price_col].ewm(span=slow, adjust=False).mean()
    df["macd"]        = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]

    df["signal_col"] = 0
    df.loc[df["macd"] > df["macd_signal"], "signal_col"] = 1
    df.loc[df["macd"] < df["macd_signal"], "signal_col"] = -1

    # Renombrar para que backtest use "signal"
    df = df.rename(columns={"signal_col": "signal"})
    df.dropna(subset=["macd", "macd_signal"], inplace=True)
    return df