import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def plot_heatmap(results_df, metric="sharpe_ratio"):
    """
    Genera un heatmap (mapa de calor) para visualizar el desempeño
    de la estrategia según combinaciones de short y long SMA.
    
    Parámetros:
    -----------
    results_df : pandas.DataFrame
        Debe contener columnas 'short', 'long' y la métrica a graficar.
    metric : str
        Nombre de la métrica a visualizar (por ejemplo: 'sharpe_ratio', 'cagr').
    """

    pivot_table = results_df.pivot(index="short", columns="long", values=metric)

    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_table, annot=False, cmap="RdYlGn", cbar_kws={'label': metric})
    plt.title(f"Mapa de calor para {metric}")
    plt.xlabel("SMA Larga")
    plt.ylabel("SMA Corta")
    plt.tight_layout()
    plt.show()
