import time
import yfinance as yf
from strategies.strategy_loader import run_strategy
from utils.trade_executor import handle_signal

SYMBOL = "AAPL"
STRATEGY = "sma"        # Cambia aquí: "rsi", "macd", "bollinger"
INTERVAL_SECONDS = 60   # Frecuencia de actualización

def get_data(symbol, days=200):
    df = yf.download(symbol, period=f"{days}d")
    df = df.dropna()
    return df

def main():
    print(f"➡ Iniciando bot en PAPER TRADING con estrategia: {STRATEGY}")
    while True:
        df = get_data(SYMBOL)
        signal = run_strategy(df, STRATEGY)

        if signal == 1:
            print("📈 BUY signal")
            handle_signal("buy", SYMBOL)

        elif signal == -1:
            print("📉 SELL signal")
            handle_signal("sell", SYMBOL)

        else:
            print("➖ HOLD")

        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
