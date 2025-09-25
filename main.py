import matplotlib.pyplot as plt
from utils.data_loader import get_data
from strategies.sma_strategy import apply_sma_strategy
from backtesting.simple_backtester import backtest

# ==========================
#   PARÁMETROS GENERALES
# ==========================
symbol = "AAPL"
start_date = "2015-01-01"
end_date = "2025-01-01"

# ==========================
#   PIPELINE DEL PROGRAMA
# ==========================

print("📥 Descargando datos de", symbol, "...")
df = get_data(symbol, start_date, end_date)

print("📊 Calculando señales de SMA...")
df = apply_sma_strategy(df, short_window=20, long_window=50)

print("⚙️ Ejecutando backtest...")

# Backtest con TODO el capital
results_full = backtest(df, commission=0.001, slippage=0.0005, position_size=1.0)

# Backtest con la MITAD del capital
results_half = backtest(df, commission=0.001, slippage=0.0005, position_size=0.5)

# ==========================
#   RESULTADOS
# ==========================

print("\n📈 Resultados con 100% del capital:")
print(f"Capital final: ${results_full['final_equity']:.2f}")
print(f"Retorno total: {results_full['total_return_pct']:.2f}%")
print(f"CAGR: {results_full['cagr']:.2%}")
print(f"Sharpe Ratio: {results_full['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results_full['max_drawdown']:.2%}")

print("\n📉 Resultados con 50% del capital:")
print(f"Capital final: ${results_half['final_equity']:.2f}")
print(f"Retorno total: {results_half['total_return_pct']:.2f}%")
print(f"CAGR: {results_half['cagr']:.2%}")
print(f"Sharpe Ratio: {results_half['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results_half['max_drawdown']:.2%}")

# ==========================
#   GRÁFICA DE EQUITY CURVE
# ==========================
plt.figure(figsize=(10, 5))
results_full["equity_curve"].plot(label="100% del capital")
results_half["equity_curve"].plot(label="50% del capital", linestyle="--")
plt.title("Impacto de Position Sizing en la Curva de Capital")
plt.ylabel("Equidad ($)")
plt.xlabel("Fecha")
plt.legend()
plt.show()
