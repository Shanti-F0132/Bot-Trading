"""
data_loader.py  –  v3.0
========================
Descarga datos OHLCV con tres fuentes en cascada:

    1. Alpaca Historical Data API  (prioridad 1 — mismo broker, sin bloqueos)
    2. yfinance                    (prioridad 2 — fallback con reintentos)
    3. Stooq via pandas_datareader (prioridad 3 — último recurso)

Requisitos
----------
    pip install alpaca-py yfinance pandas_datareader requests-cache --upgrade

Variables de entorno necesarias para Alpaca:
    ALPACA_API_KEY
    ALPACA_SECRET_KEY

Si las variables no están definidas, Alpaca se omite y se pasa directo a yfinance.

Columnas de salida
------------------
Siempre devuelve: open, high, low, close, volume
con índice DatetimeIndex (tz-naive, UTC normalizado).
"""

import os
import time
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================
# Helpers compartidos
# ============================================================

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplana MultiIndex si existe, pone columnas en minúsculas,
    filtra solo OHLCV y elimina NaNs.
    """
    # Aplanar MultiIndex de columnas (yfinance ≥ 0.2)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    # Normalizar nombre de índice
    df.index.name = "date"

    # Quitar timezone para consistencia entre fuentes
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas {missing}. Disponibles: {list(df.columns)}")

    return df[required].dropna()


# ============================================================
# FUENTE 1 — Alpaca Historical Data API
# ============================================================

def _download_alpaca(
    symbol: str,
    start: str,
    end: str,
    timeframe: str = "1Day",
) -> pd.DataFrame:
    """
    Descarga barras históricas desde Alpaca usando alpaca-py.

    timeframe opciones comunes: '1Min', '5Min', '15Min', '1Hour', '1Day'
    """
    api_key    = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise EnvironmentError(
            "ALPACA_API_KEY y/o ALPACA_SECRET_KEY no están definidas. "
            "Saltando Alpaca como fuente."
        )

    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    except ImportError:
        raise ImportError(
            "alpaca-py no está instalado. Ejecuta: pip install alpaca-py"
        )

    # Mapear string a objeto TimeFrame
    _tf_map = {
        "1Min":   TimeFrame(1,  TimeFrameUnit.Minute),
        "5Min":   TimeFrame(5,  TimeFrameUnit.Minute),
        "15Min":  TimeFrame(15, TimeFrameUnit.Minute),
        "30Min":  TimeFrame(30, TimeFrameUnit.Minute),
        "1Hour":  TimeFrame(1,  TimeFrameUnit.Hour),
        "1Day":   TimeFrame.Day,
        "1Week":  TimeFrame.Week,
        "1Month": TimeFrame.Month,
    }
    tf = _tf_map.get(timeframe)
    if tf is None:
        raise ValueError(
            f"timeframe '{timeframe}' no reconocido. "
            f"Opciones: {list(_tf_map.keys())}"
        )

    client = StockHistoricalDataClient(
        api_key=api_key,
        secret_key=secret_key,
    )

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=tf,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        adjustment="all",   # ajuste por splits y dividendos
    )

    bars = client.get_stock_bars(request).df

    if bars.empty:
        raise ValueError(f"Alpaca devolvió DataFrame vacío para {symbol}")

    # Alpaca devuelve MultiIndex (symbol, timestamp) → quedarse solo con timestamp
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level="symbol")

    # Alpaca incluye columnas extra como 'vwap', 'trade_count' → _normalize filtra
    return _normalize(bars)


# ============================================================
# FUENTE 2 — yfinance
# ============================================================

def _download_yfinance(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Descarga con yfinance y normaliza columnas."""
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("yfinance no está instalado. Ejecuta: pip install yfinance")

    df = yf.download(
        symbol,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        actions=False,
    )

    if df.empty:
        raise ValueError(f"yfinance devolvió DataFrame vacío para {symbol}")

    return _normalize(df)


# ============================================================
# FUENTE 3 — Stooq (via pandas_datareader)
# ============================================================

def _download_stooq(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fuente de último recurso: Stooq via pandas_datareader."""
    try:
        from pandas_datareader import data as pdr
    except ImportError:
        raise ImportError(
            "pandas_datareader no está instalado. "
            "Ejecuta: pip install pandas_datareader"
        )

    # Stooq usa sufijo .US para acciones americanas
    stooq_symbol = symbol if "." in symbol else f"{symbol}.US"

    df = pdr.DataReader(stooq_symbol, "stooq", start=start, end=end)

    if df.empty:
        raise ValueError(f"Stooq devolvió DataFrame vacío para {stooq_symbol}")

    df = df.sort_index()   # Stooq devuelve orden descendente
    return _normalize(df)


# ============================================================
# API PÚBLICA
# ============================================================

def get_data(
    symbol: str,
    start: str = "2015-01-01",
    end: str = "2026-01-01",
    timeframe: str = "1Day",
    max_retries: int = 3,
    retry_delay: float = 5.0,
    source: str = "auto",
) -> pd.DataFrame:
    """
    Descarga datos OHLCV para *symbol* entre *start* y *end*.

    Parámetros
    ----------
    symbol       : Ticker (ej: 'AAPL', 'MSFT', 'BTC-USD')
    start        : Fecha inicio  'YYYY-MM-DD'
    end          : Fecha fin     'YYYY-MM-DD'
    timeframe    : Granularidad de las barras. Relevante solo para Alpaca.
                   Opciones: '1Min','5Min','15Min','30Min','1Hour','1Day','1Week'
    max_retries  : Intentos para yfinance antes de pasar a Stooq
    retry_delay  : Segundos base entre reintentos (back-off exponencial)
    source       : 'auto' | 'alpaca' | 'yfinance' | 'stooq'
                   'auto' prueba en cascada: Alpaca → yfinance → Stooq

    Retorna
    -------
    DataFrame con columnas: open, high, low, close, volume
    Índice: DatetimeIndex tz-naive
    """

    # --- Fuente forzada manualmente ---
    if source == "alpaca":
        return _download_alpaca(symbol, start, end, timeframe)
    if source == "yfinance":
        return _download_yfinance(symbol, start, end)
    if source == "stooq":
        return _download_stooq(symbol, start, end)

    # --- Cascada automática ---

    # 1. Alpaca
    try:
        logger.info(f"[{symbol}] Intentando Alpaca...")
        df = _download_alpaca(symbol, start, end, timeframe)
        logger.info(f"[{symbol}] ✅ Alpaca OK — {len(df)} filas")
        return df
    except EnvironmentError as e:
        # Credenciales no configuradas → saltar silenciosamente
        logger.info(f"[{symbol}] Alpaca no disponible: {e}")
    except Exception as e:
        logger.warning(f"[{symbol}] Alpaca falló: {e}")

    # 2. yfinance con reintentos y back-off exponencial
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[{symbol}] yfinance intento {attempt}/{max_retries}...")
            df = _download_yfinance(symbol, start, end)
            logger.info(f"[{symbol}] ✅ yfinance OK — {len(df)} filas")
            return df
        except Exception as e:
            last_exc = e
            logger.warning(f"[{symbol}] yfinance falló (intento {attempt}): {e}")
            if attempt < max_retries:
                wait = retry_delay * (2 ** (attempt - 1))
                logger.info(f"[{symbol}] Esperando {wait:.1f}s...")
                time.sleep(wait)

    # 3. Stooq
    logger.warning(
        f"[{symbol}] yfinance falló {max_retries} veces. "
        "Intentando Stooq como último recurso..."
    )
    try:
        df = _download_stooq(symbol, start, end)
        logger.info(f"[{symbol}] ✅ Stooq OK — {len(df)} filas")
        return df
    except Exception as stooq_exc:
        raise RuntimeError(
            f"❌ No se pudo descargar datos para '{symbol}'.\n"
            f"  Alpaca  : credenciales no configuradas o fallo de API\n"
            f"  yfinance: {last_exc}\n"
            f"  Stooq   : {stooq_exc}\n\n"
            "Posibles causas:\n"
            "  - IP bloqueada por Yahoo Finance (usa VPN o espera unas horas)\n"
            "  - Símbolo incorrecto\n"
            "  - Sin conexión a internet\n"
            "  - Variables ALPACA_API_KEY / ALPACA_SECRET_KEY no definidas"
        ) from stooq_exc


# ============================================================
# UTILIDAD EXTRA — Carga desde CSV local (desarrollo offline)
# ============================================================

def get_data_from_csv(filepath: str) -> pd.DataFrame:
    """
    Carga datos OHLCV desde un CSV local.

    El CSV debe tener una columna de fecha (cualquier nombre) como primera
    columna o como índice, y columnas OHLCV (mayúsculas o minúsculas).

    Útil para desarrollo sin internet o para evitar rate-limits.
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return _normalize(df)