import os
import csv
import io
from datetime import datetime, date, timedelta
from typing import Optional, Literal
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db
from models import Student, AttendanceRecord, ModelVersion, SystemLog
from schemas import StudentCreate, StudentUpdate, FrameCaptureRequest, TrainRequest, RecognizeRequest
from security import get_api_key
from vision_engine import validate_and_save_capture, train_encodings_model, recognize_faces_in_frame, DATASET_DIR
from pdf_generator import build_attendance_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AttendX API - AI-Powered Smart Attendance Platform",
    version="1.0.0",
    description="Enterprise Python OpenCV + dlib Recognition Engine"
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

def log_event(db: Session, level: str, module: str, message: str):
    db.add(SystemLog(level=level, module=module, message=message))
    db.commit()

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# --- 1. STUDENT CRUD ENDPOINTS ---
@app.post("/api/students", dependencies=[Depends(get_api_key)])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(
        (Student.roll_number == payload.roll_number) | (Student.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this roll number or email already exists.")

    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    log_event(db, "INFO", "STUDENTS", f"Registered student {student.roll_number} ({student.name})")
    return student

@app.get("/api/students", dependencies=[Depends(get_api_key)])
def list_students(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(Student)
    if not include_inactive:
        query = query.filter(Student.is_active == True)
    return query.order_by(Student.roll_number.asc()).all()

@app.get("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student

@app.put("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(student, k, v)
    db.commit()
    db.refresh(student)
    log_event(db, "INFO", "STUDENTS", f"Updated profile for {student.roll_number}")
    return student

@app.delete("/api/students/{student_id}", dependencies=[Depends(get_api_key)])
def deactivate_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    # Soft delete preserves historical attendance logs
    student.is_active = False
    db.commit()
    log_event(db, "WARNING", "STUDENTS", f"Deactivated student {student.roll_number}; historical records preserved.")
    return {"message": f"Student {student.roll_number} deactivated. Historical attendance preserved."}

# --- 2. DATASET CAPTURE & GALLERY ---
@app.post("/api/dataset/capture", dependencies=[Depends(get_api_key)])
def capture_dataset_frame(payload: FrameCaptureRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.roll_number == payload.roll_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student roll number not registered.")
    try:
        res = validate_and_save_capture(payload.roll_number, payload.image_base64)
        if res["saved"]:
            student.photo_count = res["photo_count"]
            db.commit()
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/dataset/summary", dependencies=[Depends(get_api_key)])
def dataset_summary(db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.is_active == True).all()
    data = []
    for s in students:
        safe_roll = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s.roll_number)
        folder = os.path.join(DATASET_DIR, safe_roll)
        files = sorted(os.listdir(folder)) if os.path.exists(folder) else []
        data.append({
            "id": s.id,
            "roll_number": s.roll_number,
            "name": s.name,
            "department": s.department,
            "photo_count": len(files),
            "ready_for_training": len(files) >= 10
        })
    return data

# --- 3. MODEL TRAINING & STATUS ---
@app.post("/api/model/train", dependencies=[Depends(get_api_key)])
def trigger_training(payload: TrainRequest, db: Session = Depends(get_db)):
    active_students = db.query(Student).filter(Student.is_active == True).all()
    try:
        metrics = train_encodings_model(active_students, tolerance=payload.tolerance)
        db.query(ModelVersion).update({"is_active": False})
        version = ModelVersion(**metrics, is_active=True)
        db.add(version)
        db.commit()
        db.refresh(version)
        log_event(db, "INFO", "TRAINING", f"Trained {version.version_tag} | Accuracy: {version.validation_accuracy}%")
        return version
    except ValueError as e:
        log_event(db, "ERROR", "TRAINING", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/model/status", dependencies=[Depends(get_api_key)])
def get_model_status(db: Session = Depends(get_db)):
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    versions = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).limit(10).all()
    return {
        "active_model": active_model,
        "history": versions
    }

# --- 4. LIVE RECOGNITION & ATTENDANCE ---
@app.post("/api/recognition/recognize", dependencies=[Depends(get_api_key)])
def recognize_frame(payload: RecognizeRequest, db: Session = Depends(get_db)):
    try:
        detections = recognize_faces_in_frame(payload.image_base64, tolerance=payload.tolerance)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    today = date.today()
    now_str = datetime.now().strftime("%H:%M:%S")

    for det in detections:
        if det["status"] == "KNOWN" and payload.auto_mark:
            student = db.query(Student).filter(
                Student.roll_number == det["roll_number"],
                Student.is_active == True
            ).first()
            if not student:
                det["status"] = "UNKNOWN"
                det["name"] = "Unknown"
                det["attendance_event"] = None
                continue

            record = AttendanceRecord(
                roll_number=student.roll_number,
                student_name=student.name,
                department=student.department,
                attendance_date=today,
                check_in_time=now_str,
                face_distance=det["distance"],
                verification_source="LIVE_WEBCAM"
            )
            try:
                db.add(record)
                db.commit()
                det["attendance_event"] = "MARKED_NEW"
                det["message"] = f"Attendance marked: {student.name} ({student.roll_number}) at {now_str}"
                log_event(db, "INFO", "ATTENDANCE", det["message"])
            except IntegrityError:
                db.rollback()
                det["attendance_event"] = "ALREADY_MARKED"
                det["message"] = f"Already marked today: {student.name} ({student.roll_number})"
        else:
            det["attendance_event"] = "IGNORED_UNKNOWN"

    return {"detections": detections}

@app.post("/api/attendance/mark", dependencies=[Depends(get_api_key)])
def mark_verified_attendance(roll_number: str, face_distance: float, db: Session = Depends(get_db)):
    """Explicit endpoint restricted to verified live webcam matches."""
    student = db.query(Student).filter(Student.roll_number == roll_number, Student.is_active == True).first()
    if not student:
        raise HTTPException(status_code=404, detail="Active student not found.")
    today = date.today()
    now_str = datetime.now().strftime("%H:%M:%S")
    record = AttendanceRecord(
        roll_number=student.roll_number,
        student_name=student.name,
        department=student.department,
        attendance_date=today,
        check_in_time=now_str,
        face_distance=face_distance,
        verification_source="LIVE_WEBCAM"
    )
    try:
        db.add(record)
        db.commit()
        return {"status": "MARKED", "roll_number": student.roll_number, "time": now_str}
    except IntegrityError:
        db.rollback()
        return {"status": "DUPLICATE_PREVENTED", "roll_number": student.roll_number}

@app.get("/api/attendance", dependencies=[Depends(get_api_key)])
def get_attendance_history(
    target_date: Optional[str] = None,
    roll_number: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceRecord)
    if target_date:
        query = query.filter(AttendanceRecord.attendance_date == _parse_date(target_date))
    if roll_number:
        query = query.filter(AttendanceRecord.roll_number == roll_number)
    if search:
        like_term = f"%{search}%"
        query = query.filter(
            (AttendanceRecord.student_name.ilike(like_term)) |
            (AttendanceRecord.roll_number.ilike(like_term))
        )
    return query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.check_in_time.desc()).all()

@app.get("/api/attendance/daily-report", dependencies=[Depends(get_api_key)])
def get_daily_report(target_date: Optional[str] = None, db: Session = Depends(get_db)):
    report_date = _parse_date(target_date) if target_date else date.today()
    active_students = db.query(Student).filter(Student.is_active == True).order_by(Student.roll_number).all()
    active_rolls = {s.roll_number for s in active_students}
    # Only active students count: deactivated students' history must not inflate today's totals
    present_records = [
        r for r in db.query(AttendanceRecord).filter(AttendanceRecord.attendance_date == report_date).all()
        if r.roll_number in active_rolls
    ]
    present_map = {r.roll_number: r for r in present_records}

    roster = []
    for s in active_students:
        rec = present_map.get(s.roll_number)
        roster.append({
            "roll_number": s.roll_number,
            "student_name": s.name,
            "department": s.department,
            "status": "Present" if rec else "Absent",
            "check_in_time": rec.check_in_time if rec else "—",
            "face_distance": rec.face_distance if rec else "—"
        })

    total = len(active_students)
    present_count = len(present_records)
    absent_count = max(0, total - present_count)
    pct = round((present_count / total) * 100.0, 1) if total > 0 else 0.0

    # Weekly trend (last 7 days)
    trend = []
    for offset in range(6, -1, -1):
        d = report_date - timedelta(days=offset)
        cnt = db.query(AttendanceRecord).filter(
            AttendanceRecord.attendance_date == d,
            AttendanceRecord.roll_number.in_(active_rolls) if active_rolls else False,
        ).count()
        trend.append({
            "date": d.strftime("%b %d"),
            "present": cnt,
            "absent": max(0, total - cnt),
            "rate": round((cnt / total) * 100.0, 1) if total > 0 else 0.0
        })

    return {
        "date": report_date.isoformat(),
        "total_students": total,
        "present_count": present_count,
        "absent_count": absent_count,
        "attendance_percentage": pct,
        "roster": roster,
        "weekly_trend": trend
    }

@app.get("/api/attendance/export", dependencies=[Depends(get_api_key)])
def export_attendance(
    target_date: Optional[str] = None,
    format: Literal["csv", "pdf"] = Query("csv"),
    db: Session = Depends(get_db)
):
    report = get_daily_report(target_date=target_date, db=db)
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Roll Number", "Student Name", "Department", "Date", "Status", "Check-In Time", "Face Distance"])
        for row in report["roster"]:
            writer.writerow([
                row["roll_number"], row["student_name"], row["department"],
                report["date"], row["status"], row["check_in_time"], row["face_distance"]
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=attendance_{report['date']}.csv"}
        )
    else:
        pdf_bytes = build_attendance_pdf(report["date"], report, report["roster"])
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=attendance_{report['date']}.pdf"}
        )

@app.get("/api/system/logs", dependencies=[Depends(get_api_key)])
def get_system_logs(db: Session = Depends(get_db)):
    return db.query(SystemLog).order_by(SystemLog.created_at.desc()).limit(50).all()