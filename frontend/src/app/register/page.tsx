"use client";
import { useRef, useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { Camera, CheckCircle2, AlertCircle, UserPlus } from "lucide-react";

const ANGLE_PROMPTS = [
  "Look straight at the camera",
  "Turn head slightly LEFT",
  "Turn head slightly RIGHT",
  "Tilt chin slightly UP",
  "Tilt chin slightly DOWN",
  "Neutral expression in bright light",
  "Slight smile facing forward",
  "45-degree angle LEFT",
  "45-degree angle RIGHT",
  "Final straight verification shot",
];

export default function RegisterStudentPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [form, setForm] = useState({ roll_number: "", name: "", email: "", department: "Computer Science" });
  const [registeredRoll, setRegisteredRoll] = useState<string | null>(null);
  const [photoCount, setPhotoCount] = useState(0);
  const [statusMsg, setStatusMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    navigator.mediaDevices?.getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => setStatusMsg({ type: "err", text: "Camera permission denied. Enable webcam over HTTPS/localhost." }));

    return () => {
      const stream = videoRef.current?.srcObject as MediaStream | null;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    try {
      const student = await apiFetch("/students", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setRegisteredRoll(student.roll_number);
      setPhotoCount(student.photo_count || 0);
      setStatusMsg({ type: "ok", text: `Profile created for ${student.name}. Capture at least 10 face angles below.` });
    } catch (err: any) {
      setStatusMsg({ type: "err", text: err.message });
    }
  };

  const capturePhoto = async () => {
    if (!registeredRoll || !videoRef.current || !canvasRef.current) return;
    setCapturing(true);
    setStatusMsg(null);

    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
    const base64 = canvas.toDataURL("image/jpeg", 0.9);

    try {
      const res = await apiFetch("/dataset/capture", {
        method: "POST",
        body: JSON.stringify({ roll_number: registeredRoll, image_base64: base64 }),
      });
      if (res.saved) {
        setPhotoCount(res.photo_count);
        setStatusMsg({ type: "ok", text: `Sample ${res.photo_count}/10 verified & saved.` });
      } else {
        setStatusMsg({ type: "err", text: res.reason });
      }
    } catch (err: any) {
      setStatusMsg({ type: "err", text: err.message });
    } finally {
      setCapturing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Biometric Student Registration</h1>
        <p className="text-sm text-slate-500">Register student metadata and capture at least 10 validated face angles</p>
      </div>

      {statusMsg && (
        <div className={`p-4 rounded-xl flex items-center gap-3 text-sm font-medium ${
          statusMsg.type === "ok" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "bg-rose-50 text-rose-800 border border-rose-200"
        }`}>
          {statusMsg.type === "ok" ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {statusMsg.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleCreateProfile} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-indigo-600" /> Step 1: Student Profile
          </h2>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Unique Roll Number</label>
            <input required placeholder="e.g., CS-2026-01" value={form.roll_number}
              onChange={(e) => setForm({ ...form, roll_number: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Full Name</label>
            <input required placeholder="e.g., Zara Ahmed" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Institutional Email</label>
            <input required type="email" placeholder="zara@university.edu" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Department</label>
            <input required value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
          </div>
          <button type="submit" className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold transition">
            Save Student & Unlock Camera Capture
          </button>
        </form>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2">
              <Camera className="w-4 h-4 text-indigo-600" /> Step 2: Multi-Angle Face Capture
            </h2>
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${photoCount >= 10 ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {photoCount} / 10 Required
            </span>
          </div>

          <div className="relative rounded-xl overflow-hidden bg-slate-950 aspect-video">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            <canvas ref={canvasRef} className="hidden" />
            <div className="absolute bottom-3 left-3 right-3 bg-slate-900/80 backdrop-blur text-white text-xs px-3 py-2 rounded-lg">
              Prompt: {ANGLE_PROMPTS[photoCount % ANGLE_PROMPTS.length]}
            </div>
          </div>

          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div className="bg-indigo-600 h-full transition-all" style={{ width: `${Math.min(100, (photoCount / 10) * 100)}%` }} />
          </div>

          <button
            type="button"
            disabled={!registeredRoll || capturing}
            onClick={capturePhoto}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold transition"
          >
            {capturing ? "Validating Face Geometry..." : "Capture Face Sample"}
          </button>
        </div>
      </div>
    </div>
  );
}