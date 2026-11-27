"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, UserPlus, Users, FolderKanban, Cpu,
  ScanFace, History, BarChart3, Settings, Menu, X
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
  { href: "/settings", label: "Settings & Logs", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <>
      <div className="md:hidden fixed top-0 inset-x-0 z-40 h-14 px-4 flex items-center gap-3 bg-slate-950 text-white border-b border-slate-800">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="p-2 -ml-2 rounded-lg hover:bg-slate-900"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center overflow-hidden">
          <Image src="/attendx-mark.png" alt="AttendX logo" width={32} height={32} priority />
        </div>
        <span className="font-extrabold tracking-tight">
          Attend<span className="text-sky-400">X</span>
        </span>
      </div>

      {open && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/50"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-64 shrink-0 bg-slate-950 text-slate-200 flex flex-col min-h-screen overflow-y-auto border-r border-slate-800 transform transition-transform duration-300 ${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        <div className="p-6 flex items-center gap-3 border-b border-slate-800/80">
          <div className="h-11 w-11 rounded-xl bg-white flex items-center justify-center overflow-hidden shadow-lg shadow-blue-500/20">
            <Image src="/attendx-mark.png" alt="AttendX logo" width={44} height={44} priority />
          </div>
          <div>
            <h1 className="font-extrabold text-white tracking-tight text-lg leading-tight">Attend<span className="text-sky-400">X</span></h1>
            <p className="text-[11px] text-slate-400">Recognize. Verify. Attend.</p>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="md:hidden ml-auto p-2 rounded-lg hover:bg-slate-900"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
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
    </>
  );
}
