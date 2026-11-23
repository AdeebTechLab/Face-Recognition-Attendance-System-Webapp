"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Settings } from "lucide-react";

const LEVEL_STYLE: Record<string, string> = {
  INFO: "bg-blue-50 text-blue-700",
  WARNING: "bg-amber-50 text-amber-700",
  ERROR: "bg-rose-50 text-rose-700",
};

export default function SettingsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/system/logs")
      .then(setLogs)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings & System Logs</h1>
        <p className="text-sm text-slate-500">50 most recent backend events</p>
      </div>
      {error && <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>}

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <Settings className="w-4 h-4 text-indigo-600" /> Event Log
        </div>
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr><th className="p-4">Time (UTC)</th><th className="p-4">Level</th><th className="p-4">Module</th><th className="p-4">Message</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={4} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan={4} className="p-8 text-center text-slate-400">No events yet.</td></tr>
            ) : logs.map((l) => (
              <tr key={l.id}>
                <td className="p-4 whitespace-nowrap text-slate-500">{String(l.created_at).replace("T", " ").slice(0, 19)}</td>
                <td className="p-4"><span className={`text-xs font-semibold px-2 py-0.5 rounded ${LEVEL_STYLE[l.level] || ""}`}>{l.level}</span></td>
                <td className="p-4 font-mono text-xs">{l.module}</td>
                <td className="p-4">{l.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
