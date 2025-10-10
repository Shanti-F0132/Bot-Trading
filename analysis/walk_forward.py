import pandas as pd
import numpy as np
from backtesting.simple_backtester import backtest
from utils.data_loader import get_data
from itertools import product

def walk_forward_analysis(strategy_func, param_grid, symbol="AAPL", start="2018-01-01", end="2024-01-01", n_splits=4):
    """
    📆 Realiza validación Walk-Forward de una estrategia.
    Divide el histórico en segmentos temporales (train/test),
    optimiza en train y evalúa fuera de muestra en test.
    """

    print(f"\n🚀 Iniciando Walk-Forward Analysis para {strategy_func.__name__} ({symbol})")
    df = get_data(symbol, start, end)
    split_size = len(df) // n_splits
    results = []

    for i in range(n_splits - 1):
        train = df.iloc[: split_size * (i + 1)]
        test = df.iloc[split_size * (i + 1): split_size * (i + 2)]

        print(f"\n🧩 Segmento {i + 1}/{n_splits - 1}")
        print(f"   Entrenamiento: {train.index[0].date()} → {train.index[-1].date()}")
        print(f"   Prueba: {test.index[0].date()} → {test.index[-1].date()}")

        # 🔹 Buscar la mejor combinación en entrenamiento
        best_sharpe, best_params = -np.inf, None
        for combo in product(*param_grid.values()):
            params = dict(zip(param_grid.keys(), combo))
            try:
                df_train = strategy_func(train.copy(), **params)
                metrics = backtest(df_train)
                sharpe = metrics.get("sharpe_ratio", 0)
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params
            except Exception:
                continue

        print(f"   🏆 Mejor conjunto de parámetros: {best_params} (Sharpe {best_sharpe:.3f})")

        # 🔹 Evaluar fuera de muestra (test)
        df_test = strategy_func(test.copy(), **best_params)
        test_metrics = backtest(df_test)
        test_metrics["params"] = best_params
        results.append(test_metrics)

    df_results = pd.DataFrame(results)
    df_results["segment"] = range(1, len(df_results) + 1)
    print("\n✅ Walk-Forward completado.\n")
    return df_results
