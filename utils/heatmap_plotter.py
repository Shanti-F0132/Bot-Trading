import matplotlib.pyplot as plt
import seaborn as sns

def plot_heatmap(results_df, metric="sharpe_ratio"):
    """
    Genera un heatmap a partir de resultados de optimización.
    Funciona tanto para SMA (short/long) como para SL/TP (stop_loss/take_profit).

    Parámetros:
    -----------
    results_df : DataFrame con resultados
    metric : str, métrica a graficar ("sharpe_ratio", "cagr", etc.)
    """

    # Detectar columnas automáticamente
    if {"short", "long"}.issubset(results_df.columns):
        index_col, col_col = "short", "long"
    elif {"stop_loss", "take_profit"}.issubset(results_df.columns):
        index_col, col_col = "stop_loss", "take_profit"
    else:
        raise ValueError("El DataFrame no contiene columnas válidas para heatmap (short/long o stop_loss/take_profit).")

    # Crear tabla dinámica
    pivot_table = results_df.pivot(index=index_col, columns=col_col, values=metric)

    # Dibujar heatmap
    plt.figure(figsize=(10,6))
    sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="viridis")
    plt.title(f"Heatmap de {metric} ({index_col} vs {col_col})")
    plt.xlabel(col_col)
    plt.ylabel(index_col)
    plt.show()
