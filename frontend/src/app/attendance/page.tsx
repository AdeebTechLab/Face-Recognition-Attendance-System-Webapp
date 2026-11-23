"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { History } from "lucide-react";

export default function AttendanceHistoryPage() {
  const [records, setRecords] = useState<any[]>([]);
  const [date, setDate] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (date) params.set("target_date", date);
    if (search.trim()) params.set("search", search.trim());
    const qs = params.toString();
    // debounce typing in the search box
    const t = setTimeout(() => {
      setLoading(true);
      apiFetch(`/attendance${qs ? `?${qs}` : ""}`)
        .then((r) => { setRecords(r); setError(null); })
        .catch((e: Error) => setError(e.message))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [date, search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Attendance History</h1>
        <p className="text-sm text-slate-500">Every verified check-in, newest first</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white" />
        <input placeholder="Search name or roll number" value={search} onChange={(e) => setSearch(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white w-72" />
        {(date || search) && (
          <button onClick={() => { setDate(""); setSearch(""); }} className="text-sm text-indigo-600 hover:underline">Clear</button>
        )}
      </div>

      {error && <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>}

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-600" /> {records.length} records
        </div>
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr><th className="p-4">Date</th><th className="p-4">Time</th><th className="p-4">Roll</th><th className="p-4">Name</th><th className="p-4">Department</th><th className="p-4">Distance</th><th className="p-4">Source</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={7} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : records.length === 0 ? (
              <tr><td colSpan={7} className="p-8 text-center text-slate-400">No records found.</td></tr>
            ) : records.map((r) => (
              <tr key={r.id}>
                <td className="p-4">{r.attendance_date}</td>
                <td className="p-4">{r.check_in_time}</td>
                <td className="p-4 font-mono font-semibold">{r.roll_number}</td>
                <td className="p-4">{r.student_name}</td>
                <td className="p-4">{r.department}</td>
                <td className="p-4">{r.face_distance}</td>
                <td className="p-4 text-xs text-slate-500">{r.verification_source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
