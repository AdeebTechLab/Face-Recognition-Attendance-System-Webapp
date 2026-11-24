"""Monthly Attendance Register data builder.

Builds the data behind the Monthly Attendance Register download (Excel and
PDF share this exact structure, so both files always agree).

Rules (all values come from real stored records — nothing is invented):
- A "class day" is a day in the month that has at least one stored
  attendance record (Present or Leave) for an active student.
- On a class day, each active student is:
    "P" — they have a check-in record that day,
    "L" — they have a Leave record that day (verification_source == "LEAVE"),
    "A" — they have no record that day.
- On any other day the cell is "—" (Holiday / No Class).
- Working Days = number of class days in the month.
- A student's percentage = P / (P + A) * 100 (Leave days are excluded,
  the standard register convention).
"""
import calendar
from datetime import date

from models import Student, AttendanceRecord

LEAVE_SOURCE = "LEAVE"


def is_leave(record) -> bool:
    """A Leave is stored as an attendance record whose verification_source
    is "LEAVE" (check_in_time "—", face_distance 0.0). The table's unique
    (roll_number, attendance_date) constraint guarantees a student can never
    be both Present and on Leave on the same day."""
    return record.verification_source == LEAVE_SOURCE


def _clean_pct(p: int, a: int):
    if (p + a) == 0:
        return 0
    value = round((p / (p + a)) * 100, 1)
    return int(value) if value == int(value) else value


def build_monthly_register(db, year: int, month: int) -> dict:
    days_in_month = calendar.monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, days_in_month)

    students = (
        db.query(Student)
        .filter(Student.is_active == True)
        .order_by(Student.roll_number.asc())
        .all()
    )
    active_rolls = {s.roll_number for s in students}

    records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.attendance_date >= first,
            AttendanceRecord.attendance_date <= last,
        )
        .all()
    )

    marks = {}  # (roll_number, day) -> "P" | "L"
    class_days = set()
    for r in records:
        if r.roll_number not in active_rolls:
            continue  # Deactivated students never distort the register
        marks[(r.roll_number, r.attendance_date.day)] = "L" if is_leave(r) else "P"
        class_days.add(r.attendance_date.day)

    rows = []
    total_p = total_a = total_l = 0
    for idx, s in enumerate(students, start=1):
        cells = []
        p = a = l = 0
        for d in range(1, days_in_month + 1):
            if d not in class_days:
                cells.append("—")
                continue
            mark = marks.get((s.roll_number, d))
            if mark == "P":
                cells.append("P")
                p += 1
            elif mark == "L":
                cells.append("L")
                l += 1
            else:
                cells.append("A")
                a += 1
        rows.append({
            "serial": idx,
            "name": s.name,
            "roll_number": s.roll_number,
            "cells": cells,
            "present": p,
            "absent": a,
            "leave": l,
            "percentage": _clean_pct(p, a),
        })
        total_p += p
        total_a += a
        total_l += l

    departments = {s.department for s in students}
    class_label = departments.pop() if len(departments) == 1 else "All Classes"
    # Academic session runs August -> July (e.g. Nov 2026 and Jan 2027 are both 2026-27)
    session = f"{year}-{str(year + 1)[2:]}" if month >= 8 else f"{year - 1}-{str(year)[2:]}"

    return {
        "class_label": class_label,
        "month_label": f"{calendar.month_name[month]} {year}",
        "session": session,
        "year": year,
        "month": month,
        "days_in_month": days_in_month,
        "summary": {
            "total_students": len(students),
            "working_days": len(class_days),
            "present": total_p,
            "absent": total_a,
            "leave": total_l,
            "overall_percentage": _clean_pct(total_p, total_a),
        },
        "rows": rows,
    }
