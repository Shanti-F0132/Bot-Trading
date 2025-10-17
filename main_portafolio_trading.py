# main_portfolio_trading.py
"""
Script unificado para Paper Trading de portafolio.
Adaptable a distintas versiones de tus utilidades (data_loader, portfolio_manager).
Guarda resultados en outputs/ y grafica la equity curve si plot_utils está disponible.
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Ajustes de paths / outputs
# ---------------------------------------------------------
os.makedirs("outputs", exist_ok=True)

# ---------------------------------------------------------
# Import helpers (intento flexible)
# ---------------------------------------------------------
# data loader: preferimos get_data(symbol, start, end)
try:
    from utils.data_loader import get_data
    data_loader_fn = "get_data"
except Exception:
    # fallback to data_streamer.stream_data
    try:
        from utils.data_streamer import stream_data
        get_data = None
        data_streamer = stream_data
        data_loader_fn = "stream_data"
    except Exception:
        print("❌ No pude importar utils.data_loader ni utils.data_streamer. Asegúrate de que existan.")
        raise

# plot util (optional)
try:
    from utils.plot_utils import plot_equity_curve
    have_plot_utils = True
except Exception:
    have_plot_utils = False

# PortfolioManager: intento distintas firmas
try:
    from utils.portfolio_manager import PortfolioManager
except Exception:
    print("❌ No se pudo importar utils.portfolio_manager. Asegúrate del path y del nombre de la clase.")
    raise

# Estrategias (si no existen, el script fallará: asegúrate de tenerlas)
from strategies.sma_strategy import sma_strategy as sma_strategy
from strategies.rsi_strategy import rsi_strategy as rsi_strategy
from strategies.macd_strategy import macd_strategy as macd_strategy
from strategies.bollinger_strategy import bollinger_strategy as bollinger_strategy

# ---------------------------------------------------------
# Configuración
# ---------------------------------------------------------
SYMBOL = "AAPL"
INITIAL_CAPITAL = 10000
COMMISSION = 0.001
# ventana de datos histórica
END = datetime.now()
START = END - timedelta(days=365 * 2)

print("🚀 Iniciando main_portfolio_trading.py")
print(f"Símbolo: {SYMBOL} | Capital inicial: ${INITIAL_CAPITAL:,.2f}\n")

# ---------------------------------------------------------
# 1) Cargar datos (con tolerancia a firmas diferentes)
# ---------------------------------------------------------
print("📡 Cargando datos...")

if data_loader_fn == "get_data":
    # Intentamos varias firmas comunes: (symbol, start, end), (symbol, period, interval), (symbol, period)
    df = None
    try:
        df = get_data(SYMBOL, start=START, end=END)
    except TypeError:
        # tal vez la firma es get_data(symbol, period, interval)
        try:
            df = get_data(SYMBOL, period="2y", interval="1d")
        except Exception:
            df = None
    except Exception:
        df = None
else:
    # usamos stream_data como fallback (no live)
    try:
        df = data_streamer(SYMBOL, interval="1d", live=False)
    except Exception as e:
        print("❌ Error llamando a data_streamer:", e)
        df = None

if df is None or df.empty:
    raise RuntimeError("❌ No se cargaron datos. Revisa data_loader o data_streamer.")

# Normalizar columnas (asegura 'Close' en mayúscula)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [c[0].capitalize() for c in df.columns]
else:
    df.columns = [c.capitalize() for c in df.columns]

df = df[~df.index.duplicated(keep="first")].sort_index()
print(f"✅ Datos cargados: {len(df)} filas. Rango: {df.index[0].date()} -> {df.index[-1].date()}\n")

# ---------------------------------------------------------
# 2) Generar señales por estrategia
# ---------------------------------------------------------
print("⚙️ Calculando señales...")

# Cada función de estrategia suele devolver un DataFrame con columna 'Signal' (o 'signal').
# Adaptamos llamadas por si las firmas son diferentes.
strategies = {}
try:
    strategies["SMA"] = sma_strategy(df.copy(), short_window=10, long_window=30)
except TypeError:
    # alternativa de firma
    strategies["SMA"] = sma_strategy(df.copy(), short=10, long=30)

try:
    strategies["RSI"] = rsi_strategy(df.copy(), window=14, lower=30, upper=70)
except TypeError:
    strategies["RSI"] = rsi_strategy(df.copy(), rsi_period=14, lower=30, upper=70)

try:
    strategies["MACD"] = macd_strategy(df.copy())
except Exception:
    # si MACD necesita parámetros diferentes o no existe, se omite pero avisamos
    try:
        strategies["MACD"] = macd_strategy(df.copy(), fast=12, slow=26, signal=9)
    except Exception:
        print("⚠️ MACD strategy failed to run; skipping.")
        strategies.pop("MACD", None)

try:
    strategies["Bollinger"] = bollinger_strategy(df.copy(), window=20, num_std=2)
except TypeError:
    strategies["Bollinger"] = bollinger_strategy(df.copy())

# Verificación rápida de señales
print("\n🔍 Señales únicas por estrategia (muestra):")
for name, s_df in strategies.items():
    col = "Signal" if "Signal" in s_df.columns else ("signal" if "signal" in s_df.columns else None)
    if col:
        uniq = np.unique(s_df[col].dropna().values)
        print(f"  • {name}: {uniq}")
    else:
        print(f"  • {name}: ⚠️ no encontró columna 'Signal'/'signal'")

print()

# ---------------------------------------------------------
# 3) Crear instancia de PortfolioManager (intento flexible)
# ---------------------------------------------------------
print(" Inicializando PortfolioManager...")

pm = None
# Primero intento la firma que vimos en varias versiones: PortfolioManager(simulator)
# Si existe TradeSimulator en utils, usarlo; si no, intentamos construir PM pasando estrategias directamente.
try:
    # intentar traer TradeSimulator
    from utils.trade_simulator import TradeSimulator
    sim = TradeSimulator(initial_capital=INITIAL_CAPITAL, commission=COMMISSION)
except Exception:
    sim = None

# Intentos de creación más comunes:
# 1) PortfolioManager(simulator=sim)
# 2) PortfolioManager(simulator, strategies, initial_capital)
# 3) PortfolioManager(initial_capital=INITIAL_CAPITAL)  <-- versión simplificada
try:
    if sim is not None:
        try:
            pm = PortfolioManager(simulator=sim)
        except TypeError:
            try:
                pm = PortfolioManager(sim, strategies, initial_capital=INITIAL_CAPITAL)
            except TypeError:
                pm = PortfolioManager(initial_capital=INITIAL_CAPITAL)
    else:
        pm = PortfolioManager(initial_capital=INITIAL_CAPITAL)
except Exception as e:
    print("❌ No pude instanciar PortfolioManager con las firmas probadas:", e)
    raise

print("✅ PortfolioManager instanciado.\n")

# ---------------------------------------------------------
# 4) Configurar pesos / asignación
# ---------------------------------------------------------
# Default: pesos iguales entre estrategias activas
active_strats = list(strategies.keys())
if not active_strats:
    raise RuntimeError("❌ No hay estrategias activas. Revisa las implementaciones.")

equal_weights = {name: 1.0 / len(active_strats) for name in active_strats}

# aplicar pesos: intentamos distintos métodos disponibles
if hasattr(pm, "update_weights"):
    try:
        pm.update_weights(equal_weights)
    except Exception:
        pass
elif hasattr(pm, "allocate_cash"):
    try:
        # allocate_cash puede tomar un dict o no; probamos sin args y luego con args
        try:
            pm.allocate_cash()
        except TypeError:
            pm.allocate_cash(equal_weights)
    except Exception:
        pass
else:
    # si no existe ninguno, intentamos set attribute directly
    try:
        pm.weights = equal_weights
    except Exception:
        pass

print("📦 Pesos aplicados (por defecto iguales):")
for k, v in equal_weights.items():
    print(f"   {k}: {v:.3f}")
print()

# ---------------------------------------------------------
# 5) Loop principal: iterar sobre las filas y aplicar señales
# ---------------------------------------------------------
print("📈 Ejecutando simulación de trading...\n")

# Aseguramos que todos los DataFrames de estrategias estén index-aligned con df
# Si no, usaremos iloc para acceder por posición.
use_index_alignment = all(df.index.equals(s.index) for s in strategies.values())

for i in range(1, len(df)):
    price = float(df["Close"].iloc[i])
    # construir dict signals: si tiene 'Signal' o 'signal' usa eso
    signals = {}
    for name, s_df in strategies.items():
        col = "Signal" if "Signal" in s_df.columns else ("signal" if "signal" in s_df.columns else None)
        if col:
            # intentamos por index si coincide, si no por iloc
            try:
                val = s_df[col].iloc[i] if use_index_alignment else s_df[col].iloc[i]  # iloc seguro
            except Exception:
                # fallback: 0
                val = 0
        else:
            val = 0
        # convertir numpy types a int
        try:
            signals[name] = int(np.sign(val)) if not pd.isna(val) else 0
        except Exception:
            signals[name] = int(val) if val is not None else 0

    # Depuración: mostrar señales activas
    if any(v != 0 for v in signals.values()):
        print(f"[{df.index[i].date()}] Precio: {price:.2f} | Señales activas: {signals}")

    # Llamada tolerante a update_positions:
    # Intentamos primero la firma (current_price, signals)
    updated = False
    if hasattr(pm, "update_positions"):
        try:
            pm.update_positions(price, signals)
            updated = True
        except TypeError:
            # tal vez la firma es (price_data, signals) — le damos el slice df.iloc[:i+1]
            try:
                pm.update_positions(df.iloc[: i + 1], signals)
                updated = True
            except Exception:
                updated = False
        except Exception:
            updated = False

    # Si no existe update_positions, intentamos otros métodos (buy/sell API) - opcional
    if not updated:
        # Intentamos fallback simple: si pm tiene sim, modificamos sim directamente (compra todo si any positive)
        if hasattr(pm, "sim"):
            combined_signal = np.sign(sum(signals.values()))
            try:
                if combined_signal == 1 and getattr(pm.sim, "position", 0) == 0:
                    # comprar todo
                    units = (getattr(pm.sim, "cash", INITIAL_CAPITAL) * (1 - COMMISSION)) / price
                    pm.sim.position = units
                    pm.sim.cash = 0
                    print(f"🟢 [FALLBACK] Compra ejecutada (sim) a {price:.2f}")
                elif combined_signal == -1 and getattr(pm.sim, "position", 0) > 0:
                    pm.sim.cash = pm.sim.position * price * (1 - COMMISSION)
                    pm.sim.position = 0
                    print(f"🔴 [FALLBACK] Venta ejecutada (sim) a {price:.2f}")
            except Exception:
                pass

    # Actualizar equity: preferimos método update_all_equity(current_price)
    if hasattr(pm, "update_all_equity"):
        try:
            pm.update_all_equity(price)
        except TypeError:
            # some versions accept no args
            try:
                pm.update_all_equity()
            except Exception:
                pass
        except Exception:
            pass
    else:
        # fallback: si tiene sim con cash/position
        if hasattr(pm, "sim"):
            total_value = getattr(pm.sim, "cash", 0) + getattr(pm.sim, "position", 0) * price
            if hasattr(pm, "equity_history"):
                pm.equity_history.append(total_value)

# ---------------------------------------------------------
# 6) Resumen final (intentar summary() o get_summary())
# ---------------------------------------------------------
summary = {}
if hasattr(pm, "summary"):
    try:
        summary = pm.summary()
    except TypeError:
        try:
            summary = pm.get_summary()
        except Exception:
            summary = {}
elif hasattr(pm, "get_summary"):
    summary = pm.get_summary()
else:
    # construir summary básico desde atributos
    final_value = None
    if hasattr(pm, "equity_history") and pm.equity_history:
        final_value = pm.equity_history[-1]
    elif hasattr(pm, "sim"):
        final_value = getattr(pm.sim, "cash", 0) + getattr(pm.sim, "position", 0) * float(df["Close"].iloc[-1])
    else:
        final_value = INITIAL_CAPITAL

    summary = {
        "initial_capital": getattr(pm, "initial_capital", INITIAL_CAPITAL),
        "final_value": final_value,
        "profit": final_value - getattr(pm, "initial_capital", INITIAL_CAPITAL),
        "profit_pct": (final_value / getattr(pm, "initial_capital", INITIAL_CAPITAL) - 1) * 100,
        "trades": getattr(pm, "history", 0),
        "equity_history": getattr(pm, "equity_history", []),
        "positions": getattr(pm, "positions", {})
    }

# normalize keys
summary.setdefault("initial_capital", INITIAL_CAPITAL)
summary.setdefault("final_value", summary.get("final_value", INITIAL_CAPITAL))
summary.setdefault("profit", summary["final_value"] - summary["initial_capital"])
summary.setdefault("profit_pct", (summary["profit"] / summary["initial_capital"]) * 100 if summary["initial_capital"] else 0)
summary.setdefault("trades", getattr(pm, "history", 0))
summary.setdefault("equity_history", getattr(pm, "equity_history", []))
summary.setdefault("positions", getattr(pm, "positions", {}))

# if drawdown method exists, compute it
max_dd = None
if hasattr(pm, "calculate_drawdown"):
    try:
        max_dd = pm.calculate_drawdown()
    except Exception:
        max_dd = None

# ---------------------------------------------------------
# 7) Imprimir & guardar resultados
# ---------------------------------------------------------
print("\n📊 RESULTADOS FINALES DEL PORTAFOLIO")
print(f"Capital inicial:  ${summary['initial_capital']:.2f}")
print(f"Capital final:    ${summary['final_value']:.2f}")

profit = summary["profit"]
profit_pct = summary["profit_pct"]
if summary["equity_history"]:
    print(f"Ganancia total:   ${profit:.2f} ({profit_pct:.2f}%)")
    print(f"Último equity:    ${summary['equity_history'][-1]:.2f}")
else:
    print("⚠️ No hay historial de equity registrado durante la simulación.")

trades = summary["trades"]
num_trades = len(trades) if isinstance(trades, (list, tuple)) else trades
print(f"Operaciones:      {num_trades}")

print(f"Drawdown máximo:  {max_dd:.2f}%" if max_dd is not None else "Drawdown máximo:  N/A")
print(f"Posiciones abiertas: {len(summary['positions'])}")

# Guardar CSV: trades (si existe historial de trades/positions)
try:
    if isinstance(summary.get("trades"), (list, tuple)) and summary["trades"]:
        pd.DataFrame(summary["trades"]).to_csv("outputs/portfolio_trades.csv", index=False)
    # equity
    if summary["equity_history"]:
        pd.DataFrame({"equity": summary["equity_history"]}).to_csv("outputs/portfolio_equity.csv", index=False)
    print("💾 Results saved to outputs/ (portfolio_trades.csv, portfolio_equity.csv)")
except Exception as e:
    print("⚠️ No se pudieron guardar algunos CSVs:", e)

# ---------------------------------------------------------
# 8) Graficar equity si disponemos de plot_utils
# ---------------------------------------------------------
if summary["equity_history"] and have_plot_utils:
    try:
        eqdf = pd.DataFrame({"Equity": summary["equity_history"]})
        plot_equity_curve(eqdf, title="Portfolio Equity Curve")
    except Exception as e:
        print("⚠️ Error al graficar equity curve:", e)
elif summary["equity_history"] and not have_plot_utils:
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        plt.plot(summary["equity_history"])
        plt.title("Portfolio Equity Curve")
        plt.ylabel("Equity")
        plt.xlabel("Step")
        plt.grid(True)
        plt.show()
    except Exception as e:
        print("⚠️ Error al graficar con matplotlib:", e)

print("\n✅ Simulación completada.")
