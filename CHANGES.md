# AttendX — Controlled Changes (Attendance History Download + Hidden Live Attendance)

Only the requested areas were changed. Architecture, database schema, authentication,
student data, attendance records, and the face-recognition engine (`vision_engine.py`)
are untouched.

## Change 1 — Attendance History Download
- Removed the old **Reports & Exports** page and its sidebar entry (the old
  Report / Export / Download location).
- **Attendance History** (`/attendance`) now has a **Download** button on the right
  side of its header, in the existing indigo UI style, with **Download Excel** and
  **Download PDF** options. It respects the page's current date/search filters.
- The existing export endpoint (`GET /api/attendance/export`) was extended — not
  duplicated — to `format=xlsx|pdf|csv` and now emits these columns in this exact order:
  **Serial Number, Name, Roll Number, Date, Present, Absent, Leave**.
- Data is real stored data only: a stored check-in for a date = Present; an active
  student with no check-in that date = Absent (the project's existing daily-report
  rule). The system stores **no Leave records**, so the Leave column is present but
  left blank — no values are fabricated.
- Excel is a real `.xlsx` (new `backend/excel_generator.py`, openpyxl): styled header,
  readable column widths, freeze panes, auto-filter, alternating row shading.
- PDF (`backend/pdf_generator.py`) uses the same 7 columns with fixed column widths
  and wrapping text; long tables split across pages with a repeating header
  (verified with 300 rows → 14 pages, nothing clipped).
- `openpyxl==3.1.5` was added to `backend/requirements.txt` for Excel generation.

## Change 2 — Live Recorder/Camera Hidden
- On **Live Attendance** (`/live`), the camera preview and bounding-box overlay are
  gone from the main UI. The `<video>` element is kept off-screen (1px, transparent)
  purely so the existing frame-capture → recognition pipeline keeps working internally.
- The page now shows: **Live Attendance**, a pulsing **● Live Detection Active**
  indicator, **Automatic Detection Enabled**, a **Student Detected** card, and a
  results table (Name | Roll Number | Status | Date | Time).
- The camera now starts only when **Start Live Attendance** is pressed (previously it
  started on page load) and is released on Stop or when leaving the page.

## Change 3 — Automatic Attendance Detection
- This already existed in the backend and was kept: starting live sends frames to the
  existing `POST /api/recognition/recognize` with `auto_mark: true`. A recognized
  student is marked automatically — no student selection, no manual Present button.
- Duplicates are still prevented by the existing database rule (one record per
  student per day): a repeated detection returns `ALREADY_MARKED`, creates no new
  record, and the UI shows the student once with their real recorded check-in time
  from Attendance History.
- Error handling (shown as friendly status messages, never a crash): no face
  detected, unknown/unrecognized face, low recognition confidence (never marked),
  multiple faces (each recognized student is marked), already marked, camera
  start failure, and recognition/network failure (loop keeps retrying).

## Verification performed
- Backend: 34 automated API tests passed — Excel/PDF/CSV headers and column order,
  Present/Absent correctness for multiple students and dates, history export across
  dates, auto-mark on recognition, duplicate prevention (exactly 1 DB record),
  unknown face not marked, no-face frame OK, Attendance History updates after a live
  mark, and the dashboard daily-report/students endpoints unchanged.
- Frontend: `tsc --noEmit` clean and `npm run build` succeeds; all existing routes
  build (`/reports` intentionally removed per Change 1).
