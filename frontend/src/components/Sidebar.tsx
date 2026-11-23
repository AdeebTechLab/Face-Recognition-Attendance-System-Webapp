"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, UserPlus, Users, FolderKanban, Cpu,
  ScanFace, History, BarChart3, FileSpreadsheet, Settings
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/live", label: "Live Recognition", icon: ScanFace },
  { href: "/register", label: "Student Registration", icon: UserPlus },
  { href: "/students", label: "Student Management", icon: Users },
  { href: "/dataset", label: "Dataset Management", icon: FolderKanban },
  { href: "/training", label: "Model Training", icon: Cpu },
  { href: "/attendance", label: "Attendance History", icon: History },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/reports", label: "Reports & Exports", icon: FileSpreadsheet },
  { href: "/settings", label: "Settings & Logs", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-950 text-slate-200 flex flex-col min-h-screen border-r border-slate-800 shrink-0">
      <div className="p-6 flex items-center gap-3 border-b border-slate-800/80">
        <div className="h-11 w-11 rounded-xl bg-white flex items-center justify-center overflow-hidden shadow-lg shadow-blue-500/20">
          <Image src="/attendx-mark.png" alt="AttendX logo" width={44} height={44} priority />
        </div>
        <div>
          <h1 className="font-extrabold text-white tracking-tight text-lg leading-tight">Attend<span className="text-sky-400">X</span></h1>
          <p className="text-[11px] text-slate-400">Recognize. Verify. Attend.</p>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-900"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 m-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
        <p className="font-semibold text-slate-200">Privacy Architecture</p>
        <p className="mt-1">128-d encodings stored in isolated private storage.</p>
      </div>
    </aside>
  );
}