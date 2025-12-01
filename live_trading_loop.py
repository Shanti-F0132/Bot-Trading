import time
import yfinance as yf
import pandas as pd

from strategies.data_normalizer import normalize_columns
from strategies.strategy_loader import run_strategy
from broker_api.alpaca_client import client
from utils.trade_executor import handle_signal
from strategies.combo_sma_macd import combo_sma_macd

# ===============================
# CONFIGURACIÓN
# ===============================

SYMBOL = "AAPL"              # Ticker(AAPL, TSLA, MSFT... etc.)
STRATEGY = "combo_sma_macd"       # sma, rsi, macd, bollinger, combo_sma_macd
PERIOD = "5d"                # Datos recientes
INTERVAL = "5m"              # Velas de 5 minutos
SLEEP_SECONDS = 60           # Tiempo entre iteraciones

# Parámetros de estrategias
PARAMS = {
    "sma": {"short": 5, "long": 20},
    "rsi": {"window": 7},
    "macd": {"fast": 6, "slow": 13, "signal": 5},
    "bollinger": {"window": 10, "num_std": 2},
    "combo_sma_macd": {
        "sma_short": 5,
        "sma_long": 20,
        "macd_fast": 6,
        "macd_slow": 13,
        "macd_signal": 5
    }
}

# ===============================
# FUNCIONES
# ===============================

def get_latest_data(symbol):
    """Descarga datos con YF y normaliza columnas."""
    df = yf.download(symbol, period=PERIOD, interval=INTERVAL, auto_adjust=True)
    df = normalize_columns(df)
    return df


def print_last_values(df):
    """Imprime el último valor de indicadores."""
    last = df.iloc[-1]
    print("📊 Últimos valores:")
    print(last)
    print()


# ===============================
# LOOP PRINCIPAL
# ===============================

def main():
    print("Iniciando Live Trading Loop...")
    print(f"Estrategia: {STRATEGY.upper()} | Activo: {SYMBOL}")
    print("=============================================")

    strategy_params = PARAMS.get(STRATEGY, {})

    while True:
        print("\n==========================")
        print("Actualizando datos...")

        try:
            df = get_latest_data(SYMBOL)

            # Ejecutar estrategia
            print("Ejecutando estrategia...")
            df = run_strategy(df, STRATEGY, **strategy_params)

            # Mostrar últimos valores
            print_last_values(df)

            signal = df["position_change"].iloc[-1]
            
            # Procesar señal
            if signal == 1:
                signal = "buy"
            elif signal == -1:
                signal = "sell"
            else:
                signal = "hold"
            print(f"SEÑAL DETECTADA: {signal}")
            handle_signal(signal, SYMBOL)

        except Exception as e:
            print(f"ERROR: {e}")

        print(f"Esperando {SLEEP_SECONDS}s...")
        time.sleep(SLEEP_SECONDS)


# ===============================
# EJECUCIÓN
# ===============================

if __name__ == "__main__":
    main()
