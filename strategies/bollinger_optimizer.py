import pandas as pd
from backtesting.simple_backtester import backtest
from strategies.bollinger_strategy import bollinger_strategy

def optimize_bollinger(df, window_range=(10, 30), num_std_range=(1, 3)):
    results = []

    for window in range(window_range[0], window_range[1] + 1):
        for num_std in range(num_std_range[0], num_std_range[1] + 1):
            # Aplicamos la estrategia con parámetros actuales
            df_bb = bollinger_strategy(df.copy(), window=window, num_std=num_std)

            # Ejecutamos el backtest
            res = backtest(df_bb)

            # Saltamos combinaciones que no generen cambios (capital igual al inicial)
            if res["final_equity"] == 10000:  
                continue  

            results.append({
                "window": window,
                "num_std": num_std,
                "final_equity": res["final_equity"],
                "total_return_pct": res["total_return_pct"],
                "cagr": res["cagr"],
                "sharpe_ratio": res["sharpe_ratio"],
                "max_drawdown": res["max_drawdown"]
            })

    return pd.DataFrame(results)
