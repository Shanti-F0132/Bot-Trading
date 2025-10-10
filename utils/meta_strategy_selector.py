import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def evaluate_strategies(recent_results):
    """
    Evalúa las estrategias con base en métricas recientes.
    recent_results: dict con métricas de cada estrategia (sharpe_ratio, cagr, max_drawdown, etc.)
    Retorna un DataFrame ordenado por Sharpe Ratio.
    """
    df = pd.DataFrame(recent_results).T
    df = df.sort_values(by="sharpe_ratio", ascending=False)
    return df


def select_best_strategy(all_results, mode="weighted"):
    """
    Selecciona la mejor estrategia o construye un portafolio ponderado
    basado en múltiples métricas de desempeño.
    """

    print("\n📈 Analizando rendimiento global de estrategias...")

    required_cols = {"strategy", "sharpe_ratio", "cagr", "max_drawdown"}
    if not required_cols.issubset(all_results.columns):
        print("⚠️ Faltan columnas necesarias en los resultados.")
        return None

    # Agrupar y calcular métricas promedio por estrategia
    metrics = (
        all_results.groupby("strategy")[["sharpe_ratio", "cagr", "max_drawdown"]]
        .mean()
        .reset_index()
    )

    # Normalizar valores para comparabilidad
    metrics["sharpe_norm"] = metrics["sharpe_ratio"] / metrics["sharpe_ratio"].abs().max()
    metrics["cagr_norm"] = metrics["cagr"] / metrics["cagr"].abs().max()
    metrics["dd_norm"] = 1 - (metrics["max_drawdown"] / metrics["max_drawdown"].abs().max())

    # Score ponderado (70% Sharpe, 20% CAGR, 10% Drawdown)
    metrics["score"] = (
        0.7 * metrics["sharpe_norm"]
        + 0.2 * metrics["cagr_norm"]
        + 0.1 * metrics["dd_norm"]
    )

    if mode == "best":
        best = metrics.loc[metrics["score"].idxmax()]
        print(f"🏆 Mejor estrategia: {best['strategy']} (Score: {best['score']:.3f})")
        return best

    elif mode == "weighted":
        # Normalizar scores para pesos relativos
        weights = metrics.set_index("strategy")["score"]
        weights = weights / weights.sum()

        print("\n📊 Pesos asignados:")
        print(weights)

        # Visualización de los pesos
        plt.figure(figsize=(6, 4))
        weights.sort_values().plot(kind="barh", color="skyblue")
        plt.title("Distribución de pesos por estrategia")
        plt.xlabel("Peso relativo")
        plt.tight_layout()
        plt.savefig("outputs/charts/strategy_weights.png")
        plt.close()

        return weights


def simulate_meta_portfolio(df_dict, weights):
    """
    Combina las curvas de capital de varias estrategias según sus pesos.
    Devuelve la curva combinada (meta-equity).
    """
    equity_combined = None
    for name, df in df_dict.items():
        if "equity_curve" not in df.columns:
            continue
        if equity_combined is None:
            equity_combined = df["equity_curve"] * weights.get(name, 0)
        else:
            equity_combined += df["equity_curve"] * weights.get(name, 0)

    print("\n📈 Meta-estrategia combinada generada exitosamente.")
    return equity_combined
