"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Users, UserCheck, UserX, Percent, Cpu, Clock } from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function DashboardPage() {
  const [report, setReport] = useState<any>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiFetch("/attendance/daily-report"),
      apiFetch("/model/status"),
      apiFetch("/attendance"),
    ])
      .then(([rep, mod, att]) => {
        setReport(rep);
        setModelStatus(mod.active_model);
        setRecentLogs(att.slice(0, 6));
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-64 bg-slate-200 rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-28 bg-slate-200 rounded-2xl" />)}
        </div>
        <div className="h-80 bg-slate-200 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Institutional Attendance Overview</h1>
          <p className="text-sm text-slate-500">Live biometric metrics synchronized with SQL database</p>
        </div>
        <div className="flex items-center gap-3 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm">
          <Cpu className="w-4 h-4 text-indigo-600" />
          <div className="text-xs">
            <span className="font-semibold text-slate-800">
              {modelStatus ? `Model ${modelStatus.version_tag} Active` : "No Model Trained"}
            </span>
            <span className="text-slate-400 block">
              {modelStatus ? `Trained: ${new Date(modelStatus.trained_at).toLocaleDateString()}` : "Train model to begin"}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Active Students" value={report?.total_students ?? 0} icon={Users} accent="text-indigo-600 bg-indigo-50" />
        <StatCard title="Present Today" value={report?.present_count ?? 0} icon={UserCheck} accent="text-emerald-600 bg-emerald-50" />
        <StatCard title="Absent Today" value={report?.absent_count ?? 0} icon={UserX} accent="text-rose-600 bg-rose-50" />
        <StatCard title="Attendance Rate" value={`${report?.attendance_percentage ?? 0}%`} icon={Percent} accent="text-blue-600 bg-blue-50" />
      </div>

      {/* Charts & Recent Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-4">7-Day Attendance Trend</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={report?.weekly_trend || []}>
                <defs>
                  <linearGradient id="colorPresent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey="present" stroke="#4f46e5" strokeWidth={2.5} fillOpacity={1} fill="url(#colorPresent)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Recent Live Check-Ins</h2>
          {recentLogs.length === 0 ? (
            <p className="text-sm text-slate-400 py-12 text-center">No biometric check-ins recorded yet.</p>
          ) : (
            <div className="space-y-3">
              {recentLogs.map((log: any) => (
                <div key={log.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{log.student_name}</p>
                    <p className="text-xs text-slate-500">{log.roll_number} • {log.department}</p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md">
                      <Clock className="w-3 h-3" /> {log.check_in_time}
                    </span>
                    <p className="text-[11px] text-slate-400 mt-0.5">dist: {log.face_distance}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, accent }: any) {
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
      <div>
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
      </div>
      <div className={`p-3 rounded-xl ${accent}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}