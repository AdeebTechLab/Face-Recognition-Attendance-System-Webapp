"""Monthly Attendance Register data builder - MongoDB (PyMongo) version.

Rules unchanged from the SQL version:
- A "class day" is a day in the month that has at least one stored
  attendance record (Present or Leave) for an active student.
- On a class day, each active student is P / L / A as per their record.
- On any other day the cell is "—" (Holiday / No Class).
- A student's percentage = P / (P + A) * 100 (Leave excluded).

Only the data access changed: students / records are now plain dicts from
PyMongo, and attendance_date is stored as a "YYYY-MM-DD" string.
"""
import calendar
from datetime import date

from database import students_col, attendance_col

LEAVE_SOURCE = "LEAVE"


def is_leave(record) -> bool:
    """Works for both dict records (Mongo) and old attribute-style records."""
    if isinstance(record, dict):
        return record.get("verification_source") == LEAVE_SOURCE
    return getattr(record, "verification_source", None) == LEAVE_SOURCE


def _clean_pct(p: int, a: int):
    if (p + a) == 0:
        return 0
    value = round((p / (p + a)) * 100, 1)
    return int(value) if value == int(value) else value


def build_monthly_register(db, year: int, month: int) -> dict:
    # `db` is the PyMongo database, kept in the signature so main.py's
    # call site is unchanged from the SQL version.
    days_in_month = calendar.monthrange(year, month)[1]
    first = date(year, month, 1)
    last = date(year, month, days_in_month)

    students = list(
        students_col.find({"is_active": True}).sort("roll_number", 1)
    )
    active_rolls = {s["roll_number"] for s in students}

    # attendance_date is an ISO string, so a string range query is a date range.
    records = list(
        attendance_col.find(
            {"attendance_date": {"$gte": first.isoformat(), "$lte": last.isoformat()}}
        )
    )

    marks = {}  # (roll_number, day) -> "P" | "L"
    class_days = set()
    for r in records:
        if r["roll_number"] not in active_rolls:
            continue
        day = date.fromisoformat(r["attendance_date"]).day
        marks[(r["roll_number"], day)] = "L" if is_leave(r) else "P"
        class_days.add(day)

    rows = []
    total_p = total_a = total_l = 0
    for idx, s in enumerate(students, start=1):
        cells = []
        p = a = l = 0
        for d in range(1, days_in_month + 1):
            if d not in class_days:
                cells.append("—")
                continue
            mark = marks.get((s["roll_number"], d))
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
            "name": s["name"],
            "roll_number": s["roll_number"],
            "cells": cells,
            "present": p,
            "absent": a,
            "leave": l,
            "percentage": _clean_pct(p, a),
        })
        total_p += p
        total_a += a
        total_l += l

    departments = {s["department"] for s in students}
    class_label = departments.pop() if len(departments) == 1 else "All Classes"
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
