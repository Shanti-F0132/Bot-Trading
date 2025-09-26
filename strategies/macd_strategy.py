import pandas as pd

def macd_strategy(df, fast=12, slow=26, signal=9):
    """
    Estrategia MACD: compra cuando MACD cruza hacia arriba la señal,
    vende cuando cruza hacia abajo.
    """

    # Calcular EMAs
    df["EMA_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()

    # MACD y línea de señal
    df["MACD"] = df["EMA_fast"] - df["EMA_slow"]
    df["Signal_Line"] = df["MACD"].ewm(span=signal, adjust=False).mean()

    # Inicializar señales
    df["signal"] = 0

    # Señales solo cuando hay cruce
    df.loc[(df["MACD"] > df["Signal_Line"]) & (df["MACD"].shift(1) <= df["Signal_Line"].shift(1)), "signal"] = 1  # Compra
    df.loc[(df["MACD"] < df["Signal_Line"]) & (df["MACD"].shift(1) >= df["Signal_Line"].shift(1)), "signal"] = -1  # Venta

    # Detectar cambios de posición
    df["position_change"] = df["signal"]

    return df
