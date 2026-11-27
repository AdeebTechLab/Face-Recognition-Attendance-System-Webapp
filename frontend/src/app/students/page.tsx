"use client";
import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { useToast } from "@/components/ToastProvider";
import { Users, UserX, RotateCcw } from "lucide-react";

export default function StudentsPage() {
  const { toast } = useToast();
  const [students, setStudents] = useState<any[]>([]);
  const [showInactive, setShowInactive] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    apiFetch(`/students?include_inactive=${showInactive}`)
      .then(setStudents)
      .catch((e: Error) => toast(e.message, "error"))
      .finally(() => setLoading(false));
  }, [showInactive, toast]);

  useEffect(() => { load(); }, [load]);

  const deactivate = async (s: any) => {
    if (!confirm(`Deactivate ${s.name}? Attendance history is preserved.`)) return;
    try {
      await apiFetch(`/students/${s.id}`, { method: "DELETE" });
      toast(`${s.name} deactivated`);
      load();
    } catch (e: any) { toast(e.message, "error"); }
  };

  const reactivate = async (s: any) => {
    try {
      await apiFetch(`/students/${s.id}`, { method: "PUT", body: JSON.stringify({ is_active: true }) });
      toast(`${s.name} reactivated`);
      load();
    } catch (e: any) { toast(e.message, "error"); }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Student Management</h1>
          <p className="text-sm text-slate-500">Soft-delete keeps historical attendance intact</p>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
          Show inactive
        </label>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-x-auto">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <Users className="w-4 h-4 text-indigo-600" /> {students.length} students
        </div>
        <table className="w-full min-w-[640px] text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="p-4">Roll</th><th className="p-4">Name</th><th className="p-4">Email</th>
              <th className="p-4">Department</th><th className="p-4">Photos</th><th className="p-4">Status</th>
              <th className="p-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td colSpan={7} className="p-8 text-center text-slate-400">Loading…</td></tr>
            ) : students.length === 0 ? (
              <tr><td colSpan={7} className="p-8 text-center text-slate-400">No students registered yet.</td></tr>
            ) : students.map((s) => (
              <tr key={s.id}>
                <td className="p-4 font-mono font-semibold">{s.roll_number}</td>
                <td className="p-4">{s.name}</td>
                <td className="p-4 text-slate-500">{s.email}</td>
                <td className="p-4">{s.department}</td>
                <td className="p-4">{s.photo_count}</td>
                <td className="p-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${s.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                    {s.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="p-4 text-right">
                  {s.is_active ? (
                    <button onClick={() => deactivate(s)} className="inline-flex items-center gap-1 text-xs text-rose-600 hover:underline">
                      <UserX className="w-3.5 h-3.5" /> Deactivate
                    </button>
                  ) : (
                    <button onClick={() => reactivate(s)} className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline">
                      <RotateCcw className="w-3.5 h-3.5" /> Reactivate
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
