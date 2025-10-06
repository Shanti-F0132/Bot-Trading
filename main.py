import matplotlib.pyplot as plt
import pandas as pd

# === Imports de módulos internos ===
from utils.data_loader import get_data
from strategies.sma_strategy import sma_strategy
from strategies.rsi_strategy import rsi_strategy
from strategies.macd_strategy import macd_strategy
from strategies.bollinger_strategy import bollinger_strategy
from optimizers.sma_optimizer import optimize_sma
from optimizers.rsi_optimizer import optimize_rsi
from optimizers.macd_optimizer import optimize_macd
from optimizers.bollinger_optimizer import optimize_bollinger
from backtesting.simple_backtester import backtest
from utils.heatmap_plotter import plot_heatmap
from utils.report_generator import generate_report

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
    # --- Lista de activos a probar ---
    symbols = ["AAPL", "MSFT", "TSLA"]  # puedes agregar más, incluso "BTC-USD" o "EURUSD=X"

    all_results = []

    for symbol in symbols:
        print(f"\n📥 Descargando datos de {symbol}...")
        df = get_data(symbol, start="2015-01-01", end="2025-01-01")

        # --- Estrategias ---
        print(f"\n⚙️ Backtesting en {symbol}...")

        # SMA
        df_sma = sma_strategy(df.copy(), short=10, long=50)
        res_sma = backtest(df_sma)
        print_metrics(res_sma, f"SMA ({symbol})")
        all_results.append({"Activo": symbol, "Estrategia": "SMA", **res_sma})

        # RSI
        df_rsi = rsi_strategy(df.copy(), period=14, overbought=70, oversold=30)
        res_rsi = backtest(df_rsi)
        print_metrics(res_rsi, f"RSI ({symbol})")
        all_results.append({"Activo": symbol, "Estrategia": "RSI", **res_rsi})

        # MACD
        df_macd = macd_strategy(df.copy(), fast=12, slow=26, signal=9)
        res_macd = backtest(df_macd)
        print_metrics(res_macd, f"MACD ({symbol})")
        all_results.append({"Activo": symbol, "Estrategia": "MACD", **res_macd})

        # Bollinger
        df_bb = bollinger_strategy(df.copy(), window=20, num_std=2)
        res_bb = backtest(df_bb)
        print_metrics(res_bb, f"Bollinger Bands ({symbol})")
        all_results.append({"Activo": symbol, "Estrategia": "Bollinger", **res_bb})

    # ==========================
    #   TABLA FINAL DE RESULTADOS
    # ==========================
    df_all = pd.DataFrame(all_results)

    print("\n📊 Resultados globales (todos los activos y estrategias):\n")
    print(df_all[["Activo", "Estrategia", "final_equity", "cagr", "sharpe_ratio",
                  "sortino_ratio", "calmar_ratio", "profit_factor", "win_rate", "max_drawdown"]])

    # Mejor estrategia por activo
    print("\n🏆 Mejor estrategia por activo (Sharpe Ratio):\n")
    best_per_symbol = df_all.loc[df_all.groupby("Activo")["sharpe_ratio"].idxmax()]
    print(best_per_symbol[["Activo", "Estrategia", "sharpe_ratio", "cagr", "max_drawdown"]])

    # ==========================
    #   COMPARACIÓN DE ESTRATEGIAS
    # ==========================
    print("\n📊 Comparación de estrategias...")

    # === Ejecutar backtests para cada estrategia ===
    results_sma = backtest(df_sma)
    results_rsi = backtest(df_rsi)
    results_macd = backtest(df_macd)
    results_bb = backtest(df_bb)

    # === Guardar resultados en lista para comparación ===
    all_results = []
    all_results.append({"Activo": symbol, "Estrategia": "SMA", **results_sma})
    all_results.append({"Activo": symbol, "Estrategia": "RSI", **results_rsi})
    all_results.append({"Activo": symbol, "Estrategia": "MACD", **results_macd})
    all_results.append({"Activo": symbol, "Estrategia": "Bollinger Bands", **results_bb})

    # === Convertir a DataFrame para mejor visualización ===
    df_comparacion = pd.DataFrame(all_results)

    # Ordenar por Sharpe Ratio (mejor estrategia arriba)
    df_comparacion = df_comparacion.sort_values(by="sharpe_ratio", ascending=False)

   # === RANKING EXPANDIDO ===
    print("\n🏆 Ranking de estrategias por activo:")

    # Normalizamos métricas para que tengan escalas comparables
    df_all["Sharpe_norm"] = (df_all["sharpe_ratio"] - df_all["sharpe_ratio"].min()) / (df_all["sharpe_ratio"].max() - df_all["sharpe_ratio"].min())
    df_all["CAGR_norm"] = (df_all["cagr"] - df_all["cagr"].min()) / (df_all["cagr"].max() - df_all["cagr"].min())
    df_all["MaxDD_norm"] = (df_all["max_drawdown"].max() - df_all["max_drawdown"]) / (df_all["max_drawdown"].max() - df_all["max_drawdown"].min())

    # Score compuesto
    df_all["score"] = 0.5 * df_all["Sharpe_norm"] + 0.3 * df_all["CAGR_norm"] + 0.2 * df_all["MaxDD_norm"]

    # Mostrar ranking por activo
    for symbol in df_all["Activo"].unique():
        df_symbol = df_all[df_all["Activo"] == symbol].sort_values(by="score", ascending=False)
        print(f"\n🔎 {symbol}")
        print(df_symbol[["Estrategia", "sharpe_ratio", "cagr", "max_drawdown", "score"]])

    # Ranking global
    print("\n🌍 Ranking global (todos los activos):")
    df_global = df_all.groupby("Estrategia").mean(numeric_only=True).sort_values(by="score", ascending=False)
    print(df_global[["sharpe_ratio", "cagr", "max_drawdown", "score"]])


    # === Visualización del ranking global ===
    plt.figure(figsize=(8, 5))
    plt.bar(df_global.index, df_global["score"], color="skyblue", edgecolor="black")
    plt.title("Ranking Global de Estrategias (Score Compuesto)", fontsize=14)
    plt.ylabel("Score", fontsize=12)
    plt.xlabel("Estrategia", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.savefig("global_strategy_ranking.png")
    plt.show()
    plt.close()

    # === Visualización del ranking por activo ===
    for symbol in df_all["Activo"].unique():
        df_symbol = df_all[df_all["Activo"] == symbol]

        plt.figure(figsize=(8, 5))
        plt.bar(df_symbol["Estrategia"], df_symbol["score"], color="lightgreen", edgecolor="black")
        plt.title(f"Ranking de Estrategias - {symbol}", fontsize=14)
        plt.ylabel("Score", fontsize=12)
        plt.xlabel("Estrategia", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.savefig(f"{symbol}_strategy_ranking.png")
        plt.show()
        plt.close()

    
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
    plt.savefig("capital_comparison.png")
    plt.show()
    plt.close()

        # === Función para calcular drawdowns ===
    def calculate_drawdown(equity_curve):
        cumulative_max = equity_curve.cummax()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        return drawdown

    # === Calcular drawdowns de cada estrategia ===
    drawdown_sma = calculate_drawdown(results_sma["equity_curve"])
    drawdown_rsi = calculate_drawdown(results_rsi["equity_curve"])
    drawdown_macd = calculate_drawdown(results_macd["equity_curve"])
    drawdown_bb = calculate_drawdown(results_bb["equity_curve"])

    # === Crear figura con subplots ===
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={"height_ratios": [2, 1]})

    # --- Subplot 1: Curvas de capital ---
    ax1.plot(results_sma["equity_curve"], label="SMA")
    ax1.plot(results_rsi["equity_curve"], label="RSI")
    ax1.plot(results_macd["equity_curve"], label="MACD")
    ax1.plot(results_bb["equity_curve"], label="Bollinger Bands")
    ax1.set_title("Curvas de Capital - Estrategias")
    ax1.set_ylabel("Capital ($)")
    ax1.legend()
    ax1.grid(True)

    # --- Subplot 2: Drawdowns ---
    ax2.plot(drawdown_sma, label="SMA")
    ax2.plot(drawdown_rsi, label="RSI")
    ax2.plot(drawdown_macd, label="MACD")
    ax2.plot(drawdown_bb, label="Bollinger Bands")
    ax2.set_title("Comparación de Drawdowns - Estrategias")
    ax2.set_xlabel("Fecha")
    ax2.set_ylabel("Drawdown (%)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("capital_and_drawdown_comparison.png")
    plt.show()
    plt.close()

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
    plt.savefig("heatmaps_comparison.png")
    plt.show()
    plt.close()

    # ==========================
    #   GENERACIÓN DE REPORTES
    # ==========================
    print("\n📝 Generando reporte PDF...")

    results_dict = {
        "SMA": results_sma,
        "RSI": results_rsi,
        "MACD": results_macd,
        "Bollinger": results_bb
    }

    # Generar el PDF
    generate_report(
        "reporte_final.pdf",
        all_results,
        charts=[
            "C:\\Users\\david\\Desktop\\Bot01\\AAPL_strategy_ranking.png",
            "C:\\Users\\david\\Desktop\\Bot01\\MSFT_strategy_ranking.png",
            "C:\\Users\\david\\Desktop\\Bot01\\TSLA_strategy_ranking.png",
            "C:\\Users\\david\\Desktop\\Bot01\\global_strategy_ranking.png",
            "C:\\Users\\david\\Desktop\\Bot01\\capital_comparison.png",
            "C:\\Users\\david\\Desktop\\Bot01\\capital_and_drawdown_comparison.png",
            "C:\\Users\\david\\Desktop\\Bot01\\heatmaps_comparison.png"
    ]
    )
