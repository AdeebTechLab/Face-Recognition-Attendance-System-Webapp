# Production Deployment Guide (Vercel + Render/Railway)

## 1. Environment Variables

### Python Backend (Render / Railway)
Configure these environment variables in your backend service:
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/biometric_db`)
- `BACKEND_API_KEY`: Strong random secret token (e.g., `openssl rand -hex 32`)
- `CORS_ORIGINS`: Your Vercel production URL (e.g., `https://attendx.vercel.app`)
- `BIOMETRIC_STORAGE_DIR`: Persistent disk mount path (e.g., `/var/data/biometrics`)

### Next.js Frontend (Vercel)
Configure these server-side environment variables in Vercel Project Settings:
- `PYTHON_BACKEND_URL`: Public HTTPS URL of your Render/Railway backend (e.g., `https://attendx-api.onrender.com`)
- `BACKEND_API_KEY`: Must match the backend `BACKEND_API_KEY` (kept server-side via `/api/proxy`)

## 2. Deploying the Python Backend (Render)
1. Push the repository to GitHub.
2. Create a new **Web Service** on Render pointing to the `backend/` root directory.
3. Select **Docker** as the runtime (uses `backend/Dockerfile` to compile `dlib` cleanly).
4. Attach a **Persistent Disk** mounted at `/var/data/biometrics` so student photos and `.pkl` models survive redeploys.
5. Verify health endpoint at `https://<your-backend>.onrender.com/health`.

## 3. Deploying the Frontend (Vercel)
1. Import the repository into Vercel and set the **Root Directory** to `frontend`.
2. Add `PYTHON_BACKEND_URL` and `BACKEND_API_KEY` in Environment Variables.
3. Deploy. Vercel automatically serves the app over **HTTPS**, which is mandatory for browser `navigator.mediaDevices.getUserMedia()` webcam access.

## 4. Local Development
1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Frontend**:
   ```bash
   cd frontend
   cp .env.example .env.local
   npm install
   npm run dev
   ```
3. Open http://localhost:3000 (`localhost` is allowed to use the webcam without HTTPS).
