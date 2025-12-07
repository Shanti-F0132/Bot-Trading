# state_manager.py
class StrategyState:
    def __init__(self):
        # prev_signals holds the last "signal" value for each strategy: -1,0,1
        self.prev_signals = {}

    def get_prev(self, name: str):
        return int(self.prev_signals.get(name, 0))

    def set_prev(self, name: str, value):
        self.prev_signals[name] = int(value)


# instancia global que el loop importará
state = StrategyState()
