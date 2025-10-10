from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from reportlab.lib.enums import TA_CENTER
import os


def generate_report(output_path, all_results, charts=None, risk_summary=None):
    """
    Genera un reporte PDF consolidado con resultados de estrategias, métricas de riesgo
    y análisis de la Meta-Estrategia Adaptativa.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=1,
        spaceAfter=20,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#007ACC"),
        fontSize=14,
        spaceAfter=10,
    )
    subtext_style = ParagraphStyle(
        "SubtextStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER,
        leading=14,
        spaceAfter=8,
    )

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # ============================================================
    # 🧾 ENCABEZADO
    # ============================================================
    elements.append(Paragraph("📈 Reporte Consolidado de Estrategias de Trading", title_style))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Paragraph("Autor: David Santiago Figueroa Mendoza", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ============================================================
    # 📊 RESULTADOS POR ESTRATEGIA
    # ============================================================
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

    # ============================================================
    # ⚠️ ANÁLISIS DE RIESGO
    # ============================================================
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

    # ============================================================
    # 🧠 META-ESTRATEGIA ADAPTATIVA
    # ============================================================
    meta_chart = "outputs/charts/meta_vs_individuals.png"
    if os.path.exists(meta_chart):
        elements.append(Paragraph("🧠 Meta-Estrategia Adaptativa", subtitle_style))
        elements.append(Paragraph(
            "Compara el rendimiento de la Meta-Estrategia Adaptativa con las estrategias individuales. "
            "Los pesos se ajustan dinámicamente según Sharpe Ratio, CAGR y Drawdown promedio.",
            subtext_style
        ))
        elements.append(Image(meta_chart, width=480, height=300))
        elements.append(Spacer(1, 18))
    else:
        print("⚠️ No se encontró el gráfico meta_vs_individuals.png, omitiendo del reporte.")

    # ============================================================
    # 📉 VISUALIZACIONES DE RESULTADOS
    # ============================================================
    if charts:
        elements.append(Paragraph("📉 Visualizaciones de Resultados", subtitle_style))
        fig_counter = 1

        for chart in charts:
            try:
                elements.append(Image(chart, width=480, height=260))
                elements.append(Spacer(1, 6))
                subtitle = None
                if "robustness_sma" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia SMA."
                elif "robustness_macd" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia MACD."
                elif "robustness_rsi" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia RSI."
                elif "robustness_bollinger" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Análisis de robustez de la estrategia Bollinger Bands."
                elif "heatmap" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Heatmap comparativo de desempeño entre parámetros o estrategias."
                elif "montecarlo" in chart.lower():
                    subtitle = f"Figura {fig_counter}. Simulación Monte Carlo: distribución de resultados finales."

                if subtitle:
                    elements.append(Paragraph(subtitle, subtext_style))
                    elements.append(Spacer(1, 10))
                    fig_counter += 1

            except Exception as e:
                elements.append(Paragraph(f"⚠️ No se pudo cargar la imagen: {chart} ({e})", styles["Normal"]))

    # ============================================================
    # 📈 COMPARATIVA GLOBAL FINAL ENTRE ESTRATEGIAS
    # ============================================================
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np

        metrics_df = pd.DataFrame([
            {
                "Estrategia": r.get("Estrategia", ""),
                "CAGR (%)": r.get("cagr", 0) * 100,
                "Sharpe": r.get("sharpe_ratio", 0),
                "Drawdown (%)": abs(r.get("max_drawdown", 0)) * 100
            }
            for r in all_results
        ])

        if not metrics_df.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            x = np.arange(len(metrics_df["Estrategia"]))
            width = 0.25
            ax.bar(x - width, metrics_df["CAGR (%)"], width, label="CAGR (%)")
            ax.bar(x, metrics_df["Sharpe"], width, label="Sharpe Ratio")
            ax.bar(x + width, metrics_df["Drawdown (%)"], width, label="Max Drawdown (%)")
            ax.set_xticks(x)
            ax.set_xticklabels(metrics_df["Estrategia"], rotation=45, ha="right")
            ax.set_title("📊 Comparativa Global de Estrategias", fontsize=14, fontweight="bold")
            ax.legend()
            plt.tight_layout()

            comparison_chart = "outputs/charts/comparative_metrics.png"
            plt.savefig(comparison_chart)
            plt.close()

            # Insertar en el PDF
            elements.append(PageBreak())
            elements.append(Paragraph(" Comparativa Global de Estrategias", title_style))
            elements.append(Image(comparison_chart, width=500, height=250))
            elements.append(Paragraph(
                "Esta gráfica muestra la comparación de las métricas clave de rendimiento "
                "entre todas las estrategias evaluadas, incluyendo la Meta-Estrategia Adaptativa. "
                "Permite visualizar el equilibrio entre rentabilidad (CAGR), eficiencia (Sharpe Ratio) "
                "y riesgo (Drawdown).",
                subtext_style
            ))
            elements.append(Spacer(1, 20))

    except Exception as e:
        print(f"⚠️ Error generando la comparativa global: {e}")

    # ============================================================
    # 📘 CIERRE DEL REPORTE
    # ============================================================
    elements.append(Spacer(1, 25))
    elements.append(Paragraph("📘 Fin del Reporte", styles["Italic"]))
    elements.append(Paragraph("Generado automáticamente por el Bot de Trading Cuantitativo — Bot01", styles["Normal"]))

    doc.build(elements)
