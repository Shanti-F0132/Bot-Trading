import matplotlib.pyplot as plt
import pandas as pd

# === Imports de módulos internos ===
from utils.data_loader import get_data
from strategies.sma_strategy import sma_strategy
from strategies.rsi_strategy import rsi_strategy
from strategies.macd_strategy import macd_strategy
from strategies.bollinger_strategy import bollinger_strategy
from strategies.sma_optimizer import optimize_sma
from strategies.rsi_optimizer import optimize_rsi
from strategies.macd_optimizer import optimize_macd
from strategies.bollinger_optimizer import optimize_bollinger
from backtesting.simple_backtester import backtest
from utils.heatmap_plotter import plot_heatmap

# === Función estándar para imprimir métricas ===
def print_metrics(results, strategy_name="Estrategia"):
    print(f"\n📈 Resultados del Backtest - {strategy_name}")
    print(f"Capital final: ${results['final_equity']:.2f}")
    print(f"Retorno total: {results['total_return_pct']:.2f}%")
    print(f"CAGR: {results['cagr']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {results['sortino_ratio']:.2f}")
    print(f"Calmar Ratio: {results['calmar_ratio']:.2f}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")


# ==========================
#   PIPELINE PRINCIPAL
# ==========================
if __name__ == "__main__":
    # 1. Descargar datos
    print("📥 Descargando datos de AAPL...")
    df = get_data("AAPL", start="2015-01-01", end="2025-01-01")

    # 2. SMA Strategy
    print("\n⚙️ Backtest con SMA...")
    df_sma = sma_strategy(df.copy(), short=10, long=50)
    results_sma = backtest(df_sma)
    print_metrics(results_sma, "SMA")

    # 3. RSI Strategy
    print("\n⚙️ Backtest con RSI...")
    df_rsi = rsi_strategy(df.copy(), period=14, overbought=70, oversold=30)
    results_rsi = backtest(df_rsi)
    print_metrics(results_rsi, "RSI")

    # 4. MACD Strategy
    print("\n⚙️ Backtest con MACD...")
    df_macd = macd_strategy(df.copy(), fast=12, slow=26, signal=9)
    results_macd = backtest(df_macd)
    print_metrics(results_macd, "MACD")

    # 5. Bollinger Bands Strategy
    print("\n⚙️ Backtest con Bollinger Bands...")
    df_bb = bollinger_strategy(df.copy(), window=20, num_std=2)
    results_bb = backtest(df_bb)
    print_metrics(results_bb, "Bollinger Bands")

    # ==========================
    #   COMPARACIÓN DE ESTRATEGIAS
    # ==========================
    print("\n📊 Comparación de estrategias...")

    results_summary = [
        {"Estrategia": "SMA", **results_sma},
        {"Estrategia": "RSI", **results_rsi},
        {"Estrategia": "MACD", **results_macd},
        {"Estrategia": "Bollinger Bands", **results_bb},
    ]

    df_results = pd.DataFrame(results_summary)
    print("\n📋 Resultados comparativos:")
    print(df_results[["Estrategia", "final_equity", "cagr", "sharpe_ratio", "sortino_ratio",
                      "calmar_ratio", "profit_factor", "win_rate", "max_drawdown"]])

    # === Gráfica de curvas de capital ===
    plt.figure(figsize=(12, 6))
    plt.plot(results_sma["equity_curve"], label="SMA")
    plt.plot(results_rsi["equity_curve"], label="RSI")
    plt.plot(results_macd["equity_curve"], label="MACD")
    plt.plot(results_bb["equity_curve"], label="Bollinger Bands")
    plt.title("Comparación de Curvas de Capital")
    plt.xlabel("Tiempo")
    plt.ylabel("Capital")
    plt.legend()
    plt.show()

    # ==========================
    #   RANKING DE ESTRATEGIAS
    # ==========================
    print("\n🏆 Ranking de estrategias...")

    # --- Menú de selección de métrica ---
    print("\nSelecciona la métrica para ordenar el ranking:")
    print("1) Sharpe Ratio (Mayor es mejor)")
    print("2) CAGR (Mayor es mejor)")
    print("3) Max Drawdown (Menor es mejor)")

    choice_rank = input("👉 Ingresa el número (1-3): ").strip()

    if choice_rank == "1":
        rank_metric = "sharpe_ratio"
        ascending_order = False
    elif choice_rank == "2":
        rank_metric = "cagr"
        ascending_order = False
    elif choice_rank == "3":
        rank_metric = "max_drawdown"
        ascending_order = True   # Drawdown se minimiza
    else:
        print("⚠️ Opción inválida, se usará Sharpe Ratio por defecto.")
        rank_metric = "sharpe_ratio"
        ascending_order = False

    # --- Ordenar estrategias ---
    df_ranked = df_results.sort_values(by=rank_metric, ascending=ascending_order).reset_index(drop=True)

    print(f"\n📊 Ranking de estrategias basado en: {rank_metric}\n")
    print(df_ranked[["Estrategia", "final_equity", "cagr", "sharpe_ratio",
                "sortino_ratio", "calmar_ratio", "profit_factor",
                "win_rate", "max_drawdown"]])

    # Mejor estrategia
    best_strategy = df_ranked.iloc[0]
    print(f"\n✅ La mejor estrategia según {rank_metric} es: {best_strategy['Estrategia']} "
          f"({rank_metric}: {best_strategy[rank_metric]:.2f})")

    
    # ==========================
    #   GRÁFICAS INDIVIDUALES
    # ==========================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # SMA
    axes[0, 0].plot(results_sma["equity_curve"], label="SMA", color="blue")
    axes[0, 0].set_title("Curva de Capital - SMA")
    axes[0, 0].set_xlabel("Tiempo")
    axes[0, 0].set_ylabel("Capital")
    axes[0, 0].legend()

    # RSI
    axes[0, 1].plot(results_rsi["equity_curve"], label="RSI", color="orange")
    axes[0, 1].set_title("Curva de Capital - RSI")
    axes[0, 1].set_xlabel("Tiempo")
    axes[0, 1].set_ylabel("Capital")
    axes[0, 1].legend()

    # MACD
    axes[1, 0].plot(results_macd["equity_curve"], label="MACD", color="green")
    axes[1, 0].set_title("Curva de Capital - MACD")
    axes[1, 0].set_xlabel("Tiempo")
    axes[1, 0].set_ylabel("Capital")
    axes[1, 0].legend()

    # Bollinger Bands
    axes[1, 1].plot(results_bb["equity_curve"], label="Bollinger Bands", color="purple")
    axes[1, 1].set_title("Curva de Capital - Bollinger Bands")
    axes[1, 1].set_xlabel("Tiempo")
    axes[1, 1].set_ylabel("Capital")
    axes[1, 1].legend()

    plt.suptitle("Curvas de Capital por Estrategia", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()

    # ==========================
    #   HEATMAPS AGRUPADOS
    # ==========================
    print("\n📊 Generando heatmaps de optimización...")

    # Optimización de cada estrategia
    heatmap_sma = optimize_sma(df.copy())
    heatmap_rsi = optimize_rsi(df.copy())
    heatmap_macd = optimize_macd(df.copy())
    heatmap_bb = optimize_bollinger(df.copy())

    # --- Menú de selección de métrica ---
    print("\nSelecciona la métrica a visualizar en los heatmaps:")
    print("1) Sharpe Ratio")
    print("2) CAGR")
    print("3) Max Drawdown")

    choice = input("👉 Ingresa el número (1-3): ").strip()

    if choice == "1":
        metric_to_plot = "sharpe_ratio"
    elif choice == "2":
        metric_to_plot = "cagr"
    elif choice == "3":
        metric_to_plot = "max_drawdown"
    else:
        print("⚠️ Opción inválida, se usará Sharpe Ratio por defecto.")
        metric_to_plot = "sharpe_ratio"

    print(f"\n📊 Generando heatmaps usando la métrica: {metric_to_plot}")

    # --- Subplots 2x2 ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # SMA
    plot_heatmap(heatmap_sma, metric=metric_to_plot, ax=axes[0, 0])
    axes[0, 0].set_title(f"SMA - {metric_to_plot}")

    # RSI
    plot_heatmap(heatmap_rsi, metric=metric_to_plot, ax=axes[0, 1])
    axes[0, 1].set_title(f"RSI - {metric_to_plot}")

    # MACD
    plot_heatmap(heatmap_macd, metric=metric_to_plot, ax=axes[1, 0])
    axes[1, 0].set_title(f"MACD - {metric_to_plot}")

    # Bollinger Bands
    plot_heatmap(heatmap_bb, metric=metric_to_plot, ax=axes[1, 1])
    axes[1, 1].set_title(f"Bollinger Bands - {metric_to_plot}")

    plt.suptitle(f"Heatmaps de Optimización ({metric_to_plot})", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.show()

