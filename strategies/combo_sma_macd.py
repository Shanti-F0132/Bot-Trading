import pandas as pd
from strategies.sma_strategy import sma_strategy
from strategies.macd_strategy import macd_strategy

def combo_sma_macd(df, sma_short=20, sma_long=50, macd_fast=12, macd_slow=26, macd_signal=9):
    """
    Estrategia combinada SMA + MACD.
    Solo genera señal cuando ambas coinciden.
    """

    df = df.copy()

    # Ejecutar sub-estrategias por separado
    df_sma  = sma_strategy(df, short=sma_short, long=sma_long)
    df_macd = macd_strategy(df, fast=macd_fast, slow=macd_slow, signal=macd_signal)

    # Unir resultados
    df["sma_signal"] = df_sma["signal"]
    df["sma_change"] = df_sma["position_change"]

    df["macd_signal"] = df_macd["signal"]
    df["macd_change"] = df_macd["position_change"]

    # Señal final
    df["signal"] = 0

    # BUY
    df.loc[
        (df_sma["sma_short"] > df_sma["sma_long"]) &
        (df_macd["macd"].shift(1) < df_macd["macd_signal"].shift(1)) &
        (df_macd["macd"] >= df_macd["macd_signal"]),
        "signal"
    ] = 1

    # SELL
    df.loc[
        (df_sma["sma_short"] < df_sma["sma_long"]) &
        (df_macd["macd"].shift(1) > df_macd["macd_signal"].shift(1)) &
        (df_macd["macd"] <= df_macd["macd_signal"]),
        "signal"
    ] = -1

    # Cambio final para el bot
    df["position_change"] = df["signal"].diff().fillna(0).astype(int)

    return df
