# ============================================================
# main_live_trading.py — Simulación de trading en tiempo real
# ============================================================

import time
import pandas as pd
from utils.data_loader import get_data
from utils.trade_simulator import TradeSimulator
from strategies.sma_strategy import sma_strategy
from strategies.rsi_strategy import rsi_strategy
from strategies.macd_strategy import macd_strategy
from strategies.bollinger_strategy import bollinger_strategy


# ==============================
# 🔧 CONFIGURACIÓN INICIAL
# ==============================
symbol = "AAPL"
initial_capital = 10000
commission = 0.001

print(f"\n📡 Cargando datos históricos para {symbol}...")
df = get_data(symbol, start="2023-01-01", end="2025-10-10", interval="1d")  # <-- más datos
df.dropna(inplace=True)
print(f"✅ Datos cargados: {len(df)} filas ({df.index[0].date()} → {df.index[-1].date()})")

# ==============================
# 🧠 CREAR ESTRATEGIAS Y SIMULADORES
# ==============================
capital_per_strategy = initial_capital / 4

strategies = {
    "SMA": {
        "data": sma_strategy(df.copy()),
        "sim": TradeSimulator(initial_capital=capital_per_strategy, commission=commission)
    },
    "RSI": {
        "data": rsi_strategy(df.copy()),
        "sim": TradeSimulator(initial_capital=capital_per_strategy, commission=commission)
    },
    "MACD": {
        "data": macd_strategy(df.copy()),
        "sim": TradeSimulator(initial_capital=capital_per_strategy, commission=commission)
    },
    "Bollinger": {
        "data": bollinger_strategy(df.copy()),
        "sim": TradeSimulator(initial_capital=capital_per_strategy, commission=commission)
    }
}

print("\n💸 Capital asignado por estrategia:")
for name in strategies:
    print(f"  • {name}: ${capital_per_strategy:,.2f}")

# ==============================
# 🚀 SIMULACIÓN EN TIEMPO REAL
# ==============================
print("\n🚀 Iniciando simulación en tiempo real...\n")

try:
    for i in range(1, len(df)):
        price = df["Close"].iloc[i]

        # Obtener señal de cada estrategia
        signals = {}
        for name, strat in strategies.items():
            data = strat["data"]
            if "Signal" in data.columns:
                signal = data["Signal"].iloc[i]
            elif "signal" in data.columns:
                signal = data["signal"].iloc[i]
            else:
                signal = 0
            signals[name] = signal

        # Mostrar señales activas
        active_signals = {k: v for k, v in signals.items() if v != 0}
        if active_signals:
            print(f"[{df.index[i]}] Precio: {price:.2f} | Señales activas: {active_signals}")

        # Ejecutar señales en cada simulador
        for name, strat in strategies.items():
            sim = strat["sim"]
            signal = signals[name]

            if signal == 1:
                sim.buy(price, name)
            elif signal == -1:
                sim.sell(price, name)

            sim.update_equity(price)

        time.sleep(0.2)  # pequeña pausa para simular flujo de datos

except KeyboardInterrupt:
    print("\n🟥 Simulación interrumpida manualmente.")
except Exception as e:
    print(f"⚠️ Error durante la simulación: {e}")

# ==============================
# 📊 RESULTADOS FINALES
# ==============================
print("\n📊 RESULTADOS FINALES POR ESTRATEGIA")
results = []

for name, strat in strategies.items():
    sim = strat["sim"]
    equity = sim.equity_history[-1] if sim.equity_history else sim.initial_capital
    profit = equity - sim.initial_capital
    profit_pct = (profit / sim.initial_capital) * 100 if sim.initial_capital > 0 else 0

    print(f"\n📈 {name} Strategy:")
    print(f"  - Capital final: ${equity:,.2f}")
    print(f"  - Ganancia total: ${profit:,.2f} ({profit_pct:.2f}%)")
    print(f"  - Operaciones: {len(sim.trades)}")
    results.append(equity)

# ==============================
# 💰 RESULTADO GLOBAL
# ==============================
total_final = sum(results)
profit_total = total_final - initial_capital
profit_pct_total = (profit_total / initial_capital) * 100

print("\n💼 RESUMEN GLOBAL DEL PORTAFOLIO")
print(f"  - Capital inicial: ${initial_capital:,.2f}")
print(f"  - Capital final:   ${total_final:,.2f}")
print(f"  - Rentabilidad:    {profit_pct_total:.2f}%")
print("✅ Simulación completada con éxito.")
