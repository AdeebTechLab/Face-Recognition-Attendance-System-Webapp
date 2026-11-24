import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Column widths for: Serial Number, Name, Roll Number, Date, Present, Absent, Leave
# Sized to fit the usable width of a letter page so nothing is clipped.
COLUMN_WIDTHS = [1.05 * inch, 1.90 * inch, 0.95 * inch, 0.95 * inch, 0.8 * inch, 0.8 * inch, 0.65 * inch]


def build_attendance_pdf(target_date: str, summary: dict, records: list) -> bytes:
    """Builds the Attendance History PDF download.

    `records` are export rows: dicts with keys serial, name, roll_number,
    date, present, absent, leave — the same logical structure as the Excel
    download. Platypus splits long tables across pages and repeats the
    header row, so large datasets are handled without overlap or clipping.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=9, leading=12)
    header_style = ParagraphStyle(
        "header_cell", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=colors.white, fontName="Helvetica-Bold",
    )
    elements = []

    elements.append(Paragraph(f"AttendX Attendance Report — {target_date}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Total Records: {summary['total_records']} | "
        f"Present: {summary['present_count']} | "
        f"Absent: {summary['absent_count']}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 16))

    headers = ["Serial Number", "Name", "Roll Number", "Date", "Present", "Absent", "Leave"]
    table_data = [[Paragraph(h, header_style) for h in headers]]
    for r in records:
        table_data.append([
            Paragraph(str(r["serial"]), cell_style),
            Paragraph(str(r["name"]), cell_style),
            Paragraph(str(r["roll_number"]), cell_style),
            Paragraph(str(r["date"]), cell_style),
            Paragraph(str(r["present"]), cell_style),
            Paragraph(str(r["absent"]), cell_style),
            Paragraph(str(r["leave"]), cell_style),
        ])

    table = Table(table_data, colWidths=COLUMN_WIDTHS, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
