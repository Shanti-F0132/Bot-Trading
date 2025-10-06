import matplotlib.pyplot as plt
from utils.data_loader import load_data
from strategies.sma_strategy import sma_strategy
from backtesting.simple_backtester import backtest

# ==============================
# Cargar datos primero
# ==============================
df = load_data("AAPL", start="2020-01-01", end="2025-01-01")

# ==============================
# Función para evaluar en distintos timeframes
# ==============================
def evaluate_timeframes(df, strategy_func, **kwargs):
    results = {}
    timeframes = {"Diario": "D", "Semanal": "W", "Mensual": "M"}

    for name, tf in timeframes.items():
        df_tf = df.resample(tf).agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()

        df_strategy = strategy_func(df_tf.copy(), **kwargs)
        results_tf = backtest(df_strategy)

        results[name] = results_tf

    return results


# ==============================
# Bloque de ejecución
# ==============================
print("📊 Comparación de SMA 10-50 en distintos timeframes...")

results_tf = evaluate_timeframes(df, sma_strategy, short=10, long=50)

# Graficar
plt.figure(figsize=(10, 6))
for name, res in results_tf.items():
    plt.plot(res["equity_curve"], label=name)

plt.title("Comparación de SMA 10-50 en distintos timeframes (AAPL)")
plt.legend()
plt.show()

# Mostrar métricas
for name, res in results_tf.items():
    print(f"\n{name}:")
    print(f"  Final Equity: {res['final_equity']:.2f}")
    print(f"  CAGR: {res['cagr']*100:.2f}%")
    print(f"  Sharpe Ratio: {res['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {res['max_drawdown']*100:.2f}%")
