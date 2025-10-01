from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

def generate_report(output_path, all_results, charts=[]):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    elements.append(Paragraph("■ Reporte de Estrategias de Trading", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    # Construir la tabla de resultados
    data = [["Estrategia", "Final Equity", "CAGR", "Sharpe Ratio", "Max Drawdown"]]
    for res in all_results:
        data.append([
            res.get("Estrategia", ""),
            f"{res.get('final_equity', 0):.2f}",
            f"{res.get('cagr', 0)*100:.2f}%",
            f"{res.get('sharpe_ratio', 0):.2f}",
            f"{res.get('max_drawdown', 0)*100:.2f}%",
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Ranking de estrategias
    sharpe_sorted = sorted(all_results, key=lambda x: x.get("sharpe_ratio", 0), reverse=True)
    cagr_sorted = sorted(all_results, key=lambda x: x.get("cagr", 0), reverse=True)
    drawdown_sorted = sorted(all_results, key=lambda x: x.get("max_drawdown", 0), reverse=False)

    ranking_text = (
        f"■ Ranking de Estrategias: "
        f"- Mejor por Sharpe Ratio: {sharpe_sorted[0]['Estrategia']} ({sharpe_sorted[0]['sharpe_ratio']:.2f}) "
        f"- Mejor por CAGR: {cagr_sorted[0]['Estrategia']} ({cagr_sorted[0]['cagr']*100:.2f}%) "
        f"- Menor Drawdown: {drawdown_sorted[0]['Estrategia']} ({drawdown_sorted[0]['max_drawdown']*100:.2f}%)"
    )
    elements.append(Paragraph(ranking_text, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Gráficas exportadas
    if charts:
        elements.append(Paragraph("■ Gráficas de Resultados", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        for chart in charts:
            try:
                elements.append(Image(chart, width=500, height=300))
                elements.append(Spacer(1, 12))
            except Exception as e:
                elements.append(Paragraph(f"No se pudo insertar {chart}: {e}", styles["Normal"]))

    # Guardar PDF
    doc.build(elements)
    print(f"✅ Reporte exportado en {output_path}")
