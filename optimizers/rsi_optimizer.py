import pandas as pd
import numpy as np
from backtesting.simple_backtester import backtest
from strategies.rsi_strategy import rsi_strategy

def optimize_rsi(df, period_range=(10, 30), overbought_range=(60, 80), oversold_range=(20, 40)):
    """
    Optimiza parámetros de RSI (period, overbought, oversold).
    
    Parámetros:
    -----------
    df : DataFrame con datos de precios
    period_range : tupla (start, end) rango de periodos RSI
    overbought_range : tupla (start, end) rango de sobrecompra
    oversold_range : tupla (start, end) rango de sobreventa

    Retorna:
    --------
    DataFrame con resultados de cada combinación
    """

    results = []

    for period in range(period_range[0], period_range[1] + 1, 2):  # step de 2
        for overbought in range(overbought_range[0], overbought_range[1] + 1, 5):  # step de 5
            for oversold in range(oversold_range[0], oversold_range[1] + 1, 5):  # step de 5
                if oversold >= overbought:
                    continue  # evitar parámetros inválidos

                df_rsi = rsi_strategy(df.copy(), rsi_period=period, lower=oversold, upper=overbought)
                res = backtest(df_rsi, commission=0.001, slippage=0.0005, position_size=1.0)

                results.append({
                    "period": period,
                    "overbought": overbought,
                    "oversold": oversold,
                    "sharpe_ratio": res["sharpe_ratio"],
                    "cagr": res["cagr"],
                    "max_drawdown": res["max_drawdown"]
                })

    return pd.DataFrame(results)
