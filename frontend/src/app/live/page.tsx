"use client";
import { useRef, useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { ScanFace, Play, Square, ShieldAlert, CheckCircle } from "lucide-react";

type AttendanceResult = {
  name: string;
  roll_number: string;
  status: string;
  date: string;
  time: string;
};

export default function LiveRecognitionPage() {
  // The video element is kept off-screen (never shown as a camera preview).
  // It only feeds frames to the capture canvas for the existing recognition
  // pipeline, exactly as before — the processing is unchanged.
  const videoRef = useRef<HTMLVideoElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const handledRollsRef = useRef<Set<string>>(new Set());

  const [running, setRunning] = useState(false);
  const [starting, setStarting] = useState(false);
  const [tolerance, setTolerance] = useState(0.5);
  const [results, setResults] = useState<AttendanceResult[]>([]);
  const [lastDetected, setLastDetected] = useState<AttendanceResult | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [toastBanner, setToastBanner] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  // Release the camera if the user leaves the page.
  useEffect(() => stopStream, [stopStream]);

  const startLive = async () => {
    setErrorMsg(null);
    setStarting(true);
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera is not available in this browser.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => undefined);
      }
      setStatusMsg("Live detection active — waiting for a student…");
      setRunning(true);
    } catch {
      stopStream();
      setErrorMsg("Camera could not be started. Please allow camera access and try again.");
    } finally {
      setStarting(false);
    }
  };

  const stopLive = () => {
    setRunning(false);
    stopStream();
    setStatusMsg(null);
  };

  const upsertResult = (row: AttendanceResult) => {
    setResults((prev) => {
      const rest = prev.filter((r) => r.roll_number !== row.roll_number);
      return [row, ...rest];
    });
    setLastDetected(row);
  };

  useEffect(() => {
    if (!running) return;
    let active = true;

    const tick = async () => {
      if (!active || !videoRef.current || !captureCanvasRef.current) return;
      const video = videoRef.current;
      if (video.readyState >= 2 && video.videoWidth > 0) {
        const capCanvas = captureCanvasRef.current;
        capCanvas.width = video.videoWidth;
        capCanvas.height = video.videoHeight;
        capCanvas.getContext("2d")?.drawImage(video, 0, 0);
        const base64 = capCanvas.toDataURL("image/jpeg", 0.8);

        try {
          // Existing recognition endpoint with auto_mark: a recognized
          // student is marked automatically — no manual Present click.
          // The backend's one-record-per-student-per-day rule prevents
          // duplicates when the same face stays in front of the camera.
          const res = await apiFetch("/recognition/recognize", {
            method: "POST",
            body: JSON.stringify({ image_base64: base64, tolerance, auto_mark: true }),
          });
          const detections: any[] = res.detections || [];
          setErrorMsg(null);

          if (detections.length === 0) {
            setStatusMsg("No face detected — waiting for a student…");
          } else if (detections.length > 1) {
            setStatusMsg("Multiple faces detected — each recognized student is marked automatically.");
          }

          for (const d of detections) {
            if (d.status !== "KNOWN") {
              // Unknown face or recognition confidence too low: never mark.
              setStatusMsg("Unknown face detected — attendance not marked. Recognition confidence was too low to identify the student.");
              continue;
            }
            if (d.attendance_event === "MARKED_NEW") {
              const now = new Date();
              upsertResult({
                name: d.name,
                roll_number: d.roll_number,
                status: "Present",
                date: now.toLocaleDateString("en-CA"),
                time: now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
              });
              handledRollsRef.current.add(d.roll_number);
              setStatusMsg("Attendance recorded successfully.");
              setToastBanner(d.message);
              setTimeout(() => setToastBanner(null), 5000);
            } else if (d.attendance_event === "ALREADY_MARKED") {
              setStatusMsg(d.message || `${d.name} is already marked present today.`);
              // Show the student once, with their real recorded check-in
              // time from Attendance History — not a fabricated time.
              if (!handledRollsRef.current.has(d.roll_number)) {
                handledRollsRef.current.add(d.roll_number);
                try {
                  const today = new Date().toLocaleDateString("en-CA");
                  const recs = await apiFetch(`/attendance?target_date=${today}&roll_number=${encodeURIComponent(d.roll_number)}`);
                  const rec = Array.isArray(recs) ? recs[0] : null;
                  if (rec && active) {
                    upsertResult({
                      name: rec.student_name,
                      roll_number: rec.roll_number,
                      status: "Present",
                      date: rec.attendance_date,
                      time: rec.check_in_time,
                    });
                  }
                } catch {
                  // History lookup is best-effort; the duplicate was already
                  // prevented by the backend and the status message is shown.
                }
              }
            } else if (d.attendance_event === "ON_LEAVE") {
              // The student has a Leave record today: never mark present,
              // show them once in the results with status Leave.
              setStatusMsg(d.message || `${d.name} is on leave today.`);
              if (!handledRollsRef.current.has(d.roll_number)) {
                handledRollsRef.current.add(d.roll_number);
                upsertResult({
                  name: d.name,
                  roll_number: d.roll_number,
                  status: "Leave",
                  date: new Date().toLocaleDateString("en-CA"),
                  time: "—",
                });
              }
            }
          }
        } catch (err: any) {
          // Recognition service / network failure: show it, never crash,
          // and keep the loop alive for the next frame.
          setErrorMsg(err.message || "Recognition service is unavailable. Retrying…");
        }
      }
      if (active) setTimeout(tick, 900); // ~1.1 FPS inference loop prevents server overload
    };

    tick();
    return () => { active = false; };
  }, [running, tolerance]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Live Attendance</h1>
          <p className="text-sm text-slate-500">Automatic face detection and attendance — no camera preview, no manual marking</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-white px-4 py-2 rounded-xl border border-slate-200 text-xs">
            <span className="font-semibold text-slate-700">Distance Threshold: {tolerance.toFixed(2)}</span>
            <input type="range" min="0.35" max="0.60" step="0.01" value={tolerance}
              onChange={(e) => setTolerance(parseFloat(e.target.value))}
              className="block w-32 accent-indigo-600 mt-1" />
          </div>

          <button
            onClick={running ? stopLive : startLive}
            disabled={starting}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition disabled:bg-slate-300 ${
              running ? "bg-rose-600 hover:bg-rose-700" : "bg-indigo-600 hover:bg-indigo-700"
            }`}
          >
            {running
              ? <><Square className="w-4 h-4" /> Stop Live Attendance</>
              : <><Play className="w-4 h-4" /> {starting ? "Starting…" : "Start Live Attendance"}</>}
          </button>
        </div>
      </div>

      {/* Hidden camera feed: required internally so frames can be captured
          for recognition, but never displayed on the main UI. */}
      <div className="absolute w-px h-px overflow-hidden opacity-0 pointer-events-none" aria-hidden="true">
        <video ref={videoRef} autoPlay playsInline muted />
        <canvas ref={captureCanvasRef} />
      </div>

      <div className="bg-white px-5 py-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-x-6 gap-y-2">
        <span className="flex items-center gap-2 font-semibold text-slate-900">
          <span className={`relative flex h-3 w-3`}>
            {running && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${running ? "bg-emerald-500" : "bg-slate-300"}`} />
          </span>
          {running ? "Live Detection Active" : "Live Detection Inactive"}
        </span>
        <span className="text-sm text-slate-500">Automatic Detection Enabled</span>
        {statusMsg && <span className="text-sm text-indigo-700 font-medium">{statusMsg}</span>}
      </div>

      {toastBanner && (
        <div className="bg-emerald-600 text-white px-5 py-3.5 rounded-xl shadow-lg flex items-center gap-3 font-medium">
          <CheckCircle className="w-5 h-5 shrink-0" />
          <span>{toastBanner}</span>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center gap-2 text-sm">
          <ShieldAlert className="w-4 h-4 shrink-0" /> {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
            <ScanFace className="w-4 h-4 text-indigo-600" /> Detected Attendance
          </div>
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
              <tr><th className="p-4">Name</th><th className="p-4">Roll Number</th><th className="p-4">Status</th><th className="p-4">Date</th><th className="p-4">Time</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {results.length === 0 ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">
                  {running ? "Scanning for faces — recognized students will appear here automatically." : "Click Start Live Attendance to begin automatic detection."}
                </td></tr>
              ) : results.map((r) => (
                <tr key={r.roll_number}>
                  <td className="p-4 font-medium text-slate-900">{r.name}</td>
                  <td className="p-4 font-mono font-semibold">{r.roll_number}</td>
                  <td className="p-4">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded text-white ${r.status === "Leave" ? "bg-amber-500" : "bg-emerald-600"}`}>{r.status}</span>
                  </td>
                  <td className="p-4">{r.date}</td>
                  <td className="p-4">{r.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <ScanFace className="w-4 h-4 text-indigo-600" /> Student Detected
          </h2>
          {!lastDetected ? (
            <p className="text-sm text-slate-400 py-8 text-center">
              {running ? "Waiting for a recognized student…" : "No student detected yet this session."}
            </p>
          ) : (
            <div className="p-4 rounded-xl border bg-emerald-50/60 border-emerald-200 space-y-1.5">
              <p className="text-sm text-slate-600">Name: <strong className="text-slate-900">{lastDetected.name}</strong></p>
              <p className="text-sm text-slate-600">Roll Number: <strong className="text-slate-900">{lastDetected.roll_number}</strong></p>
              <p className="text-sm text-slate-600">Status: <strong className={lastDetected.status === "Leave" ? "text-amber-600" : "text-emerald-700"}>{lastDetected.status}</strong></p>
              <p className="text-sm text-slate-600">Date: <strong className="text-slate-900">{lastDetected.date}</strong></p>
              <p className="text-sm text-slate-600">Time: <strong className="text-slate-900">{lastDetected.time}</strong></p>
              <p className="pt-1 text-xs font-medium text-indigo-700 flex items-center gap-1.5">
                <CheckCircle className="w-3.5 h-3.5" /> Attendance recorded successfully
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
