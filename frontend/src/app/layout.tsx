import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ToastProvider from "@/components/ToastProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AttendX | AI-Powered Smart Attendance Platform",
  description: "AttendX: recognize, verify, attend. Face recognition attendance for institutions.",
  icons: { icon: "/attendx-mark.png", apple: "/attendx-mark.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 text-slate-900 antialiased flex min-h-screen`}>
        <ToastProvider>
          <Sidebar />
          <main className="flex-1 min-w-0 p-4 pt-20 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
            {children}
          </main>
        </ToastProvider>
      </body>
    </html>
  );
}