import pandas as pd
import itertools
from strategies.sma_strategy import sma_crossover
from backtesting.simple_backtester import backtest

def optimize_sma(df, short_range=(5, 50), long_range=(30, 200)):
    """
    Optimiza la estrategia SMA probando combinaciones de short y long.
    
    Parámetros:
    -----------
    df : pandas.DataFrame
        DataFrame con columna 'Close'
    short_range : tuple (min, max)
        Rango de SMA corta a probar.
    long_range : tuple (min, max)
        Rango de SMA larga a probar.

    Retorna:
    --------
    pandas.DataFrame con resultados de cada combinación ordenados por Sharpe Ratio.
    """

    results = []

    for short, long in itertools.product(range(short_range[0], short_range[1]+1, 5),
                                         range(long_range[0], long_range[1]+1, 10)):
        if short >= long:
            continue  # SMA corta no puede ser >= a SMA larga

        df_signals = sma_crossover(df, short=short, long=long)
        res = backtest(df_signals)

        results.append({
            "short": short,
            "long": long,
            "final_equity": res["final_equity"],
            "total_return_pct": res["total_return_pct"],
            "cagr": res["cagr"],
            "sharpe_ratio": res["sharpe_ratio"],
            "max_drawdown": res["max_drawdown"]
        })

    results_df = pd.DataFrame(results)
    results_df.sort_values(by="sharpe_ratio", ascending=False, inplace=True)
    results_df.reset_index(drop=True, inplace=True)

    return results_df
