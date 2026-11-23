"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Cpu, Play, CheckCircle2 } from "lucide-react";

export default function TrainingPage() {
  const [status, setStatus] = useState<any>(null);
  const [tolerance, setTolerance] = useState(0.5);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = () => apiFetch("/model/status").then(setStatus);
  useEffect(() => { loadStatus(); }, []);

  const handleTrain = async () => {
    setTraining(true);
    setError(null);
    try {
      await apiFetch("/model/train", {
        method: "POST",
        body: JSON.stringify({ tolerance }),
      });
      await loadStatus();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">AI Model Training & Versioning</h1>
          <p className="text-sm text-slate-500">Generates 128-d ResNet embeddings and computes Leave-One-Out validation accuracy</p>
        </div>
        <button onClick={handleTrain} disabled={training}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white rounded-xl text-sm font-semibold">
          <Play className="w-4 h-4" /> {training ? "Extracting Embeddings..." : "Train New Model Version"}
        </button>
      </div>

      {error && <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>}

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <label className="text-sm font-semibold text-slate-700">
          Validation Distance Tolerance: <span className="text-indigo-600">{tolerance.toFixed(2)}</span>
        </label>
        <input type="range" min="0.35" max="0.60" step="0.01" value={tolerance}
          onChange={(e) => setTolerance(parseFloat(e.target.value))} className="w-full max-w-md accent-indigo-600 block" />
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 font-semibold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-600" /> Model Version History
        </div>
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="p-4">Version</th>
              <th className="p-4">Students</th>
              <th className="p-4">Total Encodings</th>
              <th className="p-4">LOOCV Accuracy</th>
              <th className="p-4">Threshold</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(status?.history || []).map((v: any) => (
              <tr key={v.id}>
                <td className="p-4 font-mono font-semibold">{v.version_tag}</td>
                <td className="p-4">{v.students_count}</td>
                <td className="p-4">{v.encodings_count}</td>
                <td className="p-4 font-bold text-indigo-600">{v.validation_accuracy}%</td>
                <td className="p-4">{v.tolerance_used}</td>
                <td className="p-4">
                  {v.is_active ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Active
                    </span>
                  ) : <span className="text-xs text-slate-400">Archived</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}