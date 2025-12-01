from strategies.sma_strategy import sma_strategy
from strategies.rsi_strategy import rsi_strategy
from strategies.macd_strategy import macd_strategy
from strategies.bollinger_strategy import bollinger_strategy
from strategies.combo_sma_macd import combo_sma_macd

def run_strategy(df, strategy_name: str, **kwargs):

    """
    Ejecuta la estrategia seleccionada y devuelve la señal actual.
    
    Retorna:
        -1 = SELL
         0 = HOLD
         1 = BUY
    """
    strategy_name = strategy_name.lower()

    if strategy_name == "sma":
        return sma_strategy(df, **kwargs)
    
    elif strategy_name == "rsi":
        return rsi_strategy(df, **kwargs)

    elif strategy_name == "macd":
        return macd_strategy(df, **kwargs)

    elif strategy_name == "bollinger":
        return bollinger_strategy(df, **kwargs)
    
    elif strategy_name == "combo_sma_macd":
        return combo_sma_macd(df, **kwargs)

    else:
        raise ValueError(f"Estrategia '{strategy_name}' no reconocida.")

