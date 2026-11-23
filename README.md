<p align="center"><img src="frontend/public/attendx-logo.png" alt="AttendX" width="420"></p>

# AttendX - AI-Powered Smart Attendance Platform

*Recognize. Verify. Attend.*

- `backend/`  FastAPI + OpenCV + dlib (`face_recognition`) API
- `frontend/` Next.js 14 dashboard (proxies to the backend so the API key stays server-side)

See `DEPLOYMENT.md` for environment variables, local development and production deploy.

Quick start:
```bash
cd backend && cp .env.example .env && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && cp .env.example .env.local && npm install && npm run dev
```
