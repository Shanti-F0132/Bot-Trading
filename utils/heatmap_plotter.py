import matplotlib.pyplot as plt
import seaborn as sns

def plot_heatmap(results_df, metric="sharpe_ratio", ax=None):
    """
    Genera un heatmap a partir de resultados de optimización.
    Si se pasa un objeto ax, lo dibuja en ese subplot.
    """

    # Detectar tipo de optimización según columnas
    if {"short", "long"}.issubset(results_df.columns):
        index_col, col_col = "short", "long"
    elif {"stop_loss", "take_profit"}.issubset(results_df.columns):
        index_col, col_col = "stop_loss", "take_profit"
    elif {"period", "overbought"}.issubset(results_df.columns):
        index_col, col_col = "period", "overbought"
    elif {"period", "oversold"}.issubset(results_df.columns):
        index_col, col_col = "period", "oversold"
    elif {"fast", "slow"}.issubset(results_df.columns):
        index_col, col_col = "fast", "slow"
    elif {"window", "num_std"}.issubset(results_df.columns):
        index_col, col_col = "window", "num_std"
    else:
        raise ValueError("No se detectaron columnas válidas para heatmap.")

    # Crear tabla pivote para el heatmap
    pivot_table = results_df.pivot_table(
        index=index_col,
        columns=col_col,
        values=metric,
        aggfunc="mean"
    )

    # Dibujar heatmap
    if ax is None:  # Caso normal (cada heatmap en su propia figura)
        plt.figure(figsize=(10, 6))
        sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="viridis")
        plt.title(f"Heatmap de {metric} ({index_col} vs {col_col})")
        plt.xlabel(col_col)
        plt.ylabel(index_col)
        plt.show()
    else:  # Dibujar en un subplot existente
        sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="viridis", ax=ax)
        ax.set_title(f"Heatmap de {metric} ({index_col} vs {col_col})")
        ax.set_xlabel(col_col)
        ax.set_ylabel(index_col)
