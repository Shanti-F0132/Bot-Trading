from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_report(output_path, all_results, charts=None, risk_summary=None):
    """
    Genera un reporte PDF consolidado con resultados de estrategias y métricas de riesgo.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=1,  # centrado
        spaceAfter=20,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#007ACC"),
        fontSize=14,
        spaceAfter=10,
    )

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # Título principal
    elements.append(Paragraph("📈 Reporte Consolidado de Estrategias de Trading", title_style))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Paragraph("Autor: David Santiago Figueroa Mendoza", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # Sección: resultados de estrategias
    elements.append(Paragraph("📊 Resultados por Estrategia", subtitle_style))

    data = [["Estrategia", "Final Equity", "CAGR", "Sharpe", "Max Drawdown"]]
    for res in all_results:
        data.append([
            res.get("Estrategia", ""),
            f"${res.get('final_equity', 0):,.2f}",
            f"{res.get('cagr', 0) * 100:.2f}%",
            f"{res.get('sharpe_ratio', 0):.2f}",
            f"{res.get('max_drawdown', 0) * 100:.2f}%"
        ])

    table = Table(data, hAlign="CENTER")
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#007ACC")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Sección: resumen de riesgo
    if risk_summary:
        elements.append(Paragraph("⚠️ Resumen de Análisis de Riesgo (Monte Carlo & VaR)", subtitle_style))
        risk_data = [
            ["Métrica", "Valor"],
            ["Media final", f"${risk_summary.get('mean_final', 0):,.2f}"],
            ["Mediana", f"${risk_summary.get('median', 0):,.2f}"],
            ["Probabilidad de ganancia", f"{risk_summary.get('prob>start', 0) * 100:.2f}%"],
            ["VaR 95%", f"${risk_summary.get('var', 0):,.2f}"],
            ["ES 95%", f"${risk_summary.get('es', 0):,.2f}"]
        ]
        risk_table = Table(risk_data, hAlign="CENTER")
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#CC6600")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
        ]))
        elements.append(risk_table)
        elements.append(Spacer(1, 20))

    # Sección: gráficos
    # ============================================================
    # 📊 SECCIÓN: GRÁFICOS Y ANÁLISIS DE ROBUSTEZ
    # ============================================================
    if charts:
        elements.append(Paragraph("📉 Visualizaciones de Resultados", subtitle_style))
        fig_counter = 1

        for chart in charts:
            try:
                # 🧩 Insertar la imagen
                elements.append(Image(chart, width=480, height=260))
                elements.append(Spacer(1, 6))

                # 🧠 Subtítulos automáticos según el tipo de gráfico
                subtitle = None
                if "robustness_sma" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia SMA: muestra cómo el Sharpe Ratio varía con las combinaciones de medias móviles."
                elif "robustness_macd" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia MACD: refleja cómo los parámetros rápidos y lentos afectan el rendimiento."
                elif "robustness_rsi" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia RSI: evidencia la estabilidad de la estrategia frente a distintos niveles de sobrecompra y sobreventa."
                elif "robustness_bollinger" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia Bollinger Bands: ilustra cómo la varianza cambia según el tamaño de ventana y la desviación estándar."

                # Subtítulo genérico para otros gráficos
                elif "heatmap" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Heatmap comparativo de desempeño entre parámetros o estrategias."

                elif "montecarlo" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Simulación Monte Carlo: distribución de resultados finales para evaluar el riesgo."

                # Agregar subtítulo si aplica
                if subtitle:
                    elements.append(Paragraph(subtitle, styles["Normal"]))
                    elements.append(Spacer(1, 10))
                    fig_counter += 1

            except Exception as e:
                elements.append(Paragraph(
                    f"⚠️ No se pudo cargar la imagen: {chart} ({e})",
                    styles["Normal"]
                ))
                

    # Cierre del reporte
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("📘 Fin del Reporte", styles["Italic"]))
    elements.append(Paragraph("Generado automáticamente por el Bot de Trading Cuantitativo. Bot01", styles["Normal"]))

    doc.build(elements)
