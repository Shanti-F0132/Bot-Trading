import pandas as pd

def rsi_strategy(df, rsi_period=14, lower=30, upper=70):
    """
    Estrategia basada en RSI (Relative Strength Index).
    Genera señales de compra/venta cuando RSI cruza niveles de sobrecompra/sobreventa.

    Parámetros:
    -----------
    df : DataFrame con columna 'Close'
    period : int, número de días para calcular RSI
    overbought : int, nivel de sobrecompra
    oversold : int, nivel de sobreventa
    """

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Generar señales
    df["signal"] = 0
    df.loc[df["RSI"] < lower, "signal"] = 1   # Comprar
    df.loc[df["RSI"] > upper, "signal"] = -1  # Vender

    # Detectar cambios de posición
    df["position_change"] = df["signal"].diff().fillna(0)

    return df
