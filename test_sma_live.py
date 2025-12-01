import yfinance as yf
from strategies.strategy_loader import run_strategy
from utils.trade_executor import handle_signal

SYMBOL = "AAPL"
STRATEGY = "sma"

def get_data(symbol):
    df = yf.download(symbol, period="100d", interval="1h", auto_adjust=True)
    df.columns = df.columns.get_level_values(0).str.lower()
    return df.dropna()

def main():
    print("Descargando datos…")
    df = get_data(SYMBOL)
 
    print("Ejecutando estrategia SMA…")
    signal = run_strategy(df, STRATEGY)

    print(f"➡ Señal generada: {signal}")  # 1 BUY / -1 SELL / 0 HOLD

    if signal == 1:
        print("🔵 BUY enviado al broker…")
        handle_signal("buy", SYMBOL)

    elif signal == -1:
        print("🔴 SELL enviado al broker…")
        handle_signal("sell", SYMBOL)

    else:
        print("➖ HOLD, no se envía nada.")

if __name__ == "__main__":
    main()


