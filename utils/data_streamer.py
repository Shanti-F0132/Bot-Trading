import yfinance as yf
import time
import threading
import pandas as pd
from datetime import datetime

class DataStreamer:
    """
    Clase que obtiene precios en tiempo real o modo simulado
    para alimentar el portafolio durante paper trading o pruebas en vivo.
    """

    def __init__(self, symbol: str, interval="1m", live=False, update_freq=60):
        """
        Parámetros:
        - symbol: símbolo del activo (ej: "AAPL")
        - interval: intervalo de datos (1m, 5m, 15m, 1h, 1d)
        - live: True para datos en tiempo real, False para simulación histórica
        - update_freq: frecuencia de actualización en segundos (solo en modo live)
        """
        self.symbol = symbol
        self.interval = interval
        self.live = live
        self.update_freq = update_freq
        self._running = False
        self.data = pd.DataFrame()
        self.callbacks = []

    def add_callback(self, func):
        """Permite registrar funciones que se ejecutarán cada vez que llegue un nuevo dato."""
        self.callbacks.append(func)

    def _notify_callbacks(self, new_row):
        for func in self.callbacks:
            func(new_row)

    def _simulate_data(self, historical_data):
        """Simula el flujo de datos usando históricos."""
        print(f"🎮 Iniciando simulación con {len(historical_data)} registros...")
        for _, row in historical_data.iterrows():
            if not self._running:
                break
            self.data = pd.concat([self.data, row.to_frame().T])
            self._notify_callbacks(row)
            time.sleep(1)  # Simula llegada de nuevos datos cada segundo

    def _fetch_live_data(self):
        """Obtiene datos nuevos desde Yahoo Finance en tiempo real."""
        print(f"🟢 Streaming en vivo iniciado para {self.symbol}...")
        while self._running:
            try:
                new_data = yf.download(self.symbol, period="1d", interval=self.interval, progress=False)
                if not new_data.empty:
                    last_row = new_data.iloc[-1]
                    self._notify_callbacks(last_row)
            except Exception as e:
                print(f"⚠️ Error en streaming: {e}")
            time.sleep(self.update_freq)

    def start(self, historical_data=None):
        """Inicia el streaming (modo histórico o en vivo)."""
        self._running = True
        if self.live:
            threading.Thread(target=self._fetch_live_data, daemon=True).start()
        elif historical_data is not None:
            threading.Thread(target=self._simulate_data, args=(historical_data,), daemon=True).start()
        else:
            raise ValueError("Debe pasar datos históricos si live=False.")

    def stop(self):
        """Detiene el streaming."""
        self._running = False
        print("⛔ Streaming detenido.")
