"""
AttendX - MongoDB document shapes and serializers.

There are no ORM classes any more. A "model" is now just a plain dict stored
in a collection. These helpers convert a stored document into exactly the
JSON shape the old SQLAlchemy models produced, so the frontend does not
need to change:

  - Mongo `_id` (ObjectId)  ->  `id` as a string
    (was an integer before - see MIGRATION_NOTES.md)
  - attendance_date is stored as an ISO string "YYYY-MM-DD"
    (was a SQL Date, serialised to the same string)
  - created_at / trained_at stay as datetimes, which FastAPI
    serialises to ISO strings just like before.
"""
from bson import ObjectId
from bson.errors import InvalidId


def to_object_id(value):
    """Return an ObjectId for a string id, or None if it isn't a valid one."""
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError, ValueError):
        return None


def _base(doc):
    if doc is None:
        return None
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    return out


def serialize_student(doc):
    return _base(doc)


def serialize_attendance(doc):
    return _base(doc)


def serialize_model_version(doc):
    return _base(doc)


def serialize_log(doc):
    return _base(doc)
