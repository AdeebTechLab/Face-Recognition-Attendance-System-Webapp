"""
AttendX API - MongoDB (PyMongo) version.

Same routes, same request/response shapes as the SQLAlchemy version.
Only the data layer changed:
  db.query(Model)...          ->  collection.find / find_one
  db.add() + db.commit()      ->  collection.insert_one / update_one
  sqlalchemy IntegrityError   ->  pymongo DuplicateKeyError
  .ilike("%term%")            ->  {"$regex": term, "$options": "i"}
  attendance_date (SQL Date)  ->  stored as "YYYY-MM-DD" string
"""
import os
import csv
import io
import re
from datetime import datetime, date, timedelta
from types import SimpleNamespace
from typing import Optional, Literal

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pymongo import DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError

from database import get_db, students_col, attendance_col, model_versions_col, system_logs_col
from models import (
    to_object_id,
    serialize_student,
    serialize_attendance,
    serialize_model_version,
    serialize_log,
)
from schemas import StudentCreate, StudentUpdate, FrameCaptureRequest, TrainRequest, RecognizeRequest, LeaveRequest
from security import get_api_key
from vision_engine import validate_and_save_capture, train_encodings_model, recognize_faces_in_frame, DATASET_DIR
from pdf_generator import build_attendance_pdf, build_monthly_register_pdf
from excel_generator import build_attendance_excel, build_monthly_register_excel
from monthly_register import build_monthly_register, is_leave, LEAVE_SOURCE

app = FastAPI(
    title="AttendX API - AI-Powered Smart Attendance Platform",
    version="1.0.0",
    description="Enterprise Python OpenCV + dlib Recognition Engine",
)

allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="target_date must be YYYY-MM-DD.")


def log_event(db, level: str, module: str, message: str):
    # `db` is the PyMongo database (kept as a parameter so call sites are unchanged)
    system_logs_col.insert_one(
        {"level": level, "module": module, "message": message, "created_at": datetime.utcnow()}
    )


def _find_student_by_id(student_id: str):
    oid = to_object_id(student_id)
    if oid is None:
        return None
    return students_col.find_one({"_id": oid})


def _regex(term: str) -> dict:
    return {"$regex": re.escape(term), "$options": "i"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# --- 1. STUDENT CRUD ENDPOINTS ---
@app.post("/api/students", dependencies=[Depends(get_api_key)])
def create_student(payload: StudentCreate, db=Depends(get_db)):
    existing = students_col.find_one(
        {"$or": [{"roll_number": payload.roll_number}, {"email": payload.email}]}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Student with this roll number or email already exists.")

    doc = {
        **payload.model_dump(),
        "is_active": True,
        "photo_count": 0,
        "created_at": datetime.utcnow(),
    }
    try:
        result = students_col.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Student with this roll number or email already exists.")
    doc["_id"] = result.inserted_id
    log_event(db, "INFO", "STUDENTS", f"Registered student {doc['roll_number']} ({doc['name']})")
    return serialize_student(doc)


@app.get("/api/students", dependencies=[Depends(get_api_key)])
def list_students(include_inactive: bool = False, db=Depends(get_db)):
    query = {} if include_inactive else {"is_active": True}
    docs = students_col.find(query).sort("roll_number", ASCENDING)
    return [serialize_student(d) for d in docs]


@app.get("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def get_student(student_id: str, db=Depends(get_db)):
    student = _find_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return serialize_student(student)


@app.put("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def update_student(student_id: str, payload: StudentUpdate, db=Depends(get_db)):
    student = _find_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        try:
            students_col.update_one({"_id": student["_id"]}, {"$set": updates})
        except DuplicateKeyError:
            raise HTTPException(status_code=400, detail="Student with this roll number or email already exists.")
        student.update(updates)
    log_event(db, "INFO", "STUDENTS", f"Updated profile for {student['roll_number']}")
    return serialize_student(student)


@app.delete("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def deactivate_student(student_id: str, db=Depends(get_db)):
    student = _find_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    # Soft delete preserves historical attendance logs
    students_col.update_one({"_id": student["_id"]}, {"$set": {"is_active": False}})
    log_event(db, "WARNING", "STUDENTS", f"Deactivated student {student['roll_number']}; historical records preserved.")
    return {"message": f"Student {student['roll_number']} deactivated. Historical attendance preserved."}


# --- 2. DATASET CAPTURE & GALLERY ---
@app.post("/api/dataset/capture", dependencies=[Depends(get_api_key)])
def capture_dataset_frame(payload: FrameCaptureRequest, db=Depends(get_db)):
    student = students_col.find_one({"roll_number": payload.roll_number})
    if not student:
        raise HTTPException(status_code=404, detail="Student roll number not registered.")
    try:
        res = validate_and_save_capture(payload.roll_number, payload.image_base64)
        if res["saved"]:
            students_col.update_one(
                {"_id": student["_id"]}, {"$set": {"photo_count": res["photo_count"]}}
            )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/dataset/summary", dependencies=[Depends(get_api_key)])
def dataset_summary(db=Depends(get_db)):
    students = list(students_col.find({"is_active": True}))
    data = []
    for s in students:
        safe_roll = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s["roll_number"])
        folder = os.path.join(DATASET_DIR, safe_roll)
        files = sorted(os.listdir(folder)) if os.path.exists(folder) else []
        data.append({
            "id": str(s["_id"]),
            "roll_number": s["roll_number"],
            "name": s["name"],
            "department": s["department"],
            "photo_count": len(files),
            "ready_for_training": len(files) >= 10,
        })
    return data


# --- 3. MODEL TRAINING & STATUS ---
@app.post("/api/model/train", dependencies=[Depends(get_api_key)])
def trigger_training(payload: TrainRequest, db=Depends(get_db)):
    active_students = list(students_col.find({"is_active": True}))
    try:
        # vision_engine reads student.roll_number / .name / .department as
        # attributes, so hand it simple objects built from the documents.
        student_objs = [SimpleNamespace(**{k: v for k, v in s.items() if k != "_id"}) for s in active_students]
        metrics = train_encodings_model(student_objs, tolerance=payload.tolerance)
        model_versions_col.update_many({}, {"$set": {"is_active": False}})
        doc = {**metrics, "is_active": True, "trained_at": datetime.utcnow()}
        result = model_versions_col.insert_one(doc)
        doc["_id"] = result.inserted_id
        log_event(db, "INFO", "TRAINING", f"Trained {doc['version_tag']} | Accuracy: {doc['validation_accuracy']}%")
        return serialize_model_version(doc)
    except ValueError as e:
        log_event(db, "ERROR", "TRAINING", str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/model/status", dependencies=[Depends(get_api_key)])
def get_model_status(db=Depends(get_db)):
    active_model = model_versions_col.find_one({"is_active": True})
    versions = model_versions_col.find().sort("trained_at", DESCENDING).limit(10)
    return {
        "active_model": serialize_model_version(active_model) if active_model else None,
        "history": [serialize_model_version(v) for v in versions],
    }


# --- 4. LIVE RECOGNITION & ATTENDANCE ---
@app.post("/api/recognition/recognize", dependencies=[Depends(get_api_key)])
def recognize_frame(payload: RecognizeRequest, db=Depends(get_db)):
    try:
        detections = recognize_faces_in_frame(payload.image_base64, tolerance=payload.tolerance)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    today = date.today().isoformat()
    now_str = datetime.now().strftime("%H:%M:%S")

    for det in detections:
        if det["status"] == "KNOWN" and payload.auto_mark:
            student = students_col.find_one(
                {"roll_number": det["roll_number"], "is_active": True}
            )
            if not student:
                det["status"] = "UNKNOWN"
                det["name"] = "Unknown"
                det["attendance_event"] = None
                continue

            record = {
                "roll_number": student["roll_number"],
                "student_name": student["name"],
                "department": student["department"],
                "attendance_date": today,
                "check_in_time": now_str,
                "face_distance": det["distance"],
                "verification_source": "LIVE_WEBCAM",
                "created_at": datetime.utcnow(),
            }
            try:
                # The unique (roll_number, attendance_date) index is the
                # duplicate protection - same role IntegrityError played before.
                attendance_col.insert_one(record)
                det["attendance_event"] = "MARKED_NEW"
                det["message"] = f"Attendance marked: {student['name']} ({student['roll_number']}) at {now_str}"
                log_event(db, "INFO", "ATTENDANCE", det["message"])
            except DuplicateKeyError:
                existing = attendance_col.find_one(
                    {"roll_number": student["roll_number"], "attendance_date": today}
                )
                if existing and is_leave(existing):
                    det["attendance_event"] = "ON_LEAVE"
                    det["message"] = f"On leave today: {student['name']} ({student['roll_number']})"
                else:
                    det["attendance_event"] = "ALREADY_MARKED"
                    det["message"] = f"Already marked today: {student['name']} ({student['roll_number']})"
        else:
            det["attendance_event"] = "IGNORED_UNKNOWN"

    return {"detections": detections}


@app.post("/api/attendance/mark", dependencies=[Depends(get_api_key)])
def mark_verified_attendance(roll_number: str, face_distance: float, db=Depends(get_db)):
    """Explicit endpoint restricted to verified live webcam matches."""
    student = students_col.find_one({"roll_number": roll_number, "is_active": True})
    if not student:
        raise HTTPException(status_code=404, detail="Active student not found.")
    today = date.today().isoformat()
    now_str = datetime.now().strftime("%H:%M:%S")
    record = {
        "roll_number": student["roll_number"],
        "student_name": student["name"],
        "department": student["department"],
        "attendance_date": today,
        "check_in_time": now_str,
        "face_distance": face_distance,
        "verification_source": "LIVE_WEBCAM",
        "created_at": datetime.utcnow(),
    }
    try:
        attendance_col.insert_one(record)
        return {"status": "MARKED", "roll_number": student["roll_number"], "time": now_str}
    except DuplicateKeyError:
        return {"status": "DUPLICATE_PREVENTED", "roll_number": student["roll_number"]}


@app.get("/api/attendance", dependencies=[Depends(get_api_key)])
def get_attendance_history(
    target_date: Optional[str] = None,
    roll_number: Optional[str] = None,
    search: Optional[str] = None,
    db=Depends(get_db),
):
    query = {}
    if target_date:
        query["attendance_date"] = _parse_date(target_date).isoformat()
    if roll_number:
        query["roll_number"] = roll_number
    if search:
        query["$or"] = [
            {"student_name": _regex(search)},
            {"roll_number": _regex(search)},
        ]
    docs = attendance_col.find(query).sort(
        [("attendance_date", DESCENDING), ("check_in_time", DESCENDING)]
    )
    return [serialize_attendance(d) for d in docs]


@app.get("/api/attendance/daily-report", dependencies=[Depends(get_api_key)])
def get_daily_report(target_date: Optional[str] = None, db=Depends(get_db)):
    report_date = _parse_date(target_date) if target_date else date.today()
    active_students = list(students_col.find({"is_active": True}).sort("roll_number", ASCENDING))
    active_rolls = {s["roll_number"] for s in active_students}
    # Only active students count: deactivated students' history must not inflate today's totals
    day_records = [
        r for r in attendance_col.find({"attendance_date": report_date.isoformat()})
        if r["roll_number"] in active_rolls
    ]
    record_map = {r["roll_number"]: r for r in day_records}
    present_records = [r for r in day_records if not is_leave(r)]
    leave_records = [r for r in day_records if is_leave(r)]

    roster = []
    for s in active_students:
        rec = record_map.get(s["roll_number"])
        if rec and is_leave(rec):
            status = "Leave"
        elif rec:
            status = "Present"
        else:
            status = "Absent"
        roster.append({
            "roll_number": s["roll_number"],
            "student_name": s["name"],
            "department": s["department"],
            "status": status,
            "check_in_time": rec["check_in_time"] if rec and not is_leave(rec) else "—",
            "face_distance": rec["face_distance"] if rec and not is_leave(rec) else "—",
        })

    total = len(active_students)
    present_count = len(present_records)
    leave_count = len(leave_records)
    absent_count = max(0, total - present_count - leave_count)
    pct = round((present_count / total) * 100.0, 1) if total > 0 else 0.0

    # Weekly trend (last 7 days)
    trend = []
    for offset in range(6, -1, -1):
        d = report_date - timedelta(days=offset)
        if active_rolls:
            day_recs = list(attendance_col.find(
                {"attendance_date": d.isoformat(), "roll_number": {"$in": list(active_rolls)}}
            ))
        else:
            day_recs = []
        cnt = sum(1 for r in day_recs if not is_leave(r))
        leave_cnt = sum(1 for r in day_recs if is_leave(r))
        trend.append({
            "date": d.strftime("%b %d"),
            "present": cnt,
            "leave": leave_cnt,
            "absent": max(0, total - cnt - leave_cnt),
            "rate": round((cnt / total) * 100.0, 1) if total > 0 else 0.0,
        })

    return {
        "date": report_date.isoformat(),
        "total_students": total,
        "present_count": present_count,
        "leave_count": leave_count,
        "absent_count": absent_count,
        "attendance_percentage": pct,
        "roster": roster,
        "weekly_trend": trend,
    }


def _build_export_rows(db, target_date: Optional[str] = None, search: Optional[str] = None):
    """Rows for the Attendance History download, built only from real stored data.
    Columns: Serial Number, Name, Roll Number, Date, Present, Absent, Leave.
    (Logic unchanged from the SQL version - see the original docstring.)"""
    students_query = {"is_active": True}
    if search:
        students_query["$or"] = [
            {"name": _regex(search)},
            {"roll_number": _regex(search)},
        ]
    students = list(students_col.find(students_query).sort("roll_number", ASCENDING))

    if target_date:
        dates = [_parse_date(target_date)]
    else:
        dates = sorted(
            {date.fromisoformat(d) for d in attendance_col.distinct("attendance_date") if d}
        )
        if not dates:
            dates = [date.today()]

    rows = []
    serial = 1
    for d in dates:
        day_records = {
            r["roll_number"]: r
            for r in attendance_col.find({"attendance_date": d.isoformat()})
        }
        for s in students:
            rec = day_records.get(s["roll_number"])
            on_leave = bool(rec) and is_leave(rec)
            is_present = bool(rec) and not on_leave
            rows.append({
                "serial": serial,
                "name": s["name"],
                "roll_number": s["roll_number"],
                "date": d.isoformat(),
                "present": "Present" if is_present else "",
                "absent": "Absent" if (not is_present and not on_leave) else "",
                "leave": "Leave" if on_leave else "",
            })
            serial += 1
    return rows


@app.get("/api/attendance/export", dependencies=[Depends(get_api_key)])
def export_attendance(
    target_date: Optional[str] = None,
    search: Optional[str] = None,
    format: Literal["xlsx", "pdf", "csv"] = Query("xlsx"),
    db=Depends(get_db),
):
    """Attendance History download (Excel / PDF / CSV). Columns:
    Serial Number, Name, Roll Number, Date, Present, Absent, Leave."""
    rows = _build_export_rows(db, target_date=target_date, search=search)
    label = target_date if target_date else "history"
    headers = ["Serial Number", "Name", "Roll Number", "Date", "Present", "Absent", "Leave"]

    if format == "xlsx":
        excel_bytes = build_attendance_excel(rows)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=attendance_{label}.xlsx"},
        )
    elif format == "pdf":
        summary = {
            "total_records": len(rows),
            "present_count": sum(1 for r in rows if r["present"]),
            "absent_count": sum(1 for r in rows if r["absent"]),
            "leave_count": sum(1 for r in rows if r["leave"]),
        }
        pdf_bytes = build_attendance_pdf(label, summary, rows)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=attendance_{label}.pdf"},
        )
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r["serial"], r["name"], r["roll_number"], r["date"], r["present"], r["absent"], r["leave"]])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=attendance_{label}.csv"},
        )


@app.post("/api/attendance/leave", dependencies=[Depends(get_api_key)])
def mark_leave(payload: LeaveRequest, db=Depends(get_db)):
    """Marks a student as on Leave for one date. A Leave is an attendance
    record with verification_source "LEAVE". The unique
    (roll_number, attendance_date) index means a student on leave can never
    also be marked Present that day (and vice versa)."""
    leave_date = _parse_date(payload.target_date)
    student = students_col.find_one(
        {"roll_number": payload.roll_number, "is_active": True}
    )
    if not student:
        raise HTTPException(status_code=404, detail="Active student not found.")
    record = {
        "roll_number": student["roll_number"],
        "student_name": student["name"],
        "department": student["department"],
        "attendance_date": leave_date.isoformat(),
        "check_in_time": "—",
        "face_distance": 0.0,
        "verification_source": LEAVE_SOURCE,
        "created_at": datetime.utcnow(),
    }
    try:
        result = attendance_col.insert_one(record)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail=f"{student['name']} already has a record on {leave_date.isoformat()} (Present or Leave).",
        )
    record["_id"] = result.inserted_id
    result_doc = serialize_attendance(record)
    # Keep the exact field order/shape the SQL version returned
    result_doc = {
        "id": result_doc["id"],
        "roll_number": record["roll_number"],
        "student_name": record["student_name"],
        "department": record["department"],
        "attendance_date": record["attendance_date"],
        "check_in_time": record["check_in_time"],
        "face_distance": record["face_distance"],
        "verification_source": record["verification_source"],
    }
    log_event(db, "INFO", "ATTENDANCE", f"Marked Leave: {student['name']} ({student['roll_number']}) on {leave_date.isoformat()}")
    return result_doc


@app.delete("/api/attendance/leave", dependencies=[Depends(get_api_key)])
def remove_leave(roll_number: str, target_date: str, db=Depends(get_db)):
    """Removes a Leave mark. Only Leave records can be removed here."""
    leave_date = _parse_date(target_date)
    record = attendance_col.find_one(
        {"roll_number": roll_number, "attendance_date": leave_date.isoformat()}
    )
    if not record:
        raise HTTPException(status_code=404, detail="No record found for this student on that date.")
    if not is_leave(record):
        raise HTTPException(status_code=400, detail="That record is a real check-in, not a Leave mark.")
    student_name = record["student_name"]
    attendance_col.delete_one({"_id": record["_id"]})
    log_event(db, "WARNING", "ATTENDANCE", f"Removed Leave: {student_name} ({roll_number}) on {leave_date.isoformat()}")
    return {"message": f"Leave removed for {student_name} on {leave_date.isoformat()}."}


@app.get("/api/attendance/monthly-register", dependencies=[Depends(get_api_key)])
def download_monthly_register(
    month: str,
    format: Literal["xlsx", "pdf"] = Query("xlsx"),
    db=Depends(get_db),
):
    """Monthly Attendance Register download (Excel / PDF)."""
    try:
        year_str, month_str = month.split("-")
        year, month_num = int(year_str), int(month_str)
        if not (1 <= month_num <= 12):
            raise ValueError
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="month must be YYYY-MM, e.g. 2026-11.")

    data = build_monthly_register(db, year, month_num)
    if format == "xlsx":
        content = build_monthly_register_excel(data)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = build_monthly_register_pdf(data)
        media_type = "application/pdf"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=monthly_attendance_register_{month}.{format}"},
    )


@app.get("/api/system/logs", dependencies=[Depends(get_api_key)])
def get_system_logs(db=Depends(get_db)):
    docs = system_logs_col.find().sort("created_at", DESCENDING).limit(50)
    return [serialize_log(d) for d in docs]
