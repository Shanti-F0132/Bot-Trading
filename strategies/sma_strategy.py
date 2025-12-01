import pandas as pd

def sma_strategy(df, short=9, long=21):
    """
    Calcula señales de cruce de medias móviles y genera 'position_change'.

    Parámetros:
    -----------
    df : pandas.DataFrame
        Debe contener la columna 'Close'.
    short : int
        Ventana para la SMA corta.
    long : int
        Ventana para la SMA larga.

    Retorna:
    --------
    df : pandas.DataFrame
        DataFrame original con columnas adicionales:
        - 'SMA_short'
        - 'SMA_long'
        - 'signal' (1 = tener posición, 0 = estar fuera)
        - 'position_change' (1 = señal de compra, -1 = señal de venta)
    """
    df = df.copy()

    # Cálculo de SMA
    df['sma_short'] = df['close'].rolling(window=short).mean()
    df['sma_long'] = df['close'].rolling(window=long).mean()

    # Señales
    df['signal'] = (df['sma_short'] > df['sma_long']).astype(int)
    df['position_change'] = df['signal'].diff().fillna(0).astype(int)

    return df
