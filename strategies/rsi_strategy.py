import pandas as pd

def rsi_strategy(df, window=14):
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

    df = df.copy()

    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # Señales RSI
    df["signal"] = 0
    df.loc[df["rsi"] < 30, "signal"] = 1   # Sobrevendido → compra
    df.loc[df["rsi"] > 70, "signal"] = -1  # Sobrecomprado → venta

    df["position_change"] = df["signal"].diff().fillna(0).astype(int)

    return df
