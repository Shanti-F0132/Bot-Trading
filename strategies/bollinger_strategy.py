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

    # Calcular SMA y bandas
    df["SMA"] = df["Close"].rolling(window=window).mean()
    df["STD"] = df["Close"].rolling(window=window).std()
    df["Upper"] = df["SMA"] + num_std * df["STD"]
    df["Lower"] = df["SMA"] - num_std * df["STD"]

    # Señales de compra/venta
    df["signal"] = 0
    df.loc[df["Close"] < df["Lower"], "signal"] = 1   # Comprar
    df.loc[df["Close"] > df["Upper"], "signal"] = -1  # Vender

    # Detectar cambios de posición
    df["position_change"] = df["signal"].diff().fillna(0)

    return df
