import pandas as pd

def normalize_columns(df):
    df = df.copy()

    # Aplastar MultiIndex si existe
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]

    # Convertir columnas a minúsculas
    df.columns = df.columns.str.lower()

    # Renombrar columnas relevantes
    rename_map = {}

    for col in df.columns:
        if "close" in col:
            rename_map[col] = "close"
        if "open" in col:
            rename_map[col] = "open"
        if "high" in col:
            rename_map[col] = "high"
        if "low" in col:
            rename_map[col] = "low"
        if "volume" in col:
            rename_map[col] = "volume"

    df = df.rename(columns=rename_map)

    return df
