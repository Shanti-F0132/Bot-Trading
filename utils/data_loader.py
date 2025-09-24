import yfinance as yf
import pandas as pd

def get_data(symbol, start="2020-01-01", end=None):
    """
    Descarga datos de Yahoo Finance para un solo símbolo y
    aplana columnas si hay MultiIndex (por ejemplo, cuando Yahoo
    devuelve datos con el ticker en el nombre de la columna).
    """
    df = yf.download(symbol, start=start, end=end, progress=False)

    # 👇 Paso importante: aplanar columnas si hay MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]

    # Renombrar columna Close si viene con sufijo del ticker (Close_AAPL)
    for col in df.columns:
        if col.startswith("Close"):
            df.rename(columns={col: "Close"}, inplace=True)

    return df
