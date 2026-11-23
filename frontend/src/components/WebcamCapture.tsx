"use client";
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

export type WebcamHandle = { capture: (quality?: number) => string | null };

/** Reusable webcam preview. Call ref.current.capture() to get a JPEG data URL. */
const WebcamCapture = forwardRef<WebcamHandle, { onError?: (msg: string) => void; className?: string }>(
  function WebcamCapture({ onError, className }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [ready, setReady] = useState(false);

    useEffect(() => {
      let stream: MediaStream | null = null;
      navigator.mediaDevices
        ?.getUserMedia({ video: { width: 640, height: 480 } })
        .then((s) => {
          stream = s;
          if (videoRef.current) videoRef.current.srcObject = s;
          setReady(true);
        })
        .catch(() => onError?.("Camera permission denied. Enable webcam over HTTPS/localhost."));
      return () => stream?.getTracks().forEach((t) => t.stop());
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useImperativeHandle(ref, () => ({
      capture: (quality = 0.9) => {
        const v = videoRef.current;
        const c = canvasRef.current;
        if (!ready || !v || !c || v.videoWidth === 0) return null;
        c.width = v.videoWidth;
        c.height = v.videoHeight;
        c.getContext("2d")?.drawImage(v, 0, 0);
        return c.toDataURL("image/jpeg", quality);
      },
    }));

    return (
      <>
        <video ref={videoRef} autoPlay playsInline muted className={className ?? "w-full h-full object-cover"} />
        <canvas ref={canvasRef} className="hidden" />
      </>
    );
  }
);

export default WebcamCapture;
