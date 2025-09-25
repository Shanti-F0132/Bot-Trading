import matplotlib.pyplot as plt
from utils.data_loader import get_data
from strategies.sma_strategy import sma_crossover
from backtesting.simple_backtester import backtest
from strategies.sma_optimizer import optimize_sma
from utils.heatmap_plotter import plot_heatmap

# ==========================
#   PARÁMETROS GENERALES
# ==========================
symbol = "AAPL"
start_date = "2015-01-01"
end_date = "2025-01-01"

# ==========================
#   PIPELINE DEL PROGRAMA
# ==========================

print(f"📥 Descargando datos de {symbol}...")
df = get_data(symbol, start=start_date, end=end_date)

print("📊 Calculando señales de SMA...")
df = sma_crossover(df, short=20, long=50)

# === Backtest sin costos ===
print("\n⚙️ Backtest SIN comisiones/slippage...")
results_clean = backtest(df, commission=0.0, slippage=0.0, position_size=1.0)

# === Backtest con costos ===
print("\n⚙️ Backtest CON comisiones/slippage...")
results_real = backtest(df, commission=0.001, slippage=0.0005, position_size=1.0)

# === Backtest con position sizing (50%) ===
print("\n⚙️ Backtest CON 50% del capital...")
results_half = backtest(df, commission=0.001, slippage=0.0005, position_size=0.5)

# ==========================
#   RESULTADOS
# ==========================

print("\n📈 Resultados SIN costos:")
print(f"Capital final: ${results_clean['final_equity']:.2f}")
print(f"Retorno total: {results_clean['total_return_pct']:.2f}%")
print(f"CAGR: {results_clean['cagr']:.2%}")
print(f"Sharpe Ratio: {results_clean['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results_clean['max_drawdown']:.2%}")

print("\n📉 Resultados CON costos (100% del capital):")
print(f"Capital final: ${results_real['final_equity']:.2f}")
print(f"Retorno total: {results_real['total_return_pct']:.2f}%")
print(f"CAGR: {results_real['cagr']:.2%}")
print(f"Sharpe Ratio: {results_real['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results_real['max_drawdown']:.2%}")

print("\n📉 Resultados CON costos (50% del capital):")
print(f"Capital final: ${results_half['final_equity']:.2f}")
print(f"Retorno total: {results_half['total_return_pct']:.2f}%")
print(f"CAGR: {results_half['cagr']:.2%}")
print(f"Sharpe Ratio: {results_half['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results_half['max_drawdown']:.2%}")

# ==========================
#   GRÁFICAS
# ==========================

# Comparación SIN vs CON costos
plt.figure(figsize=(10,5))
results_clean["equity_curve"].plot(label="SIN costos")
results_real["equity_curve"].plot(label="CON costos", linestyle="--")
plt.title("Curva de Capital - Impacto de Costos")
plt.ylabel("Equidad ($)")
plt.xlabel("Fecha")
plt.legend()
plt.show()

# Comparación 100% vs 50% capital
plt.figure(figsize=(10,5))
results_real["equity_curve"].plot(label="100% del capital")
results_half["equity_curve"].plot(label="50% del capital", linestyle="--")
plt.title("Curva de Capital - Impacto de Position Sizing")
plt.ylabel("Equidad ($)")
plt.xlabel("Fecha")
plt.legend()
plt.show()

# ==========================
#   OPTIMIZACIÓN
# ==========================

print("\n🔎 Ejecutando optimización de SMA...")
results_df = optimize_sma(df, short_range=(5, 30), long_range=(40, 100))

print("\n📊 Top 5 combinaciones por Sharpe Ratio:")
print(results_df[['short', 'long', 'sharpe_ratio', 'cagr', 'max_drawdown']].head())

# Heatmaps
print("\n🖼 Generando heatmaps...")
plot_heatmap(results_df, metric="sharpe_ratio")
plot_heatmap(results_df, metric="cagr")
