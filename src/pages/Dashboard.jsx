import { useState } from "react";
import { Activity, ArrowUpRight, Clock3, ExternalLink, LayoutDashboard, LogOut, Menu, ScanSearch, Shield, ShieldAlert, ShieldCheck, ShieldEllipsis, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useScans } from "../context/ScanContext";
import EducationAside from "../components/EducationAside";
import SingleScan from "./SingleScan";
import BatchScan from "./BatchScan";
import ScanHistory from "./ScanHistory";

const views = [
  { id: "single", label: "URL scanner", icon: ScanSearch },
  { id: "batch", label: "Bulk scan", icon: ShieldEllipsis },
  { id: "history", label: "Scan history", icon: Clock3 },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { history } = useScans();
  const [active, setActive] = useState("single");
  const [mobileMenu, setMobileMenu] = useState(false);
  const counts = { safe: history.filter((item) => item.level === "Safe").length, suspicious: history.filter((item) => item.level === "Suspicious").length, malicious: history.filter((item) => item.level === "Malicious").length };
  const cards = [
    { label: "Total scans", value: history.length, icon: Activity, style: "bg-blue-50 text-blue-700", detail: "Links analyzed" },
    { label: "Safe", value: counts.safe, icon: ShieldCheck, style: "bg-emerald-50 text-emerald-700", detail: "Low risk" },
    { label: "Suspicious", value: counts.suspicious, icon: ShieldAlert, style: "bg-amber-50 text-amber-700", detail: "Take a closer look" },
    { label: "Malicious", value: counts.malicious, icon: Shield, style: "bg-rose-50 text-rose-700", detail: "High risk detected" },
  ];
  const activeView = views.find((view) => view.id === active);
  const selectView = (id) => { setActive(id); setMobileMenu(false); };

  return (
    <div className="min-h-screen bg-[#f4f8ff] text-slate-800">
      <header className="sticky top-0 z-30 border-b border-blue-100/80 bg-white/95 backdrop-blur"><div className="mx-auto flex h-[68px] max-w-[1500px] items-center justify-between px-4 sm:px-6 lg:px-8"><a href="/dashboard" className="flex items-center gap-2.5"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-700 text-white"><ShieldCheck className="h-5 w-5" /></span><span className="font-display text-base font-extrabold tracking-tight text-slate-900">PhishGuard<span className="text-blue-700">.</span></span><span className="ml-1 hidden rounded-md bg-blue-50 px-2 py-1 text-[9px] font-extrabold uppercase tracking-widest text-blue-700 sm:inline">Security</span></a><div className="flex items-center gap-3"><div className="hidden text-right sm:block"><p className="text-xs font-bold text-slate-700">{user?.name || "Welcome"}</p><p className="text-[10px] text-slate-400">Personal workspace</p></div><div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-xs font-extrabold uppercase text-blue-800">{(user?.name || user?.email || "U").slice(0, 1)}</div><button onClick={logout} className="hidden items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 sm:flex"><LogOut className="h-3.5 w-3.5" /> Sign out</button><button onClick={() => setMobileMenu((value) => !value)} aria-label="Toggle navigation" className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 sm:hidden">{mobileMenu ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}</button></div></div>
        {mobileMenu && <div className="border-t border-slate-100 bg-white px-4 py-3 sm:hidden">{views.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => selectView(id)} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold ${active === id ? "bg-blue-50 text-blue-700" : "text-slate-600"}`}><Icon className="h-4 w-4" />{label}</button>)}<button onClick={logout} className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-600"><LogOut className="h-4 w-4" />Sign out</button></div>}
      </header>
      <div className="mx-auto grid max-w-[1500px] lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="sticky top-[68px] hidden h-[calc(100vh-68px)] flex-col border-r border-blue-100/80 bg-white px-4 py-7 lg:flex"><p className="mb-3 px-3 text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400">Workspace</p><nav className="space-y-1">{views.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => selectView(id)} className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-bold transition ${active === id ? "bg-blue-700 text-white shadow-md shadow-blue-700/15" : "text-slate-500 hover:bg-blue-50 hover:text-blue-700"}`}><Icon className={`h-[18px] w-[18px] ${active === id ? "text-blue-100" : "text-slate-400 group-hover:text-blue-600"}`} />{label}{active === id && <ArrowUpRight className="ml-auto h-3.5 w-3.5" />}</button>)}</nav><div className="mt-auto rounded-2xl border border-blue-100 bg-[#f2f7ff] p-4"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-blue-700 shadow-sm"><ShieldCheck className="h-5 w-5" /></div><h3 className="mt-3 text-sm font-extrabold text-slate-800">Safer clicks start here</h3><p className="mt-1 text-xs leading-relaxed text-slate-500">Check a link before you trust it.</p><button onClick={() => selectView("single")} className="mt-3 inline-flex items-center gap-1 text-xs font-extrabold text-blue-700">Scan a URL <ExternalLink className="h-3 w-3" /></button></div><p className="mt-5 px-3 text-[10px] text-slate-400">PhishGuard · Demo mode</p></aside>
        <main className="min-w-0 px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-9">
          <div className="mb-7 flex flex-wrap items-end justify-between gap-3"><div><div className="mb-2 flex items-center gap-1.5 text-[11px] font-bold text-blue-700"><LayoutDashboard className="h-3.5 w-3.5" /> SECURITY OVERVIEW <span className="text-blue-300">/</span> {activeView.label.toUpperCase()}</div><h1 className="font-display text-2xl font-extrabold tracking-tight text-slate-900 sm:text-[30px]">Good to see you, {user?.name || "there"} <span aria-hidden="true">👋</span></h1><p className="mt-1.5 text-sm text-slate-500">Stay one step ahead of suspicious links.</p></div><div className="hidden items-center gap-2 rounded-full border border-emerald-100 bg-white px-3 py-2 text-xs font-bold text-emerald-700 sm:inline-flex"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Protection active</div></div>
          <section aria-label="Scan statistics" className="mb-7 grid grid-cols-2 gap-3 xl:grid-cols-4">{cards.map(({ label, value, icon: Icon, style, detail }) => <div key={label} className="rounded-2xl border border-blue-100/80 bg-white p-4 card-shadow sm:p-5"><div className="flex items-start justify-between"><div><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-2 font-display text-3xl font-extrabold tracking-tight text-slate-900">{value}</p></div><span className={`flex h-9 w-9 items-center justify-center rounded-xl ${style}`}><Icon className="h-[18px] w-[18px]" /></span></div><p className="mt-2 text-[10px] text-slate-400">{detail}</p></div>)}</section>
          <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_310px]">
            <section className="min-w-0 overflow-hidden rounded-2xl border border-blue-100/80 bg-white card-shadow"><div className="flex gap-1 overflow-x-auto border-b border-slate-100 px-3 pt-3 sm:px-5">{views.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => selectView(id)} className={`flex shrink-0 items-center gap-2 border-b-2 px-3 py-3 text-xs font-bold transition sm:px-4 ${active === id ? "border-blue-700 text-blue-700" : "border-transparent text-slate-400 hover:text-slate-700"}`}><Icon className="h-4 w-4" />{label}</button>)}</div><div className="p-4 sm:p-6">{active === "single" && <SingleScan />}{active === "batch" && <BatchScan />}{active === "history" && <ScanHistory />}</div></section>
            <EducationAside />
          </div>
          <footer className="mt-8 flex flex-wrap items-center justify-between gap-2 border-t border-blue-100/80 pt-5 text-[11px] text-slate-400"><span>PhishGuard helps you make safer choices online.</span><span className="inline-flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-blue-500" /> Stay curious. Stay safe.</span></footer>
        </main>
      </div>
    </div>
  );
}
