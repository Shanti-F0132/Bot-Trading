import pandas as pd

def sma_crossover(df, short=20, long=50):
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

    # Calcular medias móviles
    df['SMA_short'] = df['Close'].rolling(window=short).mean()
    df['SMA_long'] = df['Close'].rolling(window=long).mean()

    # Señal: 1 si SMA corta > SMA larga, 0 si no
    df['signal'] = (df['SMA_short'] > df['SMA_long']).astype(int)

    # Cambio de posición: 1 cuando pasamos de 0 -> 1 (compra), -1 de 1 -> 0 (venta)
    df['position_change'] = df['signal'].diff().fillna(0).astype(int)

    return df
