from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, UniqueConstraint
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete preserves history
    photo_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), index=True, nullable=False)
    student_name = Column(String(120), nullable=False)
    department = Column(String(100), nullable=False)
    attendance_date = Column(Date, default=date.today, index=True, nullable=False)
    check_in_time = Column(String(20), nullable=False)
    face_distance = Column(Float, nullable=False)
    verification_source = Column(String(50), default="LIVE_WEBCAM", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Database-level duplicate prevention: strictly 1 attendance record per student per day
    __table_args__ = (
        UniqueConstraint("roll_number", "attendance_date", name="uq_student_daily_attendance"),
    )

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(50), unique=True, nullable=False)
    students_count = Column(Integer, nullable=False)
    encodings_count = Column(Integer, nullable=False)
    validation_accuracy = Column(Float, nullable=False)
    tolerance_used = Column(Float, nullable=False)
    artifact_path = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    trained_at = Column(DateTime, default=datetime.utcnow)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    module = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)