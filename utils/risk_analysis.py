# utils/risk_analysis.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_returns(equity_series):
    """
    Recibe una Serie (equity curve) y devuelve una Series de retornos simples diarios.
    Acepta pandas Series o numpy array.
    """
    s = pd.Series(equity_series).dropna()
    returns = s.pct_change().dropna()
    return returns


def monte_carlo_simulation(equity_series, n_sims=1000, horizon=252, geometric=True, seed=None):
    """
    Simula n_sims trayectorias Monte Carlo a partir de los retornos históricos de equity_series.

    Parámetros:
    - equity_series: pd.Series (equity curve) o lista/ndarray
    - n_sims: número de simulaciones
    - horizon: número de pasos futuros (por defecto 252 días = 1 año)
    - geometric: si True usa modelo geometrico (GBM-like) con drift (mu) y sigma; si False usa bootstrap de retornos.
    - seed: semilla para reproducibilidad

    Retorna:
    - sims_df: DataFrame (index 0..horizon) columnas = simulaciones, valores = equity (starting from last equity)
    - params: dict con mu, sigma, start_equity
    """
    if seed is not None:
        np.random.seed(seed)

    returns = compute_returns(equity_series)
    if returns.empty:
        raise ValueError("La serie de equity no contiene retornos (equity_series muy corta o NaNs).")

    mu = returns.mean()
    sigma = returns.std()
    start = float(pd.Series(equity_series).dropna().iloc[-1])

    sims = np.zeros((horizon + 1, n_sims))
    sims[0, :] = start

    if geometric:
        # modelo simple multiplicativo: S_t+1 = S_t * exp((mu - 0.5 sigma^2) dt + sigma * sqrt(dt) * Z)
        dt = 1
        drift = mu - 0.5 * sigma ** 2
        for t in range(1, horizon + 1):
            z = np.random.normal(0, 1, n_sims)
            sims[t, :] = sims[t - 1, :] * np.exp(drift * dt + sigma * np.sqrt(dt) * z)
    else:
        # bootstrap de retornos aplicados multiplicativamente
        ret_vals = returns.values
        for t in range(1, horizon + 1):
            draws = np.random.choice(ret_vals, size=n_sims, replace=True)
            sims[t, :] = sims[t - 1, :] * (1 + draws)

    sims_df = pd.DataFrame(sims)
    sims_df.index.name = "step"
    params = {"mu": mu, "sigma": sigma, "start_equity": start}
    return sims_df, params


def compute_var_es(returns, alpha=0.05):
    """
    Calcula Value at Risk (VaR) y Expected Shortfall (ES) para una serie de retornos.
    returns: pd.Series de retornos (por ejemplo, pct_change de equity).
    alpha: nivel (0.05 => 95% VaR)
    Retorna dict con VaR, ES.
    """
    r = pd.Series(returns).dropna()
    if r.empty:
        return {"var": np.nan, "es": np.nan}

    var = np.quantile(r, alpha)  # p-quantile (porcentaje de pérdidas)
    es = r[r <= var].mean() if not r[r <= var].empty else var
    return {"var": var, "es": es}


def summarize_simulations(sims_df):
    """
    Devuelve un DataFrame resumen con percentiles finales de la simulación:
    p5, p25, p50, p75, p95 y la probabilidad de superar el capital inicial.
    """
    final_vals = sims_df.iloc[-1, :].values
    percentiles = np.percentile(final_vals, [5, 25, 50, 75, 95])
    summary = {
        "p5": percentiles[0],
        "p25": percentiles[1],
        "median": percentiles[2],
        "p75": percentiles[3],
        "p95": percentiles[4],
        "mean_final": final_vals.mean(),
        "prob>start": np.mean(final_vals > sims_df.iloc[0, 0])
    }
    return pd.Series(summary)


def plot_monte_carlo(sims_df, title="Monte Carlo Simulations", n_paths=50, save_path=None):
    """
    Grafica una muestra de trayectorias y las bandas percentiles (p5,p25,p50,p75,p95).
    - sims_df: DataFrame (index steps, columns sims)
    - n_paths: número de trayectorias individuales a graficar (aleatorias)
    - save_path: si se especifica, guarda PNG
    Retorna la figura y el axis.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6))

    # plot sample paths
    n_sims = sims_df.shape[1]
    sample_cols = np.random.choice(sims_df.columns, size=min(n_paths, n_sims), replace=False)
    for c in sample_cols:
        ax.plot(sims_df.index, sims_df[c], color="gray", alpha=0.3, linewidth=0.8)

    # percentiles envelope
    p5 = sims_df.quantile(0.05, axis=1)
    p25 = sims_df.quantile(0.25, axis=1)
    p50 = sims_df.quantile(0.50, axis=1)
    p75 = sims_df.quantile(0.75, axis=1)
    p95 = sims_df.quantile(0.95, axis=1)

    ax.plot(sims_df.index, p50, color="blue", label="Median")
    ax.fill_between(sims_df.index, p25, p75, color="blue", alpha=0.15, label="25-75 pct")
    ax.fill_between(sims_df.index, p5, p95, color="blue", alpha=0.08, label="5-95 pct")

    ax.set_title(title)
    ax.set_xlabel("Steps")
    ax.set_ylabel("Equity")
    ax.legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig, ax


def plot_final_distribution(sims_df, save_path=None, bins=50):
    """
    Histograma de valores finales de las simulaciones.
    """
    final_vals = sims_df.iloc[-1, :].values
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(final_vals, bins=bins, density=False, alpha=0.8)
    ax.axvline(np.mean(final_vals), color="red", label=f"Mean {np.mean(final_vals):.2f}")
    ax.axvline(np.median(final_vals), color="blue", label=f"Median {np.median(final_vals):.2f}")
    ax.set_title("Distribución de valores finales (Monte Carlo)")
    ax.set_xlabel("Equity final")
    ax.set_ylabel("Frecuencia")
    ax.legend()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
    return fig, ax
