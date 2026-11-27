"use client";
import { useEffect, useState } from "react";
import { apiFetch, apiDownload } from "@/lib/api";
import { useToast } from "@/components/ToastProvider";
import { History, Download, ChevronDown, FileSpreadsheet, FileText, CalendarDays, UserCheck } from "lucide-react";

function localToday(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function localMonth(): string {
  return localToday().slice(0, 7);
}

export default function AttendanceHistoryPage() {
  const { toast } = useToast();
  const [records, setRecords] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [date, setDate] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Mark Leave form
  const [leaveRoll, setLeaveRoll] = useState("");
  const [leaveDate, setLeaveDate] = useState(localToday());
  const [leaveBusy, setLeaveBusy] = useState(false);

  // Monthly Register month
  const [month, setMonth] = useState(localMonth());

  useEffect(() => {
    apiFetch("/students")
      .then((s) => setStudents(Array.isArray(s) ? s : []))
      .catch(() => setStudents([]));
  }, []);

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
  }, [date, search, refreshKey]);

  const downloadMonthly = async (format: "xlsx" | "pdf") => {
    setDownloading(`monthly-${format}`);
    setMenuOpen(false);
    try {
      await apiDownload(
        `/attendance/monthly-register?month=${month}&format=${format}`,
        `monthly_attendance_register_${month}.${format}`
      );
      toast(`Monthly Register (${format === "xlsx" ? "Excel" : "PDF"}) downloaded`);
    } catch (e: any) {
      toast(e.message || "Download failed", "error");
    } finally {
      setDownloading(null);
    }
  };

  const markLeave = async () => {
    if (!leaveRoll) {
      toast("Select a student first", "error");
      return;
    }
    if (!leaveDate) {
      toast("Select the leave date", "error");
      return;
    }
    setLeaveBusy(true);
    try {
      await apiFetch("/attendance/leave", {
        method: "POST",
        body: JSON.stringify({ roll_number: leaveRoll, target_date: leaveDate }),
      });
      const student = students.find((s) => s.roll_number === leaveRoll);
      toast(`Leave marked: ${student ? student.name : leaveRoll} on ${leaveDate}`);
      setRefreshKey((k) => k + 1);
    } catch (e: any) {
      toast(e.message || "Could not mark leave", "error");
    } finally {
      setLeaveBusy(false);
    }
  };

  const removeLeave = async (r: any) => {
    setLeaveBusy(true);
    try {
      const params = new URLSearchParams({ roll_number: r.roll_number, target_date: r.attendance_date });
      await apiFetch(`/attendance/leave?${params.toString()}`, { method: "DELETE" });
      toast(`Leave removed: ${r.student_name} on ${r.attendance_date}`);
      setRefreshKey((k) => k + 1);
    } catch (e: any) {
      toast(e.message || "Could not remove leave", "error");
    } finally {
      setLeaveBusy(false);
    }
  };

  const isLeave = (r: any) => r.verification_source === "LEAVE";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Attendance History</h1>
          <p className="text-sm text-slate-500">Every verified check-in and leave record, newest first</p>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <CalendarDays className="w-4 h-4 text-indigo-600" />
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="px-3 py-2.5 rounded-xl border border-slate-300 text-sm bg-white"
              title="Month for the Monthly Register download"
            />
          </label>
          <div className="relative">
            <button
              onClick={() => setMenuOpen((o) => !o)}
              disabled={downloading !== null}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300"
            >
              <Download className="w-4 h-4" />
              {downloading ? "Preparing…" : "Download"}
              <ChevronDown className="w-4 h-4" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 z-20 mt-2 w-72 max-w-[calc(100vw-2rem)] bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
                  <div className="px-4 pt-3 pb-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                    Monthly Register — {month}
                  </div>
                  <button
                    onClick={() => downloadMonthly("xlsx")}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 text-left"
                  >
                    <FileSpreadsheet className="w-4 h-4 text-emerald-600" /> Monthly Register — Excel
                  </button>
                  <button
                    onClick={() => downloadMonthly("pdf")}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 text-left"
                  >
                    <FileText className="w-4 h-4 text-rose-600" /> Monthly Register — PDF
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Mark Leave */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
        <div className="font-semibold text-slate-900 flex items-center gap-2 mb-3">
          <UserCheck className="w-4 h-4 text-amber-500" /> Mark Leave
          <span className="text-xs font-normal text-slate-400">A student on leave is not counted absent, and cannot be marked present the same day.</span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={leaveRoll}
            onChange={(e) => setLeaveRoll(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white min-w-64"
          >
            <option value="">Select student…</option>
            {students.map((s) => (
              <option key={s.id} value={s.roll_number}>
                {s.name} — {s.roll_number}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={leaveDate}
            onChange={(e) => setLeaveDate(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white"
          />
          <button
            onClick={markLeave}
            disabled={leaveBusy}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition bg-amber-500 hover:bg-amber-600 disabled:bg-slate-300"
          >
            {leaveBusy ? "Working…" : "Mark Leave"}
          </button>
        </div>
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

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-x-auto">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-600" /> {records.length} records
        </div>
        <table className="w-full min-w-[640px] text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr><th className="p-4">Date</th><th className="p-4">Status</th><th className="p-4">Time</th><th className="p-4">Roll</th><th className="p-4">Name</th><th className="p-4">Department</th><th className="p-4">Distance</th><th className="p-4">Action</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={8} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : records.length === 0 ? (
              <tr><td colSpan={8} className="p-8 text-center text-slate-400">No records found.</td></tr>
            ) : records.map((r) => (
              <tr key={r.id}>
                <td className="p-4">{r.attendance_date}</td>
                <td className="p-4">
                  {isLeave(r) ? (
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-500 text-white">Leave</span>
                  ) : (
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-600 text-white">Present</span>
                  )}
                </td>
                <td className="p-4">{isLeave(r) ? "—" : r.check_in_time}</td>
                <td className="p-4 font-mono font-semibold">{r.roll_number}</td>
                <td className="p-4">{r.student_name}</td>
                <td className="p-4">{r.department}</td>
                <td className="p-4">{isLeave(r) ? "—" : r.face_distance}</td>
                <td className="p-4">
                  {isLeave(r) && (
                    <button
                      onClick={() => removeLeave(r)}
                      disabled={leaveBusy}
                      className="text-xs font-semibold text-amber-700 hover:underline disabled:text-slate-300"
                    >
                      Remove Leave
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}