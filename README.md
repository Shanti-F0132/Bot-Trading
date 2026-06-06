<div align="center">

# QuantBot - de Trading Cuantitativo

**Motor de análisis cuantitativo, backtesting avanzado y trading algorítmico en tiempo real**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Alpaca](https://img.shields.io/badge/Alpaca-API-FECC02?style=for-the-badge&logo=alpaca&logoColor=black)
![yfinance](https://img.shields.io/badge/Yahoo%20Finance-yfinance-720e9e?style=for-the-badge)
![Version](https://img.shields.io/badge/Versión-1.1.3-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/Licencia-MIT-blue?style=for-the-badge)

> **Aviso:** Este proyecto es de carácter educativo e investigativo. El trading algorítmico conlleva riesgos reales. No inviertas dinero que no puedas permitirte perder.

</div>

---

## Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Tecnologías utilizadas](#-tecnologías-utilizadas)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Flujo del sistema](#-flujo-del-sistema)
- [Autor](#-autor)

---

## Descripción

**QuantBot** es un sistema de trading cuantitativo modular desarrollado en Python que integra un pipeline completo: desde la descarga y normalización de datos históricos, hasta la ejecución de órdenes en tiempo real a través del broker Alpaca.

El sistema permite evaluar múltiples estrategias técnicas (SMA, MACD, RSI, Bollinger Bands) sobre distintos activos y timeframes, optimizar sus parámetros mediante búsqueda en grilla, validar su robustez estadística con análisis Walk-Forward y Monte Carlo, y finalmente ejecutar la estrategia elegida en un loop de trading en vivo con gestión de riesgo dinámica basada en ATR, bracket orders y cooldown entre operaciones.

Toda la ejecución del backtesting genera automáticamente un **reporte PDF consolidado** con gráficos, métricas, heatmaps y análisis de riesgo, listo para presentación o revisión.

---

## Características

### Descarga y preparación de datos
- Descarga de datos OHLCV históricos desde **Yahoo Finance** vía `yfinance`
- Normalización y limpieza automática de columnas para compatibilidad entre módulos
- Soporte para múltiples activos simultáneos (`AAPL`, `MSFT`, `TSLA`, `BTC-USD`, `EURUSD=X`, etc.)
- Resampling dinámico a timeframes diario, semanal y mensual

### Estrategias técnicas implementadas
- **SMA Crossover** — cruce de medias móviles corta/larga
- **MACD** — convergencia/divergencia de medias con línea de señal
- **RSI** — índice de fuerza relativa con zonas de sobrecompra y sobreventa
- **Bollinger Bands** — rupturas de bandas de volatilidad
- **Combo SMA+MACD** — estrategia combinada disponible en el loop en vivo

### Backtesting avanzado
- Motor propio de backtesting con simulación de **slippage** y **comisiones**
- Cálculo de métricas profesionales: CAGR, Sharpe Ratio, Sortino Ratio, Calmar Ratio, Profit Factor, Win Rate y Max Drawdown
- Curvas de capital individuales y comparativas
- Comparación multi-activo y multi-estrategia con **score compuesto** ponderado

### Optimización de parámetros
- Búsqueda en grilla (*grid search*) para cada estrategia
- Visualización de resultados en **heatmaps** interactivos (Sharpe, CAGR, Max Drawdown)
- Selección automática de los mejores parámetros por activo

### Análisis de robustez y riesgo
- **Walk-Forward Analysis** con ventanas temporales sucesivas para validación fuera de muestra
- **Monte Carlo** con 1,000 simulaciones geométricas de caminos de capital
- Cálculo de **VaR (Value at Risk)** y **Expected Shortfall (CVaR)** al 5%
- Análisis de sensibilidad por estrategia y activo

### Meta-estrategia adaptativa
- Evaluación automática de todas las estrategias disponibles
- Construcción de un **portafolio ponderado** según rendimiento histórico (Sharpe/CAGR/Drawdown)
- Comparación visual de la meta-estrategia vs. estrategias individuales

### Trading en vivo (Alpaca)
- Loop continuo de ejecución con datos en tiempo real desde Alpaca Data API
- **Bracket orders** automáticas con Take Profit y Stop Loss calculados dinámicamente en base a ATR
- Gestión de riesgo dinámica: position sizing por ATR, límite de riesgo por operación (0.2% del equity)
- Filtro de horario de mercado (9:45–15:45 ET) y cooldown entre operaciones (5 minutos)
- Registro automático de trades en `trades.log` con PnL, duración y motivo de cierre (TP/SL)
- Soporte para múltiples versiones del loop (v1.0, v1.0.1, v1.1.3)

### Generación de reportes
- **Reporte PDF profesional** generado automáticamente con `reportlab`
- Incluye: métricas, curvas de capital, drawdowns, heatmaps, robustez, Monte Carlo y walk-forward
- Subtítulos explicativos automáticos en cada sección
- Exportado a `outputs/reports/reporte_final.pdf`

---

## Tecnologías utilizadas

| Categoría | Tecnología | Uso |
|---|---|---|
| **Lenguaje** | Python 3.10+ | Desarrollo completo del sistema |
| **Datos históricos** | `yfinance` | Descarga de datos OHLCV desde Yahoo Finance |
| **Broker / Datos en vivo** | Alpaca Trading API | Ejecución de órdenes y datos en tiempo real |
| **Análisis de datos** | `pandas`, `numpy` | Manipulación de series temporales y cálculo de métricas |
| **Visualización** | `matplotlib`, `seaborn` | Gráficos de curvas, drawdowns, heatmaps y distribuciones |
| **Reportes** | `reportlab` | Generación automática de reportes PDF |
| **Variables de entorno** | `python-dotenv` | Gestión segura de credenciales API |
| **Utilidades** | `os`, `glob`, `time`, `math`, `pytz` | Manejo de archivos, zonas horarias y operaciones de sistema |

---

## Estructura del proyecto

```
Bot-Trading/
│
├── main_backtest.py              # Pipeline principal de análisis y backtesting
├── live_trading_loop_1.0.1.py   # Loop de trading en vivo (versión 1.0.1)
├── live_trading_loop_1.1.3.py   # Loop de trading en vivo (versión 1.1.3 - actual)
├── lector_csv_analisis.py        # Utilidad para leer y analizar CSVs de resultados
├── logger_test.py                # Script de prueba del sistema de logging
├── requirements.txt              # Dependencias del proyecto
├── trades.log                    # Registro histórico de operaciones ejecutadas
│
├── strategies/                   # Módulos de estrategias técnicas
│   ├── sma_strategy.py           # Estrategia SMA Crossover
│   ├── rsi_strategy.py           # Estrategia RSI
│   ├── macd_strategy.py          # Estrategia MACD
│   ├── bollinger_strategy.py     # Estrategia Bollinger Bands
│   ├── strategy_loader.py        # Cargador dinámico de estrategias
│   └── data_normalizer.py        # Normalización de columnas OHLCV
│
├── backtesting/
│   └── simple_backtester.py      # Motor de backtesting con slippage y comisiones
│
├── optimizers/                   # Optimización de parámetros por estrategia
│   ├── sma_optimizer.py
│   ├── rsi_optimizer.py
│   ├── macd_optimizer.py
│   └── bollinger_optimizer.py
│
├── analysis/                     # Módulos de análisis estadístico avanzado
│   ├── risk_analysis.py          # Monte Carlo, VaR y Expected Shortfall
│   ├── robustness_analysis.py    # Análisis de robustez y sensibilidad
│   └── walk_forward.py           # Validación Walk-Forward fuera de muestra
│
├── broker_api/                   # Integración con Alpaca
│   ├── alpaca_client.py          # Cliente autenticado de Alpaca
│   └── state_manager.py          # Gestión de estado del bot en tiempo real
│
├── utils/                        # Utilidades compartidas
│   ├── data_loader.py            # Descarga y preparación de datos
│   ├── heatmap_plotter.py        # Visualización de heatmaps
│   ├── report_generator.py       # Generador de reportes PDF
│   ├── trade_logger.py           # Sistema de logging de operaciones
│   └── meta_strategy_selector.py # Evaluación y selección de meta-estrategia
│
└── outputs/                      # Carpeta de salida (generada en ejecución)
    ├── charts/                   # Gráficos generados (.png)
    ├── csv/                      # Resultados Walk-Forward (.csv)
    └── reports/                  # Reportes PDF finales
```

---

## Instalación

### Requisitos previos

- Python 3.10 o superior
- Cuenta en [Alpaca Markets](https://alpaca.markets/) (paper trading o live trading)
- Credenciales de API de Alpaca (API Key y Secret Key)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Shanti-F0132/Bot-Trading.git
cd Bot-Trading
```

### 2. Crear y activar un entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

> Las dependencias incluyen: `pandas`, `numpy`, `matplotlib`, `yfinance`, `seaborn`, `reportlab`, `python-dotenv` y el SDK de Alpaca (`alpaca-trade-api` o `alpaca-py`).

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con tus credenciales de Alpaca:

```env
ALPACA_API_KEY=tu_api_key_aquí
ALPACA_SECRET_KEY=tu_secret_key_aquí
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # para paper trading
```

> Nunca subas el archivo `.env` a GitHub. Agrega `.env` a tu `.gitignore`.

---

## Uso

### Ejecutar el pipeline completo de backtesting

El script `main_backtest.py` ejecuta todo el pipeline de análisis en secuencia:

```bash
python main_backtest.py
```

**Este script realiza automáticamente:**

1. Descarga datos históricos de `AAPL`, `MSFT` y `TSLA` desde Yahoo Finance
2. Ejecuta backtesting para las 4 estrategias (SMA, RSI, MACD, Bollinger Bands)
3. Imprime métricas detalladas por activo y estrategia
4. Genera un ranking compuesto (Sharpe + CAGR + Drawdown)
5. Solicita selección de métrica para heatmaps (Sharpe / CAGR / Max Drawdown)
6. Ejecuta análisis de Monte Carlo y calcula VaR / Expected Shortfall
7. Realiza análisis de robustez por estrategia y activo
8. Ejecuta Walk-Forward Analysis y guarda resultados CSV
9. Evalúa la meta-estrategia adaptativa
10. Genera el reporte PDF final en `outputs/reports/reporte_final.pdf`

---

### Ejecutar el loop de trading en vivo

Edita los parámetros de configuración en `live_trading_loop_1.1.3.py`:

```python
SYMBOL    = "AMD"       # Activo a operar
STRATEGY  = "sma"      # Estrategia: "sma", "macd", "rsi", "bollinger", "combo_sma_macd"
INTERVAL  = "5m"       # Timeframe: "1m", "5m", "15m", "1h", "1d"
```

Luego ejecuta:

```bash
python live_trading_loop_1.1.3.py
```

El bot iniciará el loop continuo, descargará datos en tiempo real desde Alpaca, generará señales según la estrategia configurada y enviará bracket orders automáticas cuando se detecte una entrada válida.

---

### Ejemplo de salida del backtesting

```
 Descargando datos de AAPL...

 Backtesting en AAPL...

 Resultados del Backtest - SMA (AAPL)
Capital final: $32,450.18
Retorno total: 224.50%
CAGR: 14.32%
Sharpe Ratio: 1.21
Sortino Ratio: 1.87
Calmar Ratio: 0.95
Profit Factor: 1.64
Win Rate: 54.30%
Max Drawdown: -18.45%
```

---

## Flujo del sistema

```
Datos históricos (yfinance)
        │
        ▼
Normalización OHLCV
        │
        ├──► Estrategias (SMA / RSI / MACD / Bollinger)
        │           │
        │           ▼
        │     Backtesting (métricas + curva de capital)
        │           │
        │     Optimización (grid search + heatmaps)
        │           │
        │     Robustez (sensibilidad de parámetros)
        │           │
        │     Walk-Forward (validación fuera de muestra)
        │           │
        │     Monte Carlo (VaR + Expected Shortfall)
        │           │
        │     Meta-estrategia (portafolio ponderado)
        │           │
        │           ▼
        │     Reporte PDF consolidado
        │
        └──► Loop en Vivo (Alpaca API)
                    │
             Datos en tiempo real
                    │
             Señal de entrada
                    │
             Position Sizing (ATR)
                    │
             Bracket Order (TP + SL)
                    │
             Registro en trades.log
```

---

## Autor

**David Santiago Figueroa Mendoza**

[![GitHub](https://img.shields.io/badge/GitHub-Shanti--F0132-181717?style=flat-square&logo=github)](https://github.com/Shanti-F0132)

---

<div align="center">

*Desarrollado con fines educativos y de investigación en trading cuantitativo.*

</div>