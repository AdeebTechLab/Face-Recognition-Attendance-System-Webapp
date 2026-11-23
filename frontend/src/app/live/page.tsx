"use client";
import { useRef, useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { ScanFace, Play, Square, ShieldAlert, CheckCircle } from "lucide-react";

export default function LiveRecognitionPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);

  const [running, setRunning] = useState(false);
  const [tolerance, setTolerance] = useState(0.5);
  const [detections, setDetections] = useState<any[]>([]);
  const [toastBanner, setToastBanner] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    navigator.mediaDevices?.getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => setErrorMsg("Webcam access blocked. Please allow camera access."));

    return () => {
      const stream = videoRef.current?.srcObject as MediaStream | null;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  useEffect(() => {
    if (!running) return;
    let active = true;

    const tick = async () => {
      if (!active || !videoRef.current || !captureCanvasRef.current) return;
      const video = videoRef.current;
      if (video.readyState === 4) {
        const capCanvas = captureCanvasRef.current;
        capCanvas.width = video.videoWidth;
        capCanvas.height = video.videoHeight;
        capCanvas.getContext("2d")?.drawImage(video, 0, 0);
        const base64 = capCanvas.toDataURL("image/jpeg", 0.8);

        try {
          const res = await apiFetch("/recognition/recognize", {
            method: "POST",
            body: JSON.stringify({ image_base64: base64, tolerance, auto_mark: true }),
          });
          setDetections(res.detections || []);
          drawBoundingBoxes(res.detections || []);

          const newlyMarked = (res.detections || []).find((d: any) => d.attendance_event === "MARKED_NEW");
          if (newlyMarked) {
            setToastBanner(newlyMarked.message);
            setTimeout(() => setToastBanner(null), 5000);
          }
          setErrorMsg(null);
        } catch (err: any) {
          setErrorMsg(err.message);
        }
      }
      if (active) setTimeout(tick, 900); // ~1.1 FPS inference loop prevents server overload
    };

    tick();
    return () => { active = false; };
  }, [running, tolerance]);

  const drawBoundingBoxes = (items: any[]) => {
    const canvas = overlayCanvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    items.forEach((item) => {
      const { top, right, bottom, left, frame_width, frame_height } = item.box;
      const scaleX = canvas.width / frame_width;
      const scaleY = canvas.height / frame_height;

      const x = left * scaleX;
      const y = top * scaleY;
      const w = (right - left) * scaleX;
      const h = (bottom - top) * scaleY;

      const isKnown = item.status === "KNOWN";
      ctx.strokeStyle = isKnown ? "#10b981" : "#ef4444";
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, w, h);

      const label = isKnown
        ? `${item.name} (${item.roll_number}) • d=${item.distance}`
        : `Unknown • d=${item.distance}`;

      ctx.font = "bold 12px Inter, sans-serif";
      ctx.fillStyle = isKnown ? "#10b981" : "#ef4444";
      ctx.fillRect(x, Math.max(0, y - 26), ctx.measureText(label).width + 16, 26);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x + 8, Math.max(17, y - 9));
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Live Biometric Scanner</h1>
          <p className="text-sm text-slate-500">Real-time facial verification with automatic daily attendance logging</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs">
            <span className="font-semibold text-slate-700">Distance Threshold: {tolerance.toFixed(2)}</span>
            <input type="range" min="0.35" max="0.60" step="0.01" value={tolerance}
              onChange={(e) => setTolerance(parseFloat(e.target.value))}
              className="block w-32 accent-indigo-600 mt-1" />
          </div>

          <button
            onClick={() => setRunning(!running)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition ${
              running ? "bg-rose-600 hover:bg-rose-700" : "bg-indigo-600 hover:bg-indigo-700"
            }`}
          >
            {running ? <><Square className="w-4 h-4" /> Stop Scanner</> : <><Play className="w-4 h-4" /> Start Live Scanner</>}
          </button>
        </div>
      </div>

      {toastBanner && (
        <div className="bg-emerald-600 text-white px-5 py-3.5 rounded-xl shadow-lg flex items-center gap-3 font-medium">
          <CheckCircle className="w-5 h-5 shrink-0" />
          <span>{toastBanner}</span>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center gap-2 text-sm">
          <ShieldAlert className="w-4 h-4" /> {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 relative rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 shadow-lg aspect-video">
          <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          <canvas ref={overlayCanvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
          <canvas ref={captureCanvasRef} className="hidden" />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <ScanFace className="w-4 h-4 text-indigo-600" /> Active Frame Telemetry
          </h2>
          {detections.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              {running ? "Scanning frame for faces..." : "Click Start Live Scanner to begin"}
            </p>
          ) : (
            detections.map((d, idx) => (
              <div key={idx} className={`p-4 rounded-xl border ${d.status === "KNOWN" ? "bg-emerald-50/60 border-emerald-200" : "bg-rose-50/60 border-rose-200"}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold text-slate-900">{d.name}</p>
                    <p className="text-xs text-slate-600">{d.roll_number || "Unregistered Subject"}</p>
                  </div>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${d.status === "KNOWN" ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"}`}>
                    {d.status}
                  </span>
                </div>
                <div className="mt-2 text-xs text-slate-500 flex justify-between">
                  <span>Euclidean Dist: <strong>{d.distance}</strong></span>
                  <span>Match Score: <strong>{d.confidence}%</strong></span>
                </div>
                {d.message && <p className="mt-2 text-xs font-medium text-indigo-700">{d.message}</p>}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}