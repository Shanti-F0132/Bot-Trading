"""
rsi_strategy.py  –  v2.0
"""

import pandas as pd
import numpy as np


def rsi_strategy(
    df: pd.DataFrame,
    rsi_period: int = 14,
    lower: float = 30,
    upper: float = 70,
    price_col: str = "close",
) -> pd.DataFrame:
    if price_col not in df.columns:
        alt = price_col.capitalize()
        if alt in df.columns:
            df = df.rename(columns={alt: price_col})
        else:
            raise KeyError(f"Columna '{price_col}' no encontrada. Disponibles: {list(df.columns)}")

    df = df.copy()
    delta = df[price_col].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    df["signal"] = 0
    df.loc[df["rsi"] < lower, "signal"] = 1    # sobreventa → comprar
    df.loc[df["rsi"] > upper, "signal"] = -1   # sobrecompra → vender

    df.dropna(subset=["rsi"], inplace=True)
    return df