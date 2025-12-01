import pandas as pd

def macd_strategy(df, fast=12, slow=26, signal=9):
    """
    Estrategia MACD: compra cuando MACD cruza hacia arriba la señal,
    vende cuando cruza hacia abajo.
    """
    df = df.copy()

    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()

    df["macd"] = df["ema_fast"] - df["ema_slow"]
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    df["signal"] = 0
    df.loc[df["macd"] > df["macd_signal"], "signal"] = 1
    df.loc[df["macd"] < df["macd_signal"], "signal"] = -1

    df["position_change"] = df["signal"].diff().fillna(0).astype(int)

    return df
