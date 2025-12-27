import pandas as pd

def bollinger_strategy(df, window=20, num_std=2):
    """
    Estrategia basada en Bollinger Bands.
    Señales:
      - Compra cuando el precio cierra por debajo de la banda inferior.
      - Venta cuando el precio cierra por encima de la banda superior.

    Parámetros:
    -----------
    df : DataFrame con columna 'Close'
    window : int, periodo de la SMA
    num_std : float, número de desviaciones estándar
    """

    df = df.copy()

    df["sma"] = df["close"].rolling(window).mean()
    df["std"] = df["close"].rolling(window).std()

    df["upper_band"] = df["sma"] + num_std * df["std"]
    df["lower_band"] = df["sma"] - num_std * df["std"]

    df["signal"] = 0
    df.loc[
        (df["close"] < df["lower_band"]) &
        (df["sma_long"] > df["sma_long"].shift(1)),
        "signal"
    ] = 1
    df.loc[
        (df["close"] > df["upper_band"]) &
        (df["sma_long"] < df["sma_long"].shift(1)),
        "signal"
    ] = -1

    df["position_change"] = df["signal"].diff().fillna(0).astype(int)

    return df
