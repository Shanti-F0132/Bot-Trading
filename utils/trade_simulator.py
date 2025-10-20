# utils/trade_simulator.py
from datetime import datetime

class TradeSimulator:
    """
    Simula operaciones en tiempo real (Paper Trading).
    Mantiene registro de capital, posiciones y resultados.
    """

    def __init__(self, initial_capital=10000, commission=0.001, live=False):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = 0
        self.last_price = None
        self.commission = commission
        self.trades = []
        self.equity_history = []

    def buy(self, price, symbol="N/A"):
        """Ejecuta una compra simulada."""
        if self.cash <= 0:
            print("❌ No hay suficiente capital para comprar.")
            return

        self.last_price = price
        units = (self.cash * (1 - self.commission)) / price
        self.position += units
        self.cash = 0
        self.trades.append({
            "time": datetime.now(),
            "symbol": symbol,
            "action": "BUY",
            "price": price,
            "units": units
        })
        print(f"🟢 [{symbol}] Compra ejecutada: {units:.4f} unidades a ${price:.2f}")

    def sell(self, price, symbol="N/A"):
        """Ejecuta una venta simulada."""
        if self.position <= 0:
            print("❌ No hay posición abierta para vender.")
            return

        self.last_price = price
        proceeds = self.position * price * (1 - self.commission)
        self.cash += proceeds
        self.trades.append({
            "time": datetime.now(),
            "symbol": symbol,
            "action": "SELL",
            "price": price,
            "units": self.position
        })
        print(f"🔴 [{symbol}] Venta ejecutada: {self.position:.4f} unidades a ${price:.2f}")
        self.position = 0

    def update_equity(self, current_price):
        """Actualiza el valor total del portafolio."""
        total_value = self.cash + self.position * current_price
        self.equity_history.append(total_value)
        return total_value

    def summary(self):
        """Muestra el resumen final del rendimiento."""
        final_value = self.cash + self.position * (self.last_price or 0)
        profit = final_value - self.initial_capital
        profit_pct = (profit / self.initial_capital) * 100
        print(f"\n📊 RESULTADOS DEL PAPER TRADING")
        print(f"Capital inicial: ${self.initial_capital:,.2f}")
        print(f"Valor final:     ${final_value:,.2f}")
        print(f"Ganancia total:  ${profit:,.2f} ({profit_pct:.2f}%)")
        print(f"Operaciones:     {len(self.trades)}")
        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "profit": profit,
            "profit_pct": profit_pct,
            "trades": self.trades
        }
