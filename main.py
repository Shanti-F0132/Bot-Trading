import matplotlib.pyplot as plt
from utils.data_loader import get_data
from strategies.sma_strategy import sma_crossover
from backtesting.simple_backtester import backtest
from strategies.sma_optimizer import optimize_sma
from strategies.sl_tp_optimizer import optimize_sl_tp
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

# === Backtest base ===
print("\n⚙️ Backtest SIN SL/TP...")
results_base = backtest(df, commission=0.001, slippage=0.0005, position_size=1.0)

# === Backtest con Stop-Loss y Take-Profit ===
print("\n⚙️ Backtest CON SL=5% y TP=10%...")
results_st = backtest(
    df,
    commission=0.001,
    slippage=0.0005,
    position_size=1.0,
    stop_loss=0.05,
    take_profit=0.10
)

# === Backtest con Riesgo Fijo ===
print("\n⚙️ Backtest CON Riesgo Fijo (1% por operación, SL=5%)...")
results_risk = backtest(
    df,
    commission=0.001,
    slippage=0.0005,
    fixed_risk=0.01,   # 1% del capital por trade
    stop_loss=0.05,
    take_profit=0.10
)

# ==========================
#   RESULTADOS
# ==========================
def print_results(title, results):
    print(f"\n{title}")
    print(f"Capital final: ${results['final_equity']:.2f}")
    print(f"Retorno total: {results['total_return_pct']:.2f}%")
    print(f"CAGR: {results['cagr']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")

print_results("📈 Resultados SIN SL/TP:", results_base)
print_results("📉 Resultados CON SL/TP (5% / 10%):", results_st)
print_results("⚖️ Resultados CON Riesgo Fijo (1% por trade):", results_risk)

# ==========================
#   GRÁFICAS
# ==========================
plt.figure(figsize=(10,5))
results_base["equity_curve"].plot(label="Base (SIN SL/TP)")
results_st["equity_curve"].plot(label="Con SL/TP", linestyle="--")
results_risk["equity_curve"].plot(label="Riesgo fijo (1% por trade)", linestyle="-.")
plt.title("Comparación de Estrategias - SMA 20/50")
plt.ylabel("Equidad ($)")
plt.xlabel("Fecha")
plt.legend()
plt.show()

# ==========================
#   OPTIMIZACIÓN SMA
# ==========================
print("\n🔎 Ejecutando optimización de SMA...")
results_df = optimize_sma(df, short_range=(5, 30), long_range=(40, 100))

print("\n📊 Top 5 combinaciones por Sharpe Ratio (SMA):")
print(results_df[['short', 'long', 'sharpe_ratio', 'cagr', 'max_drawdown']].head())

print("\n🖼 Generando heatmaps SMA...")
plot_heatmap(results_df, metric="sharpe_ratio")
plot_heatmap(results_df, metric="cagr")

# ==========================
#   OPTIMIZACIÓN SL/TP
# ==========================
print("\n🔎 Ejecutando optimización de Stop-Loss / Take-Profit...")
sl_tp_results = optimize_sl_tp(df, sl_range=(0.02, 0.10, 0.02), tp_range=(0.10, 0.30, 0.05))

print("\n📊 Top 5 combinaciones por Sharpe Ratio (SL/TP):")
print(sl_tp_results.sort_values("sharpe_ratio", ascending=False).head())

print("\n🖼 Generando heatmaps SL/TP...")
plot_heatmap(sl_tp_results, metric="sharpe_ratio")
plot_heatmap(sl_tp_results, metric="cagr")
