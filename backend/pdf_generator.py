import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def build_attendance_pdf(target_date: str, summary: dict, records: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"AttendX Attendance Report — {target_date}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Total Active Students: {summary['total_students']} | "
        f"Present: {summary['present_count']} | "
        f"Absent: {summary['absent_count']} | "
        f"Attendance Rate: {summary['attendance_percentage']}%",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 16))

    table_data = [["Roll Number", "Student Name", "Department", "Status", "Check-In Time", "Face Distance"]]
    for r in records:
        table_data.append([
            r["roll_number"],
            r["student_name"],
            r["department"],
            r["status"],
            r["check_in_time"],
            str(r["face_distance"])
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()