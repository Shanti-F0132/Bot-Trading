import yfinance as yf
import pandas as pd

def get_data(symbol, start="2020-01-01", end=None):
    """
    Descarga datos de Yahoo Finance para un solo símbolo y
    aplana columnas si hay MultiIndex (por ejemplo, cuando Yahoo
    devuelve datos con el ticker en el nombre de la columna).
    """
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)

    # 👇 Paso importante: aplanar columnas si hay MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]

    # Renombrar todas las columnas OHLCV si vienen con sufijo (ej: Open_AAPL → Open)
    rename_map = {}
    for col in df.columns:
        if col.startswith("Open"):
            rename_map[col] = "Open"
        elif col.startswith("High"):
            rename_map[col] = "High"
        elif col.startswith("Low"):
            rename_map[col] = "Low"
        elif col.startswith("Close"):
            rename_map[col] = "Close"
        elif col.startswith("Adj Close"):
            rename_map[col] = "Adj Close"
        elif col.startswith("Volume"):
            rename_map[col] = "Volume"

    df.rename(columns=rename_map, inplace=True)

    return df
