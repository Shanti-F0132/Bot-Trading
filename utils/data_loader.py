import yfinance as yf
import pandas as pd

def get_data(symbol, start, end):
    """
    Descarga datos históricos de un activo y limpia las columnas
    para evitar MultiIndex y mantener consistencia.
    """
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)

    # Si hay MultiIndex en las columnas, aplánalo
    if isinstance(df.columns, pd.MultiIndex):
        # Extrae solo el primer nivel (Close, Open, etc.)
        df.columns = [col[0].capitalize() for col in df.columns]
    else:
        # Asegura que las columnas estén normalizadas
        df.columns = [c.capitalize() for c in df.columns]

    # Quita espacios o valores extraños en nombres de columnas
    df.columns = [c.strip() for c in df.columns]

    # Asegurar que no existan columnas duplicadas
    df = df.loc[:, ~df.columns.duplicated()]

    # Elimina valores NaN iniciales (comunes al descargar con yf)
    df.dropna(inplace=True)

    return df
