"use client";
import { useState } from "react";
import { apiDownload } from "@/lib/api";
import { useToast } from "@/components/ToastProvider";
import { FileSpreadsheet, FileText } from "lucide-react";

export default function ReportsPage() {
  const { toast } = useToast();
  const [date, setDate] = useState(() => new Date().toLocaleDateString("en-CA")); // YYYY-MM-DD, local time
  const [busy, setBusy] = useState<"csv" | "pdf" | null>(null);

  const download = async (format: "csv" | "pdf") => {
    setBusy(format);
    try {
      await apiDownload(`/attendance/export?format=${format}&target_date=${date}`, `attendance_${date}.${format}`);
      toast(`${format.toUpperCase()} report downloaded`);
    } catch (e: any) {
      toast(e.message, "error");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reports & Exports</h1>
        <p className="text-sm text-slate-500">Download the full daily roster, including absentees</p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5 max-w-xl">
        <div>
          <label className="block text-xs font-semibold text-slate-600 mb-1">Report date</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm" />
        </div>
        <div className="flex gap-3">
          <button disabled={!date || busy !== null} onClick={() => download("csv")}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold">
            <FileSpreadsheet className="w-4 h-4" /> {busy === "csv" ? "Preparing…" : "Download CSV"}
          </button>
          <button disabled={!date || busy !== null} onClick={() => download("pdf")}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-sm font-semibold">
            <FileText className="w-4 h-4" /> {busy === "pdf" ? "Preparing…" : "Download PDF"}
          </button>
        </div>
      </div>
    </div>
  );
}
