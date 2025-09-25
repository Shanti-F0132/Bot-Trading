import pandas as pd
import numpy as np
from backtesting.simple_backtester import backtest

def optimize_sl_tp(df, sl_range=(0.02, 0.10, 0.02), tp_range=(0.05, 0.30, 0.05)):
    """
    Optimiza Stop-Loss y Take-Profit probando distintas combinaciones.

    Parámetros:
    -----------
    df : DataFrame con precios y señales
    sl_range : tupla (start, end, step) para stop-loss en %
    tp_range : tupla (start, end, step) para take-profit en %

    Retorna:
    --------
    DataFrame con resultados de cada combinación
    """

    results = []

    sl_values = np.arange(sl_range[0], sl_range[1] + sl_range[2], sl_range[2])
    tp_values = np.arange(tp_range[0], tp_range[1] + tp_range[2], tp_range[2])

    for sl in sl_values:
        for tp in tp_values:
            res = backtest(
                df,
                commission=0.001,
                slippage=0.0005,
                position_size=1.0,
                stop_loss=sl,
                take_profit=tp
            )
            results.append({
                "stop_loss": sl,
                "take_profit": tp,
                "sharpe_ratio": res["sharpe_ratio"],
                "cagr": res["cagr"],
                "max_drawdown": res["max_drawdown"]
            })

    return pd.DataFrame(results)
