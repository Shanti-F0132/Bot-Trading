# utils/data_streamer.py
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

def stream_data(symbol="AAPL", interval="1m", refresh_rate=60, lookback=200, live=False):
    """
    Descarga datos recientes de un símbolo y opcionalmente actualiza en 'tiempo real'.

    Parámetros:
        symbol (str): símbolo del activo (ej. "AAPL", "TSLA", "BTC-USD")
        interval (str): intervalo de tiempo (ej. "1m", "5m", "15m", "1h", "1d")
        refresh_rate (int): tiempo en segundos entre actualizaciones (solo si live=True)
        lookback (int): cantidad de datos históricos a mantener
        live (bool): si True, se actualiza continuamente (modo streaming)

    Retorna:
        pd.DataFrame: con columnas ['Open', 'High', 'Low', 'Close', 'Volume']
    """

    print(f"📡 Iniciando stream de datos para {symbol} (intervalo={interval})...")

    # Primera descarga
    data = yf.download(
        tickers=symbol,
        period="1d" if "m" in interval else "6mo",
        interval=interval,
        progress=False,
        auto_adjust=True,
    )

    data = data.tail(lookback)
    print(f"✅ Datos iniciales descargados: {len(data)} registros")

    if not live:
        return data

    try:
        while True:
            new_data = yf.download(
                tickers=symbol,
                period="1d" if "m" in interval else "6mo",
                interval=interval,
                progress=False
            ).tail(lookback)

            # Si hay nuevos datos, los actualizamos
            if not new_data.equals(data):
                data = new_data
                last = data.iloc[-1]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Último precio {symbol}: {last['Close']:.2f}")

            time.sleep(refresh_rate)

    except KeyboardInterrupt:
        print("\n🛑 Stream detenido manualmente.")
        return data
