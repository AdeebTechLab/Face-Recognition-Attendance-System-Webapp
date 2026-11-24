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
        f"Absent: {summary['absent_count']} | "
        f"Leave: {summary.get('leave_count', 0)}",
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


# ---------------------------------------------------------------------------
# Monthly Attendance Register (PDF) \u2014 landscape register with the same
# layout as the Excel register: title, summary strip, legend, one row per
# student with a cell per day (P / A / L / \u2014), and P / A / L / % totals.
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import A4, landscape

_REG = {
    "navy": colors.HexColor("#0F172A"),
    "grey": colors.HexColor("#64748B"),
    "grid": colors.HexColor("#CBD5E1"),
    "box": colors.HexColor("#E2E8F0"),
    "strip": colors.HexColor("#F8FAFC"),
    "legend": colors.HexColor("#F1F5F9"),
    "green": "#059669",
    "green_bg": colors.HexColor("#D1FAE5"),
    "red": "#DC2626",
    "red_bg": colors.HexColor("#FEE2E2"),
    "amber": "#D97706",
    "amber_bg": colors.HexColor("#FEF3C7"),
    "blue": "#1D4ED8",
    "dash": "#CBD5E1",
}


def _reg_pct_color(pct) -> str:
    if pct == 100:
        return _REG["green"]
    if pct == 0:
        return _REG["red"]
    return "#0F172A"


def build_monthly_register_pdf(data: dict) -> bytes:
    """Builds the Monthly Attendance Register PDF from the shared register
    data produced by monthly_register.build_monthly_register."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    usable = landscape(A4)[0] - 48
    styles = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    title_style = ps("reg_title", fontName="Helvetica-Bold", fontSize=16, leading=20,
                     textColor=_REG["navy"], alignment=1)
    subtitle_style = ps("reg_sub", fontSize=9.5, leading=13, textColor=_REG["grey"], alignment=1)
    footer_style = ps("reg_footer", fontSize=7.5, leading=10, textColor=_REG["grey"], alignment=1)

    elements = []
    elements.append(Paragraph("ATTENDX \u2022 MONTHLY ATTENDANCE REGISTER", title_style))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(
        f"Class: {data['class_label']} | Month: {data['month_label']} | Academic Session {data['session']}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 8))

    # Summary strip \u2014 6 boxes
    summary = data["summary"]
    boxes = [
        ("Total Students", summary["total_students"], "#0F172A"),
        ("Working Days", summary["working_days"], "#0F172A"),
        ("Present", summary["present"], _REG["green"]),
        ("Absent", summary["absent"], _REG["red"]),
        ("Leave", summary["leave"], _REG["amber"]),
        ("Overall %", f"{summary['overall_percentage']}%", _REG["blue"]),
    ]
    strip_cells = [
        Paragraph(
            f'<font color="#64748B" size="7.5">{label}</font><br/>'
            f'<font color="{color}" size="13"><b>{value}</b></font>',
            ps(f"strip_{i}", alignment=1, leading=17),
        )
        for i, (label, value, color) in enumerate(boxes)
    ]
    strip = Table([strip_cells], colWidths=[usable / 6.0] * 6)
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _REG["strip"]),
        ("BOX", (0, 0), (-1, -1), 0.5, _REG["box"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _REG["box"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(strip)
    elements.append(Spacer(1, 6))

    # Legend
    legend = Table(
        [[Paragraph(
            '<font color="#059669"><b>P</b></font> <font color="#334155">Present</font>'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '<font color="#DC2626"><b>A</b></font> <font color="#334155">Absent</font>'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '<font color="#D97706"><b>L</b></font> <font color="#334155">Leave</font>'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '<font color="#94A3B8">\u2014</font> <font color="#334155">Holiday / No Class</font>',
            ps("legend_p", alignment=1, fontSize=8.5, leading=11),
        )]],
        colWidths=[usable],
    )
    legend.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _REG["legend"]),
        ("BOX", (0, 0), (-1, -1), 0.5, _REG["box"]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(legend)
    elements.append(Spacer(1, 8))

    # Register grid
    days = data["days_in_month"]
    fixed = 16 + 104 + 84 + 20 + 20 + 20 + 30
    day_w = (usable - fixed) / days
    col_widths = [16, 104, 84] + [day_w] * days + [20, 20, 20, 30]

    header_style = ps("reg_h", fontName="Helvetica-Bold", fontSize=8, leading=10,
                      textColor=colors.white, alignment=1)
    serial_style = ps("reg_serial", fontSize=8, leading=10, alignment=1)
    name_style = ps("reg_name", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                    textColor=_REG["navy"])
    roll_style = ps("reg_roll", fontSize=6.5, leading=9, textColor=_REG["grey"], alignment=1)

    def day_para(mark):
        if mark == "\u2014":
            return Paragraph("\u2014", ps("d_dash", fontSize=8, leading=10,
                                          textColor=colors.HexColor(_REG["dash"]), alignment=1))
        color = {"P": _REG["green"], "A": _REG["red"], "L": _REG["amber"]}[mark]
        return Paragraph(f'<font color="{color}"><b>{mark}</b></font>',
                         ps(f"d_{mark}", fontSize=8, leading=10, alignment=1))

    def total_para(value, color):
        return Paragraph(f'<font color="{color}"><b>{value}</b></font>',
                         ps("tot", fontSize=8.5, leading=11, alignment=1))

    headers = ["#", "Student Name", "Roll No."] + [str(d) for d in range(1, days + 1)] + ["P", "A", "L", "%"]
    table_data = [[Paragraph(h, header_style) for h in headers]]
    mark_bg = {"P": _REG["green_bg"], "A": _REG["red_bg"], "L": _REG["amber_bg"]}
    bg_commands = []
    for row in data["rows"]:
        line = [
            Paragraph(str(row["serial"]), serial_style),
            Paragraph(str(row["name"]), name_style),
            Paragraph(str(row["roll_number"]), roll_style),
        ]
        for i, mark in enumerate(row["cells"]):
            line.append(day_para(mark))
            if mark in mark_bg:
                bg_commands.append(("BACKGROUND", (3 + i, len(table_data)), (3 + i, len(table_data)), mark_bg[mark]))
        line.append(total_para(row["present"], _REG["green"]))
        line.append(total_para(row["absent"], _REG["red"]))
        line.append(total_para(row["leave"], _REG["amber"]))
        line.append(total_para(f"{row['percentage']}%", _reg_pct_color(row["percentage"])))
        table_data.append(line)

    grid = Table(table_data, colWidths=col_widths, repeatRows=1)
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _REG["navy"]),
        ("GRID", (0, 0), (-1, -1), 0.4, _REG["grid"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _REG["strip"]]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ] + bg_commands))
    elements.append(grid)
    elements.append(Spacer(1, 12))

    # Signature block
    sig_label = ps("sig_l", fontName="Helvetica-Bold", fontSize=8, leading=10,
                   textColor=_REG["grey"], alignment=1)
    sig_line = ps("sig_v", fontSize=9, leading=12, textColor=_REG["grey"], alignment=1)
    sig = Table(
        [
            [Paragraph("Teacher / Coordinator Signature", sig_label),
             Paragraph("Date", sig_label),
             Paragraph("Remarks", sig_label)],
            [Paragraph("________________________", sig_line),
             Paragraph("____ / ____ / ________", sig_line),
             Paragraph("_______________________________", sig_line)],
        ],
        colWidths=[usable * 0.38, usable * 0.24, usable * 0.38],
    )
    sig.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _REG["strip"]),
        ("BOX", (0, 0), (-1, -1), 0.5, _REG["box"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _REG["box"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 16),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
    ]))
    elements.append(sig)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Generated by AttendX \u2022 {data['month_label']} \u2022 This is a system-generated monthly attendance register",
        footer_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
