<p align="center">
  <img src="frontend/public/attendx-logo.png" alt="AttendX - AI-Powered Smart Attendance Platform" width="420">
</p>

<h1 align="center">Face Recognition Attendance System — AttendX</h1>

<p align="center">
  <strong>Recognize. Verify. Attend.</strong><br>
  An AI-powered smart attendance platform that detects and recognizes students' faces and marks attendance <strong>automatically</strong> — no manual registers, no proxy attendance, no paperwork.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white" alt="Next.js 14">
  <img src="https://img.shields.io/badge/OpenCV-4.10-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/dlib-face__recognition-FF6F00" alt="dlib face recognition">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
</p>

---

## 📌 About the Project

**AttendX** is a complete face-recognition attendance system built for educational institutions. A student walks in front of the camera — the system detects the face, recognizes who it is, and records attendance instantly with date and time. Teachers and admins get a live dashboard, a full attendance history, and one-click **Excel / PDF reports**.

The system is designed around one rule: **attendance is only marked for a confidently recognized, registered student — and never twice for the same day.**

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎥 **Live Attendance (Hidden Camera)** | Start Live Attendance and detection runs in the background — **no camera preview on screen**. The UI shows only results: *Live Detection Active → Student Detected → Attendance Recorded*. |
| 🤖 **Automatic Marking** | Recognized students are marked **Present** automatically. No student selection, no manual "Present" button. |
| 🛡️ **Duplicate Prevention** | A database-level rule guarantees **one attendance record per student per day** — standing in front of the camera again never creates a duplicate. |
| 🌴 **Leave Marking** | Mark any student **on Leave** for a date from Attendance History. A student on leave is never counted Absent, cannot be marked Present the same day, and appears as **L** in the Monthly Register. |
| 📸 **Photo Capture + Upload** | Register students with 10 multi-angle webcam captures, **or upload photos directly from the computer**. Every photo is validated (exactly one clear face) before it is saved. |
| 🧠 **Real Model Training** | Trains 128-d face embeddings (dlib ResNet) and reports **genuine Leave-One-Out Cross-Validation accuracy** — never a fabricated number. |
| 📊 **Dashboard & Analytics** | Daily present/absent counts, attendance percentage, 7-day trend charts, and a full daily roster. |
| 📥 **Excel & PDF Downloads** | The **Download** button in Attendance History offers two reports, both as formatted Excel (`.xlsx`) and PDF: a **Monthly Attendance Register** (one row per student, one column per day of the month — **P / A / L / —** — with per-student totals, %, summary strip and signature block) and a **Detailed List** (Serial Number · Name · Roll Number · Date · Present · Absent · Leave). |
| 👨‍🎓 **Student Management** | Register, update, and deactivate students — deactivation is a soft delete, so historical attendance is always preserved. |
| 🔐 **Secure by Design** | The browser never sees the backend API key — all requests go through a server-side Next.js proxy. Biometric data is stored as 128-d encodings in isolated private storage, never as raw video. |
| ⚠️ **Smart Error Handling** | No face, unknown face, low confidence, multiple faces, already-marked, and camera/service failures all show friendly status messages — the app never crashes and never marks an uncertain face. |

## 🛠️ Tech Stack

**Backend** — Python 3.12 · FastAPI · SQLAlchemy · SQLite (local) / PostgreSQL (production) · OpenCV · dlib (`face_recognition`) · ReportLab (PDF) · openpyxl (Excel)

**Frontend** — Next.js 14 (App Router) · React 18 · TypeScript · Tailwind CSS · Recharts · Lucide icons

**Deployment** — Docker (backend) · Vercel (frontend) · Render / Railway (backend)

## 📂 Project Structure

```
Face-Recognition-Attendance-System-Webapp/
├── backend/                  # FastAPI + face recognition API
│   ├── main.py               # API endpoints (students, dataset, training, recognition, attendance, export)
│   ├── vision_engine.py      # Face detection, training (128-d encodings), recognition
│   ├── excel_generator.py    # Excel (.xlsx) attendance export
│   ├── pdf_generator.py      # PDF attendance export
│   ├── models.py             # Student, AttendanceRecord, ModelVersion, SystemLog
│   ├── database.py · schemas.py · security.py
│   ├── requirements.txt          # Linux / production (Docker)
│   └── requirements-windows.txt  # Windows local development (prebuilt dlib)
├── frontend/                 # Next.js 14 dashboard
│   └── src/app/
│       ├── page.tsx          # Dashboard
│       ├── live/             # Live Attendance (hidden camera, auto-marking)
│       ├── register/         # Student registration + photo capture / upload
│       ├── students/         # Student management
│       ├── dataset/          # Dataset inventory (photos per student)
│       ├── training/         # Model training & version history
│       ├── attendance/       # Attendance History + Download (Excel / PDF)
│       ├── analytics/        # Analytics
│       └── settings/         # Settings & system logs
├── DEPLOYMENT.md
├── CHANGES.md
└── README.md
```

## 🚀 Getting Started (Local)

### Prerequisites
- **Python 3.12** (required — the face-recognition libraries do not support Python 3.13/3.14 yet)
- **Node.js 18+**

### 1️⃣ Backend — PowerShell window 1

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Windows note:** install the packages with the Windows requirements file — it uses the prebuilt `dlib-bin` wheel, because the official `dlib` package tries to compile from source on Windows and fails without Visual Studio:

```powershell
pip install -r requirements-windows.txt
pip install face_recognition==1.3.0 --no-deps
```

On Linux / macOS, simply use `pip install -r requirements.txt`.

Wait for `Application startup complete` and leave the window open. Health check: http://localhost:8000/health

### 2️⃣ Frontend — PowerShell window 2 (new window)

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser. Both windows must stay open while you use the app.

## 📖 How to Use

1. **Student Registration** — add the student (roll number, name, email, department), then capture **10 face photos** with the webcam *or* upload photos from your computer.
2. **Dataset Management** — confirm the student shows **10/10 photos — Ready**.
3. **Model Training** — click **Train New Model Version** and check the validation accuracy.
4. **Live Attendance** — click **Start Live Attendance**. The camera works invisibly in the background; recognized students appear in the results table and are marked automatically.
5. **Attendance History** — see every check-in, mark **Leave** for absent-with-permission students, and click **Download** (top-right) for the **Monthly Register** or **Detailed List** in Excel or PDF.

## 🔌 API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/students` | Register a student |
| `GET` | `/api/students` | List students |
| `POST` | `/api/dataset/capture` | Validate & save a face photo (webcam capture or upload) |
| `GET` | `/api/dataset/summary` | Photos per student / training readiness |
| `POST` | `/api/model/train` | Train a new model version |
| `GET` | `/api/model/status` | Active model & version history |
| `POST` | `/api/recognition/recognize` | Recognize faces in a frame & auto-mark attendance |
| `GET` | `/api/attendance` | Attendance history (filter by date / roll / search) |
| `GET` | `/api/attendance/daily-report` | Daily roster, totals & 7-day trend |
| `GET` | `/api/attendance/export?format=xlsx\|pdf\|csv` | Download attendance (Serial Number, Name, Roll Number, Date, Present, Absent, Leave) |
| `POST` | `/api/attendance/leave` | Mark a student on Leave for a date |
| `DELETE` | `/api/attendance/leave` | Remove a Leave mark |
| `GET` | `/api/attendance/monthly-register?month=YYYY-MM&format=xlsx\|pdf` | Download the Monthly Attendance Register |
| `GET` | `/health` | Health check |

All `/api/*` endpoints require the `X-API-Key` header (handled automatically by the frontend proxy).

## ☁️ Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** — backend on Render/Railway with Docker (persistent disk for biometric storage), frontend on Vercel. HTTPS is required in production for browser camera access.

## 📝 Changelog

See **[CHANGES.md](CHANGES.md)** for the latest update: Attendance History Excel/PDF download, hidden-camera Live Attendance with automatic marking, and the fixed photo capture + upload flow.

## 👨‍💻 Author

**Muhammad Akhtar** — AI Engineering student, The Islamia University of Bahawalpur, Pakistan

- GitHub: [@AdeebTechLab](https://github.com/AdeebTechLab)
- LinkedIn: [ai-engineer-muhammad-akhtar](https://www.linkedin.com/in/ai-engineer-muhammad-akhtar)

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.
