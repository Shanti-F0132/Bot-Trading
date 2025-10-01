import pandas as pd
from backtesting.simple_backtester import backtest
from strategies.macd_strategy import macd_strategy

def optimize_macd(df, fast_range=(8, 20), slow_range=(20, 40), signal_range=(5, 15)):
    """
    Optimiza parámetros de MACD (fast, slow, signal).

    Parámetros:
    -----------
    df : DataFrame con datos de precios
    fast_range : tupla (min, max) para EMA rápida
    slow_range : tupla (min, max) para EMA lenta
    signal_range : tupla (min, max) para línea de señal

    Retorna:
    --------
    DataFrame con métricas de cada combinación
    """

    results = []

    for fast in range(fast_range[0], fast_range[1] + 1, 2):  # step de 2
        for slow in range(slow_range[0], slow_range[1] + 1, 2):
            if fast >= slow:  # fast siempre debe ser menor que slow
                continue
            for signal in range(signal_range[0], signal_range[1] + 1, 2):
                df_macd = macd_strategy(df.copy(), fast=fast, slow=slow, signal=signal)
                res = backtest(df_macd, commission=0.001, slippage=0.0005, position_size=1.0)

                results.append({
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "sharpe_ratio": res["sharpe_ratio"],
                    "cagr": res["cagr"],
                    "max_drawdown": res["max_drawdown"]
                })

    return pd.DataFrame(results)
