"""
sma_strategy.py  –  v2.0
==========================
Estrategia SMA Crossover compatible con el nuevo data_loader.

Cambios
-------
- Trabaja con columnas en minúsculas ('close') en lugar de 'Close'.
- Acepta un DataFrame con cualquier nombre de columna siempre que tenga 'close'.
- Señales: 1 = largo, -1 = corto, 0 = sin posición.
"""

import pandas as pd


def sma_strategy(
    df: pd.DataFrame,
    short: int = 10,
    long: int = 50,
    price_col: str = "close",
) -> pd.DataFrame:
    """
    Genera señales de cruce de medias móviles simples (SMA Crossover).

    Parámetros
    ----------
    df        : DataFrame con al menos la columna *price_col*
    short     : Período de la SMA corta
    long      : Período de la SMA larga
    price_col : Nombre de la columna de precio de cierre (default 'close')

    Retorna
    -------
    df con columnas adicionales:
        sma_short, sma_long, signal
    """
    if price_col not in df.columns:
        # Intento con capitalización alternativa por si acaso
        alt = price_col.capitalize()
        if alt in df.columns:
            df = df.rename(columns={alt: price_col})
        else:
            raise KeyError(
                f"Columna '{price_col}' no encontrada. "
                f"Columnas disponibles: {list(df.columns)}"
            )

    df = df.copy()
    df["sma_short"] = df[price_col].rolling(window=short).mean()
    df["sma_long"]  = df[price_col].rolling(window=long).mean()

    # Señal: 1 cuando SMA corta > SMA larga, -1 cuando SMA corta < SMA larga
    df["signal"] = 0
    df.loc[df["sma_short"] > df["sma_long"], "signal"] = 1
    df.loc[df["sma_short"] < df["sma_long"], "signal"] = -1

    # Eliminar filas donde las medias no están calculadas aún
    df.dropna(subset=["sma_short", "sma_long"], inplace=True)

    return df