# utils/portfolio_manager.py
import pandas as pd
from copy import deepcopy
from datetime import datetime
import numpy as np

class PortfolioManager:
    """
    Administra múltiples estrategias (señales) sobre un mismo activo en paper trading.
    - Cada estrategia tiene su propio registro de posición (units) y P&L.
    - Las órdenes se ejecutan usando un TradeSimulator (compartido).
    - Se permite sizing por peso o por riesgo fijo (fractional).
    """

    def __init__(self, simulator, strategies, initial_capital=10000):
        """
        Administra múltiples estrategias dentro de un portafolio.
        Cada estrategia recibe una asignación de capital independiente.
        """
        self.sim = simulator
        self.strategies = strategies
        self.initial_capital = initial_capital
        self.history = 0
        self.equity_history = []

        # 🧩 Asignar capital igual por estrategia
        capital_per_strat = initial_capital / len(strategies)
        self.positions = {
            name: {"cash_alloc": capital_per_strat, "units": 0, "last_price": 0}
            for name in strategies.keys()
        }

        print(f"✅ Portafolio inicializado con ${initial_capital:.2f}")
        for name, pos in self.positions.items():
            print(f"   • {name}: ${pos['cash_alloc']:.2f} asignados")

    # ------------------------------------------------------

    def register_strategy(self, name, weight=0.0, risk_fraction=None):
        """
        Añade una estrategia al portafolio.
        - weight: porcentaje del capital total (0..1) asignado a esa estrategia.
        - risk_fraction: si se desea sizing por riesgo (ej. 0.01 para 1% por trade).
        """
        self.positions[name] = {
            "units": 0.0,
            "avg_price": None,
            "weight": weight,
            "risk_fraction": risk_fraction,
            "cash_alloc": 0.0
        }

    def update_weights(self, weights_dict):
        """Actualizar pesos (weights_dict = {'SMA':0.4, 'RSI':0.6, ...})"""
        for k, v in weights_dict.items():
            if k in self.positions:
                self.positions[k]["weight"] = float(v)

    def allocate_cash(self):
        """Recalcula la asignación de efectivo para cada estrategia según pesos actuales."""
        total = self.sim.cash + sum([p["units"] * (self.sim.last_price or 0) for p in self.positions.values()])
        for name, p in self.positions.items():
            p["cash_alloc"] = p["weight"] * total

    def can_buy(self, name, price):
        """Comprueba si la estrategia tiene cash_alloc suficiente para comprar (toma en cuenta comisiones)."""
        p = self.positions[name]
        alloc = p["cash_alloc"]
        if alloc is None or alloc <= 0:
            return False
        # calcular unidades comprables
        units = (alloc * (1 - self.sim.commission)) / price
        return units > 0

    def buy(self, name, price, symbol="N/A"):
        """Compra usando la asignación de la estrategia (toma todo el cash_alloc disponible)."""
        self.allocate_cash()
        p = self.positions[name]
        alloc = p["cash_alloc"]
        if alloc <= 0:
            # nada asignado
            return False

        # no duplicar compras si ya tiene posición: podemos permitir scaling (aumentar)
        units = (alloc * (1 - self.sim.commission)) / price
        if units <= 0:
            return False

        # Ejecutar en el simulador: usamos buy parcial (sim.buy usa todo cash)
        # Para respetar la separación por estrategia, hacemos el cálculo y modificamos el simulador manualmente.
        # Simulador original hace: uses cash -> buys all cash. Lo usaremos así para simplicidad: guardamos pre-cash.
        pre_cash = self.sim.cash
        # Si el simulador no tiene suficiente cash para la alloc (porque otro ya usó cash),
        # ejecutamos con lo que quede.
        amount_to_use = min(pre_cash, alloc)
        if amount_to_use <= 0:
            return False

        # Ejecutar compra proporcional: calculamos unidades
        units_bought = (amount_to_use * (1 - self.sim.commission)) / price

        # Actualizamos simulador directamente (comportamiento similar a sim.buy but partial)
        self.sim.cash = pre_cash - amount_to_use  # consumimos la parte usada
        self.sim.position += units_bought
        self.sim.last_price = price
        trade = {
            "time": datetime.now(),
            "strategy": name,
            "symbol": symbol,
            "action": "BUY",
            "price": price,
            "units": units_bought,
            "amount": amount_to_use
        }
        self.history.append(trade)

        # actualizar posición por estrategia: promedio de precio
        if p["units"] == 0:
            p["avg_price"] = price
            p["units"] = units_bought
        else:
            existing_value = p["units"] * p["avg_price"]
            new_value = units_bought * price
            total_units = p["units"] + units_bought
            p["avg_price"] = (existing_value + new_value) / total_units
            p["units"] = total_units

        return True

    def sell(self, name, price, symbol="N/A"):
        """Vende toda la posición asociada a la estrategia (si existe)."""
        p = self.positions[name]
        if p["units"] <= 0:
            return False

        units_to_sell = p["units"]
        proceeds = units_to_sell * price * (1 - self.sim.commission)

        # Actualizar simulador
        self.sim.cash += proceeds
        self.sim.last_price = price
        # restar del position global (sim)
        # balance: sim.position is total across strategies; decrease it
        self.sim.position = max(0.0, self.sim.position - units_to_sell)

        trade = {
            "time": datetime.now(),
            "strategy": name,
            "symbol": symbol,
            "action": "SELL",
            "price": price,
            "units": units_to_sell,
            "amount": proceeds
        }
        self.history.append(trade)

        # resetear la posición de esa estrategia
        p["units"] = 0.0
        p["avg_price"] = None

        return True

    def update_all_equity(self, current_price):
        """Registra el equity total (cash + posiciones globales * precio)."""
        total_value = sum(
            pos["cash_alloc"] + pos["units"] * current_price
            for pos in self.positions.values()
        )
        self.equity_history.append(total_value)
        return total_value

    def summary(self):
        """Resumen del portafolio (combina info del simulador y posiciones por estrategia)."""
        final_value = self.sim.cash + self.sim.position * (self.sim.last_price or 0)
        drawdown = self.calculate_drawdown()

        return {
            "initial_capital": self.sim.initial_capital,
            "final_value": final_value,
            "profit": final_value - self.sim.initial_capital,
            "profit_pct": ((final_value / self.sim.initial_capital) - 1) * 100,
            "drawdown": drawdown,
            "trades": self.history,
            "equity_history": self.equity_history,
            "positions": {k: deepcopy(v) for k, v in self.positions.items()}
    }

    def update_positions(self, current_price, signals):
        """
        Ejecuta operaciones para cada estrategia según sus señales.
        Señal = 1 → Compra | Señal = -1 → Venta
        """
        for name, signal in signals.items():
            if name not in self.positions:
                continue

            pos = self.positions[name]
            cash = pos.get("cash_alloc", 0)
            units = pos.get("units", 0)

            # Validar precio
            if current_price is None or current_price <= 0:
                continue

            # 🟢 Compra
            if signal == 1 and cash > current_price:
                units_to_buy = cash // current_price
                cost = units_to_buy * current_price
                pos["units"] += units_to_buy
                pos["cash_alloc"] -= cost
                self.history += 1
                print(f"🟢 [{name}] Compra ejecutada: {units_to_buy} unidades a {current_price:.2f}")

            # 🔴 Venta
            elif signal == -1 and units > 0:
                proceeds = units * current_price
                pos["cash_alloc"] += proceeds
                pos["units"] = 0
                self.history += 1
                print(f"🔴 [{name}] Venta ejecutada a {current_price:.2f}")

            # Actualizar último precio
            pos["last_price"] = current_price

        # Actualizar equity total
        total_equity = sum(
            pos["cash_alloc"] + pos["units"] * current_price
            for pos in self.positions.values()
        )
        self.sim.cash = total_equity
        self.equity_history.append(total_equity)

        print(f"💰 Equity actualizado: {total_equity:.2f} | Cash total: {self.sim.cash:.2f}")

    # ------------------------------------------------------

    def calculate_drawdown(self):
        """Calcula el drawdown máximo basado en el historial de equity."""
        if not self.equity_history or len(self.equity_history) < 2:
            return None

        equity = np.array(self.equity_history)
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = np.min(drawdown)

        return max_drawdown * 100  # en porcentaje
    

