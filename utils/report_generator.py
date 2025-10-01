from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def generate_report(results_dict, output_path="report.pdf", charts=[]):
    """
    Genera un reporte en PDF con métricas y gráficas.

    :param results_dict: Diccionario con métricas de estrategias
    :param output_path: Ruta de salida del PDF
    :param charts: Lista de rutas de imágenes de gráficas para incluir
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    normal_style = styles["Normal"]

    # Título
    elements.append(Paragraph("Reporte de Backtesting - Estrategias de Trading", title_style))
    elements.append(Spacer(1, 20))

    # Tabla de métricas
    data = [["Estrategia", "Capital Final", "CAGR", "Sharpe Ratio", "Max Drawdown", "Retorno Total"]]
    for strat, metrics in results_dict.items():
        data.append([
            strat,
            f"${metrics['final_equity']:.2f}",
            f"{metrics['cagr']:.2%}",
            f"{metrics['sharpe_ratio']:.2f}",
            f"{metrics['max_drawdown']:.2%}",
            f"{metrics['total_return_pct']:.2%}"
        ])

    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Insertar gráficas
    for chart_path in charts:
        elements.append(Image(chart_path, width=500, height=300))
        elements.append(Spacer(1, 15))

    doc.build(elements)
    print(f"✅ Reporte generado en {output_path}")
