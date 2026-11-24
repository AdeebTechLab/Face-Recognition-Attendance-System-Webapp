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
