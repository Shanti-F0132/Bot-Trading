from utils.data_loader import get_data
from strategies.sma_strategy import sma_crossover
from strategies.sma_optimizer import optimize_sma
from backtesting.simple_backtester import backtest
from utils.heatmap_plotter import plot_heatmap

import matplotlib.pyplot as plt

# === 1️⃣ Descarga de datos ===
print("📥 Descargando datos de AAPL...")
df = get_data("AAPL", start="2020-01-01", end="2025-01-01")

# === 2️⃣ Calcula señales con SMA inicial ===
print("📊 Calculando señales de SMA...")
df = sma_crossover(df, short=20, long=50)

# === 3️⃣ Ejecuta backtest ===
print("⚙️ Ejecutando backtest...")
results = backtest(df)

# === 4️⃣ Muestra resultados ===
print("\n📈 Resultados del Backtest")
print(f"Capital final: ${results['final_equity']:.2f}")
print(f"Retorno total: {results['total_return_pct']:.2f}%")
print(f"CAGR: {results['cagr']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")

# === 5️⃣ Grafica curva de capital ===
results["equity_curve"].plot(title="Curva de Capital - Estrategia SMA (20/50)", figsize=(10, 5))
plt.ylabel("Equidad ($)")
plt.xlabel("Fecha")
plt.show()

# === 6️⃣ Optimización de parámetros ===
print("\n🔎 Ejecutando optimización de SMA...")
results_df = optimize_sma(df, short_range=(5, 30), long_range=(40, 100))

print("\n📊 Top 5 combinaciones por Sharpe Ratio:")
print(results_df[['short', 'long', 'sharpe_ratio', 'cagr', 'max_drawdown']].head())
print("\n✅ Optimización completada.")

# === 7️⃣ Graficar Heatmaps ===
print("\n🖼 Generando mapa de calor para Sharpe Ratio...")
plot_heatmap(results_df, metric="sharpe_ratio")

print("\n🖼 Generando mapa de calor para CAGR...")
plot_heatmap(results_df, metric="cagr")