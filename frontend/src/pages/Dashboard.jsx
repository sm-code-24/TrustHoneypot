import { useState } from "react";
import { Routes, Route, NavLink, useNavigate } from "react-router-dom";
import {
  Shield,
  MessageSquare,
  BarChart3,
  GitBranch,
  Send,
  Settings,
  Users,
  Menu,
  X,
  ChevronLeft,
} from "lucide-react";

import SessionView from "./SessionView";
import IntelligenceView from "./IntelligenceView";
import PatternsView from "./PatternsView";
import CallbacksView from "./CallbacksView";
import SettingsView from "./SettingsView";
import AboutView from "./AboutView";

const NAV_ITEMS = [
  { to: "session", icon: MessageSquare, label: "Session" },
  { to: "intelligence", icon: BarChart3, label: "Intelligence" },
  { to: "patterns", icon: GitBranch, label: "Patterns" },
  { to: "callbacks", icon: Send, label: "Callbacks" },
  { to: "settings", icon: Settings, label: "Settings" },
  { to: "about", icon: Users, label: "About" },
];

export default function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const year = new Date().getFullYear();

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
      isActive ?
        "bg-blue-500/10 text-blue-400 glow-border"
      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
    }`;

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 pt-5 pb-6">
        <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
          <Shield size={16} className="text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-white tracking-tight leading-none">
            Trust<span className="text-gradient">Honeypot</span>
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-0.5">
            COMMAND CENTER
          </span>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={navLinkClass}
            onClick={() => setSidebarOpen(false)}>
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Back to landing */}
      <div className="px-3 pb-4">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-all">
          <ChevronLeft size={14} />
          Back to Home
        </button>
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-surface-950 overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-56 border-r border-slate-800/60 bg-gradient-to-b from-surface-800/50 to-surface-950/90 backdrop-blur-sm flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-60 bg-gradient-to-b from-surface-800/90 to-surface-950 border-r border-slate-800/60 flex flex-col transform transition-transform duration-300 ease-in-out md:hidden ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}>
        <div className="absolute top-3 right-3">
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>
        <SidebarContent />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top header */}
        <header className="flex items-center justify-between px-4 md:px-6 h-12 border-b border-slate-800/50 bg-surface-950/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 md:hidden">
              <Menu size={18} />
            </button>
            <span className="text-sm font-medium text-slate-300 hidden sm:block">
              TrustHoneypot
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-xs text-emerald-400 font-medium">LIVE</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              AI Impact Buildathon — PS-2
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-grid">
          <Routes>
            <Route index element={<SessionView />} />
            <Route path="session" element={<SessionView />} />
            <Route path="intelligence" element={<IntelligenceView />} />
            <Route path="patterns" element={<PatternsView />} />
            <Route path="callbacks" element={<CallbacksView />} />
            <Route path="settings" element={<SettingsView />} />
            <Route path="about" element={<AboutView />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="flex items-center justify-center h-9 border-t border-slate-800/40 bg-surface-950/90 flex-shrink-0">
          <p className="text-[11px] text-slate-500">
            &copy; {year}{" "}
            <span className="text-slate-400 font-medium">200 Hustlers</span>
            {" — "}TrustHoneypot — Made for AI Impact Buildathon PS-2
          </p>
        </footer>
      </div>
    </div>
  );
}
