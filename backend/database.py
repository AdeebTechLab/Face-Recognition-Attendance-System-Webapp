"""
AttendX - MongoDB connection (PyMongo, sync)

Replaces the old SQLAlchemy/SQLite/PostgreSQL setup.

Environment:
  MONGODB_URL      Full connection string. Examples:
                     Local : mongodb://localhost:27017
                     Atlas : mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
                   For backwards compatibility, DATABASE_URL is also honoured
                   if (and only if) it starts with "mongodb".
  MONGODB_DB_NAME  Database name. Default: attendx
"""
import os

from pymongo import MongoClient, ASCENDING

MONGODB_URL = os.getenv("MONGODB_URL") or ""
if not MONGODB_URL:
    legacy = os.getenv("DATABASE_URL", "")
    MONGODB_URL = legacy if legacy.startswith("mongodb") else "mongodb://localhost:27017"

MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "attendx")

client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=10000)
db = client[MONGODB_DB_NAME]

# Collections (created automatically on first use)
students_col = db["students"]
attendance_col = db["attendance_records"]
model_versions_col = db["model_versions"]
system_logs_col = db["system_logs"]


def ensure_indexes():
    """Create the indexes that replace the old SQL constraints.

    This is the most important part of the migration:
    - students.roll_number / students.email were UNIQUE columns.
    - attendance had UniqueConstraint(roll_number, attendance_date) -
      strictly one attendance record per student per day. The compound
      unique index below is what now guarantees that in MongoDB.
    - model_versions.version_tag was a UNIQUE column.
    Safe to call repeatedly (create_index is idempotent).
    """
    students_col.create_index([("roll_number", ASCENDING)], unique=True)
    students_col.create_index([("email", ASCENDING)], unique=True)
    students_col.create_index([("is_active", ASCENDING)])
    attendance_col.create_index(
        [("roll_number", ASCENDING), ("attendance_date", ASCENDING)],
        unique=True,
        name="uq_student_daily_attendance",
    )
    attendance_col.create_index([("attendance_date", ASCENDING)])
    model_versions_col.create_index([("version_tag", ASCENDING)], unique=True)
    system_logs_col.create_index([("created_at", -1)])


# Indexes are created at import/startup, as Base.metadata.create_all() was before.
ensure_indexes()


def get_db():
    """FastAPI dependency - same name/signature the endpoints already used."""
    yield db
