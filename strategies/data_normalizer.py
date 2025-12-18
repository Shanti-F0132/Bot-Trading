import pandas as pd

def normalize_columns(df):
    df = df.copy()

    # Aplastar MultiIndex si existe
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Minúsculas
    df.columns = df.columns.str.lower()

    # Renombrado EXACTO (no por substring)
    rename_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }

    df = df.rename(columns={c: rename_map[c] for c in df.columns if c in rename_map})

    # Validación dura
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns after normalization: {missing}")

    return df

