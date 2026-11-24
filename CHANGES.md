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

---

# Update 2 — Monthly Attendance Register + Leave Option

## Change 4 — Monthly Attendance Register download (Excel + PDF, same layout)
- The **Download** button on Attendance History now offers a **Monthly Register**
  for the month chosen in the new month picker next to it — in **Excel and PDF
  with an identical layout**, matching the Monthly Attendance Register format:
  - Title "ATTENDX \u2022 MONTHLY ATTENDANCE REGISTER" and subtitle
    "Class: <department> | Month: <Month Year> | Academic Session <YYYY-YY>".
  - Summary strip: Total Students, Working Days, Present, Absent, Leave, Overall %.
  - Legend: P Present \u00b7 A Absent \u00b7 L Leave \u00b7 \u2014 Holiday / No Class.
  - One row per student: #, Student Name, Roll No., one cell per day of the month,
    then per-student totals P / A / L / %.
  - Signature block (Teacher / Coordinator Signature, Date, Remarks) and footer.
- Register rules (real stored data only): a "class day" is a day with at least one
  stored record that month. On a class day a student is P (check-in), L (Leave
  record) or A (no record); other days show \u2014. Working Days = number of class
  days. Percentage = P / (P + A); Leave days are excluded from the percentage.
- New backend module `backend/monthly_register.py` builds the register data once;
  `build_monthly_register_excel` (excel_generator.py) and
  `build_monthly_register_pdf` (pdf_generator.py) render it, served by
  `GET /api/attendance/monthly-register?month=YYYY-MM&format=xlsx|pdf`.
- The previous detailed download is unchanged, listed in the same menu as
  "Detailed List \u2014 Excel / PDF".

## Change 5 — Leave option in the online app
- Attendance History has a **Mark Leave** card: select a student, pick a date,
  click Mark Leave. Leave rows appear in the history table with an amber
  **Leave** badge and a **Remove Leave** action.
- Backend: `POST /api/attendance/leave` and `DELETE /api/attendance/leave`.
  A Leave is stored as an attendance record with `verification_source = "LEAVE"`
  \u2014 **no database schema change**, so existing databases keep working.
  The existing one-record-per-student-per-day rule now also guarantees a student
  cannot be both Present and on Leave on the same day.
- Leave is respected everywhere: the daily report and dashboard count Leave
  separately (a student on leave is not Absent), the detailed export's Leave
  column now shows real Leave data, the Monthly Register shows L, and Live
  Attendance answers `ON_LEAVE` (student shown once with status Leave, never
  marked present). The dashboard's Recent Live Check-Ins feed excludes Leave
  records, since they are not check-ins.

## Files changed in Update 2
- Backend: `main.py`, `schemas.py` (LeaveRequest), `excel_generator.py`,
  `pdf_generator.py` \u2014 new file: `monthly_register.py`.
- Frontend: `src/app/attendance/page.tsx`, `src/app/live/page.tsx`,
  `src/app/page.tsx` (dashboard feed filter).
- Untouched: `models.py`, `database.py`, `vision_engine.py`, `security.py`.
