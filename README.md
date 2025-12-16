# Bot de Trading Cuantitativo – Proyecto de David Santiago Figueroa Mendoza 
### VERSION : 1.0

## Descripción General

Este proyecto implementa un **bot de trading cuantitativo modular**, diseñado para analizar el mercado financiero, ejecutar estrategias, optimizar parámetros y evaluar la robustez de los resultados.  
El sistema combina **técnicas de análisis técnico, backtesting, gestión de riesgo y validación estadística** para crear un entorno de trading realista y científicamente sólido.


## Funcionalidades Principales

### Descarga de Datos
- Fuente: **Yahoo Finance** (`yfinance`)
- Limpieza y normalización de columnas OHLCV

### Backtesting Avanzado
- Cálculo de métricas clave:
  - **CAGR (Compound Annual Growth Rate)**
  - **Sharpe Ratio**
  - **Max Drawdown**
  - **Total Return**
- Curva de capital simulada con **position sizing**, **slippage** y **comisiones**

### Estrategias Técnicas
- **SMA Crossover:** cruce de medias móviles
- **MACD:** convergencia/divergencia de medias
- **RSI:** fuerza relativa (sobrecompra/sobreventa)
- **Bollinger Bands:** rupturas de volatilidad

### Optimización de Parámetros
- Exploración de rangos personalizados
- Visualización con **heatmaps de Sharpe Ratio y CAGR**
- Comparación de estabilidad entre parámetros

### Robustez y Sensibilidad
- Análisis de **resiliencia de las estrategias** ante cambios en parámetros
- Comparativas de estabilidad entre estrategias
- Resultados integrados automáticamente en el reporte PDF

### Monte Carlo y Riesgo
- Simulación de escenarios aleatorios
- **VaR (Value at Risk)** y **ES (Expected Shortfall)**
- Distribución de rendimientos y caminos de capital

### Validación Walk-Forward
- Entrenamiento y prueba en ventanas temporales sucesivas
- Evaluación de desempeño fuera de muestra
- Resultados guardados en `outputs/walkforward_results/`

### Reporte PDF Profesional
- Generación automática de:
  - Gráficos y métricas
  - Heatmaps y robustez
  - Análisis de Monte Carlo y riesgo
- Subtítulos explicativos automáticos
- Exportación a `outputs/reports/reporte_final.pdf`

---

## Ejecución del Proyecto

### Requisitos previos
Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```

---

### Para ejecutar el programa
Desde la raiz del proyecto

```bash
python main.py
```

David Santiago Figueroa Mendoza
