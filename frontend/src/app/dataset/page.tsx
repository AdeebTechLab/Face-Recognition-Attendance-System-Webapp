"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { FolderKanban, CheckCircle2 } from "lucide-react";

export default function DatasetPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/dataset/summary")
      .then(setRows)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const ready = rows.filter((r) => r.ready_for_training).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dataset Management</h1>
        <p className="text-sm text-slate-500">
          {ready} of {rows.length} active students have the 10+ photos required for training
        </p>
      </div>
      {error && <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>}

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <FolderKanban className="w-4 h-4 text-indigo-600" /> Face Sample Inventory
        </div>
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr><th className="p-4">Roll</th><th className="p-4">Name</th><th className="p-4">Department</th><th className="p-4 w-56">Photos</th><th className="p-4">Training</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={5} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={5} className="p-8 text-center text-slate-400">No active students.</td></tr>
            ) : rows.map((r) => (
              <tr key={r.id}>
                <td className="p-4 font-mono font-semibold">{r.roll_number}</td>
                <td className="p-4">{r.name}</td>
                <td className="p-4">{r.department}</td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className={`h-full ${r.ready_for_training ? "bg-emerald-500" : "bg-amber-500"}`}
                        style={{ width: `${Math.min(100, (r.photo_count / 10) * 100)}%` }} />
                    </div>
                    <span className="text-xs text-slate-600 w-10 text-right">{r.photo_count}/10</span>
                  </div>
                </td>
                <td className="p-4">
                  {r.ready_for_training ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                    </span>
                  ) : <span className="text-xs text-amber-600">Needs {10 - r.photo_count} more</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
