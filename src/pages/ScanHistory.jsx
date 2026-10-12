import { useMemo, useState } from "react";
import { Download, Search, Trash2 } from "lucide-react";
import { useScans } from "../context/ScanContext";
import RiskBadge from "../components/RiskBadge";
import { exportResultsToCsv } from "../utils/exportCsv";

export default function ScanHistory() {
  const { history, clearHistory } = useScans();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All results");
  const filtered = useMemo(() => history.filter((item) => item.url.toLowerCase().includes(query.toLowerCase()) && (filter === "All results" || item.level === filter)), [history, query, filter]);
  const clear = () => { if (window.confirm("Clear all saved scan history? This cannot be undone.")) clearHistory(); };

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-display text-lg font-extrabold text-slate-900">Your scan history</h2><p className="mt-1 text-sm text-slate-500">{history.length} {history.length === 1 ? "link" : "links"} checked so far</p></div><div className="flex gap-2"><button disabled={!filtered.length} onClick={() => exportResultsToCsv(filtered, "phishguard-scan-history.csv")} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 px-3 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-40"><Download className="h-3.5 w-3.5" />Export</button><button disabled={!history.length} onClick={clear} className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-rose-100 px-3 text-xs font-bold text-rose-600 hover:bg-rose-50 disabled:opacity-40"><Trash2 className="h-3.5 w-3.5" />Clear</button></div></div>
      <div className="mb-4 flex flex-col gap-2 sm:flex-row"><label className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search scanned URLs…" className="focus-ring h-10 w-full rounded-xl border border-slate-200 pl-9 pr-3 text-sm outline-none placeholder:text-slate-400" /></label><select value={filter} onChange={(event) => setFilter(event.target.value)} className="focus-ring h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none"><option>All results</option><option>Safe</option><option>Suspicious</option><option>Malicious</option></select></div>
      {filtered.length === 0 ? <div className="rounded-2xl border border-dashed border-blue-200 bg-blue-50/40 px-6 py-12 text-center"><div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-white text-blue-600"><Search className="h-5 w-5" /></div><h3 className="mt-3 text-sm font-bold text-slate-700">{history.length ? "No matching scans" : "Your history is clear"}</h3><p className="mt-1 text-xs text-slate-500">{history.length ? "Try another search or filter." : "Links you scan will appear here for easy reference."}</p></div> : <div className="overflow-x-auto rounded-xl border border-slate-100"><table className="w-full min-w-[620px] text-left text-sm"><thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-4 py-3">Scanned link</th><th className="px-4 py-3">Score</th><th className="px-4 py-3">Result</th><th className="px-4 py-3">Checked at</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="max-w-[280px] truncate px-4 py-3.5 text-slate-600" title={item.url}>{item.url}</td><td className="px-4 py-3.5 font-bold text-slate-800">{item.score}<span className="ml-1 text-xs font-normal text-slate-400">/ 100</span></td><td className="px-4 py-3.5"><RiskBadge score={item.score} level={item.level} /></td><td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-500">{new Date(item.scannedAt).toLocaleString()}</td></tr>)}</tbody></table></div>}
    </div>
  );
}
