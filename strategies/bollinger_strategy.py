"""
bollinger_strategy.py  –  v2.0
"""

import pandas as pd


def bollinger_strategy(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    price_col: str = "close",
) -> pd.DataFrame:
    if price_col not in df.columns:
        alt = price_col.capitalize()
        if alt in df.columns:
            df = df.rename(columns={alt: price_col})
        else:
            raise KeyError(f"Columna '{price_col}' no encontrada. Disponibles: {list(df.columns)}")

    df = df.copy()
    df["bb_mid"]   = df[price_col].rolling(window=window).mean()
    df["bb_std"]   = df[price_col].rolling(window=window).std()
    df["bb_upper"] = df["bb_mid"] + num_std * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - num_std * df["bb_std"]

    df["signal"] = 0
    df.loc[df[price_col] < df["bb_lower"], "signal"] = 1    # precio bajo banda → comprar
    df.loc[df[price_col] > df["bb_upper"], "signal"] = -1   # precio sobre banda → vender

    df.dropna(subset=["bb_mid", "bb_upper", "bb_lower"], inplace=True)
    return df