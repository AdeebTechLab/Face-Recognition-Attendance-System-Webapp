"""
One-off data migration: old SQLite database -> MongoDB.

Use this ONLY if you have existing students/attendance in the old
biometric_attendance.db (SQLite) file and want to keep them.
Fresh installs don't need it - just start the new backend.

Usage (from the backend folder, with the new requirements installed):
    set MONGODB_URL=mongodb+srv://...      (Windows PowerShell: $env:MONGODB_URL="...")
    python migrate_sql_to_mongo.py path\to\biometric_attendance.db

Notes:
- Old integer ids are NOT carried over. Mongo documents get new ObjectIds,
  and the app now returns `id` as a string. Nothing else references the old
  numeric ids (attendance is keyed by roll_number), so this is safe.
- attendance_date is converted to a "YYYY-MM-DD" string, matching the new code.
- Rows that would violate a unique index are skipped and reported.
"""
import os
import sqlite3
import sys
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# Importing database creates the collections + unique indexes first.
import database  # noqa: F401


def _parse_dt(value):
    if not value:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def main(sqlite_path: str):
    if not os.path.exists(sqlite_path):
        raise SystemExit(f"SQLite file not found: {sqlite_path}")

    sql = sqlite3.connect(sqlite_path)
    sql.row_factory = sqlite3.Row
    mongo = MongoClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = mongo[os.getenv("MONGODB_DB_NAME", "attendx")]

    def copy(table, collection, transform):
        try:
            rows = sql.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError:
            print(f"{table}: table not found, skipped")
            return
        ok = skipped = 0
        for row in rows:
            try:
                collection.insert_one(transform(dict(row)))
                ok += 1
            except DuplicateKeyError:
                skipped += 1
        print(f"{table}: {ok} copied, {skipped} duplicates skipped")

    copy("students", db["students"], lambda r: {
        "roll_number": r["roll_number"],
        "name": r["name"],
        "email": r["email"],
        "department": r["department"],
        "is_active": bool(r.get("is_active", 1)),
        "photo_count": r.get("photo_count", 0) or 0,
        "created_at": _parse_dt(r.get("created_at")),
    })
    copy("attendance_records", db["attendance_records"], lambda r: {
        "roll_number": r["roll_number"],
        "student_name": r["student_name"],
        "department": r["department"],
        "attendance_date": str(r["attendance_date"])[:10],
        "check_in_time": r["check_in_time"],
        "face_distance": r["face_distance"],
        "verification_source": r.get("verification_source") or "LIVE_WEBCAM",
        "created_at": _parse_dt(r.get("created_at")),
    })
    copy("model_versions", db["model_versions"], lambda r: {
        "version_tag": r["version_tag"],
        "students_count": r["students_count"],
        "encodings_count": r["encodings_count"],
        "validation_accuracy": r["validation_accuracy"],
        "tolerance_used": r["tolerance_used"],
        "artifact_path": r["artifact_path"],
        "is_active": bool(r.get("is_active", 1)),
        "trained_at": _parse_dt(r.get("trained_at")),
    })
    copy("system_logs", db["system_logs"], lambda r: {
        "level": r["level"],
        "module": r["module"],
        "message": r["message"],
        "created_at": _parse_dt(r.get("created_at")),
    })
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python migrate_sql_to_mongo.py <biometric_attendance.db>")
    main(sys.argv[1])
