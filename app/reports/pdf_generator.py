"""PDF report generation using ReportLab (native charts, no matplotlib)."""

import io
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.report_data import ReportContext, CurrencyReportData


APP_NAME = "Personal Finance"
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 1.5 * cm


def _create_pie_chart_drawing(data: dict[str, float], title: str) -> Drawing | None:
    """Create pie chart using ReportLab native charts (fast, no matplotlib)."""
    if not data:
        return None
    labels = list(data.keys())
    sizes = list(data.values())
    total = sum(sizes) or 1
    d = Drawing(300, 180)
    pc = Pie()
    pc.x = 100
    pc.y = 30
    pc.width = 150
    pc.height = 120
    pc.data = sizes
    pc.labels = [f"{l[:15]} {100*v/total:.0f}%" for l, v in zip(labels, sizes)]
    pc.slices.strokeWidth = 0.5
    pc.slices.popout = 2
    d.add(pc)
    d.add(String(150, 165, title, fontSize=10, textAnchor="middle"))
    return d


def _create_bar_chart_drawing(
    months: list[str],
    income: list[float],
    expense: list[float],
) -> Drawing | None:
    """Create bar chart using ReportLab native charts."""
    if not months:
        return None
    d = Drawing(400, 180)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 30
    bc.width = 300
    bc.height = 120
    bc.data = [income, expense]
    bc.categoryAxis.categoryNames = months
    bc.categoryAxis.labels.angle = 30
    bc.valueAxis.valueMin = 0
    bc.bars[0].fillColor = colors.HexColor("#2E7D32")
    bc.bars[1].fillColor = colors.HexColor("#C62828")
    bc.barSpacing = 2
    d.add(bc)
    d.add(String(200, 165, "Ingresos vs Gastos por Mes", fontSize=10, textAnchor="middle"))
    return d


def _build_header(styles: dict) -> list:
    """Build header with app name and logo (styled table as logo placeholder)."""
    elements = []
    logo_table = Table([[" PF "]], colWidths=[2 * cm], rowHeights=[0.8 * cm])
    logo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(logo_table)
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(f"<b>{APP_NAME}</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_meta(elements: list, ctx: ReportContext, styles: dict) -> None:
    """Add user, date range, generation date."""
    elements.append(Paragraph(f"<b>Usuario:</b> {ctx.user_name}", styles["Normal"]))
    elements.append(Paragraph(
        f"<b>Período:</b> {ctx.from_date.strftime('%d/%m/%Y')} - {ctx.to_date.strftime('%d/%m/%Y')}",
        styles["Normal"],
    ))
    elements.append(Paragraph(f"<b>Generado:</b> {ctx.generated_at}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))


def _build_account_summary(elements: list, data: CurrencyReportData, styles: dict) -> None:
    """Add account summary table for a currency."""
    elements.append(Paragraph(f"<b>Cuentas ({data.currency})</b>", styles["Heading2"]))
    if not data.accounts:
        elements.append(Paragraph("Sin cuentas en esta moneda.", styles["Normal"]))
    else:
        rows = [["Cuenta", "Tipo", f"Saldo ({data.currency})"]]
        for a in data.accounts:
            rows.append([a.name, a.type, f"{a.balance:,.2f}"])
        t = Table(rows, colWidths=[8 * cm, 4 * cm, 4 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#E7E6E6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 0.5 * cm))


def _build_transaction_table(
    elements: list,
    transactions: list,
    currency: str,
    styles: dict,
) -> None:
    """Add transaction detail table."""
    elements.append(Paragraph(f"<b>Detalle de transacciones ({currency})</b>", styles["Heading2"]))
    if not transactions:
        elements.append(Paragraph("Sin transacciones en este período.", styles["Normal"]))
    else:
        rows = [["Fecha", "Descripción", "Categoría", "Monto", "Cuenta"]]
        for tx in transactions:
            rows.append([
                tx.date.strftime("%d/%m/%Y"),
                (tx.description or "-")[:40],
                tx.category[:25],
                f"{tx.amount:,.2f}",
                tx.account_name[:20],
            ])
        t = Table(rows, colWidths=[2.5 * cm, 5 * cm, 3.5 * cm, 3 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 0.5 * cm))


def _add_footer(canvas: Any, doc: Any) -> None:
    """Add footer with generation date."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN, 1 * cm, f"Generado el {doc.generated_at} - {APP_NAME}")
    canvas.restoreState()


def generate_expense_report_pdf(ctx: ReportContext) -> bytes:
    """Generate expense report PDF (expenses by category, pie chart)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=2 * cm)
    doc.generated_at = ctx.generated_at
    styles = getSampleStyleSheet()
    elements = []

    elements.extend(_build_header(styles))
    elements.append(Paragraph("<b>Reporte de Gastos</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * cm))
    _build_meta(elements, ctx, styles)

    for curr, data in ctx.by_currency.items():
        _build_account_summary(elements, data, styles)

        expense_txs = [t for t in data.transactions if t.type == "expense"]
        expense_txs = sorted(expense_txs, key=lambda t: (t.category, t.date))
        _build_transaction_table(elements, expense_txs, curr, styles)

        # Category subtotals
        if data.by_category:
            elements.append(Paragraph(f"<b>Subtotales por categoría ({curr})</b>", styles["Heading2"]))
            rows = [["Categoría", f"Total ({curr})"]]
            for cat, total in sorted(data.by_category.items(), key=lambda x: -x[1]):
                rows.append([cat, f"{total:,.2f}"])
            rows.append(["<b>TOTAL GASTOS</b>", f"<b>{data.total_expenses:,.2f}</b>"])
            t = Table(rows, colWidths=[10 * cm, 4 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F2F2")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#D9E1F2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.5 * cm))

        # Pie chart (ReportLab native - fast)
        if data.by_category:
            chart = _create_pie_chart_drawing(
                data.by_category,
                f"Distribución de gastos ({curr})",
            )
            if chart:
                elements.append(chart)
        elements.append(Spacer(1, 0.8 * cm))

    doc.build(elements, onFirstPage=lambda c, d: _add_footer(c, doc),
              onLaterPages=lambda c, d: _add_footer(c, doc))
    return buf.getvalue()


def generate_income_expense_report_pdf(ctx: ReportContext) -> bytes:
    """Generate income/expense report PDF (flow, savings ratio, bar chart)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=2 * cm)
    doc.generated_at = ctx.generated_at
    styles = getSampleStyleSheet()
    elements = []

    elements.extend(_build_header(styles))
    elements.append(Paragraph("<b>Reporte de Ingresos y Egresos</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * cm))
    _build_meta(elements, ctx, styles)

    if ctx.savings_ratio is not None:
        elements.append(Paragraph(
            f"<b>Ratio de ahorro:</b> {ctx.savings_ratio * 100:.2f}%",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.3 * cm))

    for curr, data in ctx.by_currency.items():
        _build_account_summary(elements, data, styles)

        income_txs = [t for t in data.transactions if t.type == "income"]
        expense_txs = [t for t in data.transactions if t.type == "expense"]

        elements.append(Paragraph(f"<b>Ingresos ({curr})</b>", styles["Heading2"]))
        _build_transaction_table(elements, income_txs, curr, styles)

        elements.append(Paragraph(f"<b>Egresos ({curr})</b>", styles["Heading2"]))
        _build_transaction_table(elements, expense_txs, curr, styles)

        net = data.total_income - data.total_expenses
        elements.append(Paragraph(
            f"<b>Balance neto ({curr}):</b> {net:,.2f}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.5 * cm))

    if ctx.monthly_flow:
        months = [f"{m['month']:02d}/{m['year']}" for m in ctx.monthly_flow]
        income = [m["income"] for m in ctx.monthly_flow]
        expense = [m["expense"] for m in ctx.monthly_flow]
        chart = _create_bar_chart_drawing(months, income, expense)
        if chart:
            elements.append(chart)

    doc.build(elements, onFirstPage=lambda c, d: _add_footer(c, doc),
              onLaterPages=lambda c, d: _add_footer(c, doc))
    return buf.getvalue()


