import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Required Attendance History download columns, in this exact order.
EXPORT_COLUMNS = ["Serial Number", "Name", "Roll Number", "Date", "Present", "Absent", "Leave"]
COLUMN_WIDTHS = [14, 32, 16, 14, 12, 12, 12]


def build_attendance_excel(rows: list) -> bytes:
    """Builds a clean, professionally formatted .xlsx from export rows.

    Each row is a dict with keys: serial, name, roll_number, date,
    present, absent, leave (values come from real stored attendance data).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    ws.append(EXPORT_COLUMNS)
    for col_idx in range(1, len(EXPORT_COLUMNS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border

    for row in rows:
        ws.append([
            row["serial"],
            row["name"],
            row["roll_number"],
            row["date"],
            row["present"],
            row["absent"],
            row["leave"],
        ])
        r = ws.max_row
        for col_idx in range(1, len(EXPORT_COLUMNS) + 1):
            cell = ws.cell(row=r, column=col_idx)
            cell.border = border
            if col_idx in (1, 4, 5, 6, 7):
                cell.alignment = Alignment(horizontal="center")
            if r % 2 == 0:
                cell.fill = alt_fill

    for i, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    ws.freeze_panes = "A2"
    if rows:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(EXPORT_COLUMNS))}{ws.max_row}"

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Monthly Attendance Register (.xlsx) — the same layout as the PDF register:
# title, summary strip, legend, one row per student with a cell per day
# (P / A / L / \u2014), and P / A / L / % totals per student.
# ---------------------------------------------------------------------------

_REG_NAVY = "0F172A"
_REG_SLATE_FILL = "F1F5F9"
_REG_ALT_FILL = "F8FAFC"
_REG_GREEN = "059669"
_REG_GREEN_BG = "D1FAE5"
_REG_RED = "DC2626"
_REG_RED_BG = "FEE2E2"
_REG_AMBER = "D97706"
_REG_AMBER_BG = "FEF3C7"
_REG_BLUE = "1D4ED8"
_REG_GREY_TEXT = "64748B"
_REG_DASH_TEXT = "CBD5E1"


def _reg_pct_color(pct) -> str:
    if pct == 100:
        return _REG_GREEN
    if pct == 0:
        return _REG_RED
    return _REG_NAVY


def build_monthly_register_excel(data: dict) -> bytes:
    """Builds the Monthly Attendance Register .xlsx from the shared register
    data produced by monthly_register.build_monthly_register."""
    days = data["days_in_month"]
    summary = data["summary"]
    total_cols = 3 + days + 4  # #, Name, Roll + day cells + P, A, L, %

    wb = Workbook()
    ws = wb.active
    ws.title = "Monthly Register"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center")

    # Title + subtitle
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    c = ws.cell(row=1, column=1, value="ATTENDX \u2022 MONTHLY ATTENDANCE REGISTER")
    c.font = Font(name="Calibri", size=16, bold=True, color=_REG_NAVY)
    c.alignment = center
    ws.row_dimensions[1].height = 26

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    c = ws.cell(
        row=2, column=1,
        value=f"Class: {data['class_label']} | Month: {data['month_label']} | Academic Session {data['session']}",
    )
    c.font = Font(name="Calibri", size=11, color=_REG_GREY_TEXT)
    c.alignment = center

    # Summary strip: 6 boxes (label row + value row), spread across all columns
    boxes = [
        ("Total Students", summary["total_students"], _REG_NAVY),
        ("Working Days", summary["working_days"], _REG_NAVY),
        ("Present", summary["present"], _REG_GREEN),
        ("Absent", summary["absent"], _REG_RED),
        ("Leave", summary["leave"], _REG_AMBER),
        ("Overall %", f"{summary['overall_percentage']}%", _REG_BLUE),
    ]
    group = total_cols // 6
    spans = []
    start = 1
    for i in range(6):
        end = total_cols if i == 5 else start + group - 1
        spans.append((start, end))
        start = end + 1
    fill = PatternFill(start_color=_REG_SLATE_FILL, end_color=_REG_SLATE_FILL, fill_type="solid")
    for (label, value, color), (sc, ec) in zip(boxes, spans):
        ws.merge_cells(start_row=4, start_column=sc, end_row=4, end_column=ec)
        lc = ws.cell(row=4, column=sc, value=label)
        lc.font = Font(name="Calibri", size=10, bold=True, color=_REG_GREY_TEXT)
        lc.alignment = center
        ws.merge_cells(start_row=5, start_column=sc, end_row=5, end_column=ec)
        vc = ws.cell(row=5, column=sc, value=value)
        vc.font = Font(name="Calibri", size=14, bold=True, color=color)
        vc.alignment = center
        for r in (4, 5):
            for col in range(sc, ec + 1):
                cell = ws.cell(row=r, column=col)
                cell.fill = fill
                cell.border = border
    ws.row_dimensions[5].height = 22

    # Legend
    ws.merge_cells(start_row=7, start_column=1, end_row=7, end_column=total_cols)
    c = ws.cell(row=7, column=1, value="P  Present          A  Absent          L  Leave          \u2014  Holiday / No Class")
    c.font = Font(name="Calibri", size=10, color="334155")
    c.alignment = center
    for col in range(1, total_cols + 1):
        ws.cell(row=7, column=col).fill = fill

    # Grid header
    header_row = 9
    headers = ["#", "Student Name", "Roll No."] + [str(d) for d in range(1, days + 1)] + ["P", "A", "L", "%"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color=_REG_NAVY, end_color=_REG_NAVY, fill_type="solid")
        cell.alignment = center
        cell.border = border

    # Student rows
    mark_styles = {
        "P": (_REG_GREEN, _REG_GREEN_BG),
        "A": (_REG_RED, _REG_RED_BG),
        "L": (_REG_AMBER, _REG_AMBER_BG),
    }
    r = header_row
    for row in data["rows"]:
        r += 1
        alt = PatternFill(start_color=_REG_ALT_FILL, end_color=_REG_ALT_FILL, fill_type="solid") if r % 2 == 0 else None

        cell = ws.cell(row=r, column=1, value=row["serial"])
        cell.alignment = center
        cell.border = border
        if alt:
            cell.fill = alt

        cell = ws.cell(row=r, column=2, value=row["name"])
        cell.font = Font(name="Calibri", size=10, bold=True, color=_REG_NAVY)
        cell.border = border
        if alt:
            cell.fill = alt

        cell = ws.cell(row=r, column=3, value=row["roll_number"])
        cell.font = Font(name="Calibri", size=10, color=_REG_GREY_TEXT)
        cell.alignment = center
        cell.border = border
        if alt:
            cell.fill = alt

        for i, mark in enumerate(row["cells"]):
            cell = ws.cell(row=r, column=4 + i, value=mark)
            cell.alignment = center
            cell.border = border
            if mark in mark_styles:
                color, bg = mark_styles[mark]
                cell.font = Font(name="Calibri", size=10, bold=True, color=color)
                cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            else:  # \u2014 Holiday / No Class
                cell.font = Font(name="Calibri", size=10, color=_REG_DASH_TEXT)
                if alt:
                    cell.fill = alt

        totals = [
            (row["present"], _REG_GREEN),
            (row["absent"], _REG_RED),
            (row["leave"], _REG_AMBER),
            (f"{row['percentage']}%", _reg_pct_color(row["percentage"])),
        ]
        for j, (value, color) in enumerate(totals):
            cell = ws.cell(row=r, column=4 + days + j, value=value)
            cell.font = Font(name="Calibri", size=10, bold=True, color=color)
            cell.alignment = center
            cell.border = border
            if alt:
                cell.fill = alt

    # Signature block
    r += 2
    sig_groups = [(1, max(3, total_cols * 3 // 8)), (max(4, total_cols * 3 // 8 + 1), max(5, total_cols * 5 // 8)),
                  (max(6, total_cols * 5 // 8 + 1), total_cols)]
    sig_labels = ["Teacher / Coordinator Signature", "Date", "Remarks"]
    sig_lines = ["________________________", "____ / ____ / ________", "_______________________________"]
    for (sc, ec), label, line in zip(sig_groups, sig_labels, sig_lines):
        ws.merge_cells(start_row=r, start_column=sc, end_row=r, end_column=ec)
        lc = ws.cell(row=r, column=sc, value=label)
        lc.font = Font(name="Calibri", size=10, bold=True, color=_REG_GREY_TEXT)
        lc.alignment = center
        ws.merge_cells(start_row=r + 1, start_column=sc, end_row=r + 1, end_column=ec)
        vc = ws.cell(row=r + 1, column=sc, value=line)
        vc.font = Font(name="Calibri", size=11, color=_REG_GREY_TEXT)
        vc.alignment = Alignment(horizontal="center", vertical="bottom")
        for rr in (r, r + 1):
            for col in range(sc, ec + 1):
                cell = ws.cell(row=rr, column=col)
                cell.fill = fill
                cell.border = border
    ws.row_dimensions[r + 1].height = 30

    # Footer
    r += 3
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=total_cols)
    c = ws.cell(row=r, column=1,
                value=f"Generated by AttendX \u2022 {data['month_label']} \u2022 This is a system-generated monthly attendance register")
    c.font = Font(name="Calibri", size=9, color=_REG_GREY_TEXT)
    c.alignment = center

    # Column widths
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 17
    for i in range(days):
        ws.column_dimensions[get_column_letter(4 + i)].width = 3.4
    for j in range(3):
        ws.column_dimensions[get_column_letter(4 + days + j)].width = 4.5
    ws.column_dimensions[get_column_letter(4 + days + 3)].width = 6.5

    ws.freeze_panes = ws.cell(row=header_row + 1, column=4).coordinate
    ws.print_title_rows = f"{header_row}:{header_row}"

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()
