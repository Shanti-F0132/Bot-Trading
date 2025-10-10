import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
# Usar backend 'Agg' para evitar problemas con Tkinter en entornos sin GUI
matplotlib.use("Agg")
import seaborn as sns
from utils.data_loader import get_data
from backtesting.simple_backtester import backtest

def analyze_robustness(strategy_func, param_grid, symbol="AAPL", start="2020-01-01", end="2024-01-01", save_path=None):
    """
    🔍 Analiza la robustez de una estrategia probando diferentes combinaciones de parámetros.
    Evalúa estabilidad del Sharpe Ratio, CAGR y Max Drawdown.
    """

    print(f"\n   Analizando robustez para {strategy_func.__name__} en {symbol}...")

    # Descargar datos históricos
    df = get_data(symbol, start, end)

    # Generar combinaciones de parámetros
    keys = list(param_grid.keys())
    combinations = list(itertools.product(*param_grid.values()))
    total = len(combinations)

    results = []
    print(f"📈 Probando {total} combinaciones de parámetros...")

    # Evaluar todas las combinaciones
    for i, combo in enumerate(combinations, 1):
        params = dict(zip(keys, combo))
        try:
            df_copy = df.copy()
            df_test = strategy_func(df_copy, **params)
            metrics = backtest(df_test)
            results.append({
                **params,
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "cagr": metrics.get("cagr", 0),
                "max_drawdown": metrics.get("max_drawdown", 0)
            })
            print(f"  ✅ {i}/{total} -> {params} | Sharpe: {metrics.get('sharpe_ratio', 0):.3f}")
        except Exception as e:
            print(f"  ⚠️ Error con {params}: {e}")

    df_results = pd.DataFrame(results)

    # Crear Heatmap si hay 2 parámetros
    if len(keys) == 2 and not df_results.empty:
        pivot = df_results.pivot(index=keys[0], columns=keys[1], values="sharpe_ratio")
        plt.figure(figsize=(8, 6))
        sns.heatmap(pivot, annot=True, cmap="YlGnBu", fmt=".2f", cbar_kws={'label': 'Sharpe Ratio'})
        plt.title(f"Robustez de {strategy_func.__name__} - {symbol}", fontsize=13)
        plt.xlabel(keys[1])
        plt.ylabel(keys[0])
        plt.tight_layout()

        # Guardar o mostrar sin usar Tkinter
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"📊 Heatmap guardado en: {save_path}")
        else:
            plt.show(block=False)
            plt.pause(3)
            plt.close()

    print(f"✅ Análisis completado para {strategy_func.__name__}")
    return df_results
