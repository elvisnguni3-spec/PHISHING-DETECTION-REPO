import { useRef, useState } from "react";
import { Download, FileUp, ListChecks, ScanLine, UploadCloud } from "lucide-react";
import { isValidUrl, scanBatch } from "../api/scanService";
import { useScans } from "../context/ScanContext";
import RiskBadge from "../components/RiskBadge";
import { exportResultsToCsv } from "../utils/exportCsv";

const MAX_URLS = 50;

export default function BatchScan() {
  const { addScans } = useScans();
  const fileRef = useRef(null);
  const [text, setText] = useState("");
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const entries = String(reader.result).split(/[\n,;\r]+/).map((value) => value.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean).filter((value) => !/^url$/i.test(value));
      setText(entries.join("\n")); setError("");
    };
    reader.onerror = () => setError("We couldn’t read that file. Please try a .txt or .csv file.");
    reader.readAsText(file); event.target.value = "";
  };

  const runBatch = async () => {
    setError(""); setResults([]);
    const urls = [...new Set(text.split(/\r?\n/).map((value) => value.trim()).filter(Boolean))];
    if (!urls.length) return setError("Add at least one URL or upload a file first.");
    if (urls.length > MAX_URLS) return setError(`You can scan up to ${MAX_URLS} URLs at a time.`);
    const invalid = urls.filter((url) => !isValidUrl(url));
    if (invalid.length) return setError(`Please check these invalid URL${invalid.length > 1 ? "s" : ""}: ${invalid.slice(0, 2).join(", ")}${invalid.length > 2 ? " and more" : ""}`);
    setLoading(true); setProgress({ done: 0, total: urls.length });
    try { const data = await scanBatch(urls, (done, total) => setProgress({ done, total })); setResults(data); addScans(data); }
    catch (exception) { setError(exception.response?.data?.message || "The batch scan failed. Please try again."); }
    finally { setLoading(false); }
  };

  const counts = { Safe: results.filter((item) => item.level === "Safe").length, Suspicious: results.filter((item) => item.level === "Suspicious").length, Malicious: results.filter((item) => item.level === "Malicious").length };

  return (
    <div>
      <div className="mb-6 flex items-start gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><ListChecks className="h-5 w-5" /></div><div><h2 className="font-display text-lg font-extrabold text-slate-900">Bulk link check</h2><p className="mt-1 text-sm text-slate-500">Scan up to {MAX_URLS} links at once, one URL per line.</p></div></div>
      <textarea rows={7} value={text} onChange={(event) => setText(event.target.value)} placeholder={"https://example.com\nhttp://192.168.1.5/login\nhttps://account-verify.example.xyz"} className="focus-ring w-full resize-y rounded-xl border border-slate-200 bg-slate-50/60 p-4 font-mono text-sm leading-6 text-slate-700 placeholder:text-slate-400" />
      <div className="mt-2 flex items-center justify-between text-xs text-slate-400"><span>One address per line · duplicates are removed</span><span>{text.split(/\r?\n/).filter((line) => line.trim()).length} / {MAX_URLS}</span></div>
      <div className="mt-4 flex flex-wrap items-center gap-2.5"><input ref={fileRef} type="file" accept=".txt,.csv,text/plain,text/csv" onChange={handleFile} className="hidden" /><button onClick={() => fileRef.current?.click()} className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-bold text-slate-700 hover:bg-slate-50"><FileUp className="h-4 w-4 text-blue-600" />Upload .txt / .csv</button><button onClick={runBatch} disabled={loading} className="inline-flex h-10 items-center gap-2 rounded-xl bg-blue-700 px-5 text-sm font-bold text-white hover:bg-blue-800 disabled:opacity-60">{loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />Scanning {progress.done}/{progress.total}</> : <><ScanLine className="h-4 w-4" />Scan all links</>}</button>{results.length > 0 && <button onClick={() => exportResultsToCsv(results, "phishguard-batch-results.csv")} className="inline-flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-bold text-blue-700 hover:bg-blue-50"><Download className="h-4 w-4" />Export CSV</button>}</div>
      {error && <p role="alert" className="mt-3 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {loading && <div className="mt-5"><div className="mb-2 flex justify-between text-xs font-semibold text-slate-500"><span>Analysing links…</span><span>{Math.round((progress.done / (progress.total || 1)) * 100)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-blue-50"><div className="h-full rounded-full bg-blue-600 transition-all duration-300" style={{ width: `${(progress.done / (progress.total || 1)) * 100}%` }} /></div></div>}
      {results.length > 0 && <div className="mt-7"><div className="mb-4 grid grid-cols-3 gap-2.5">{[["Safe", "bg-emerald-50 text-emerald-700"], ["Suspicious", "bg-amber-50 text-amber-700"], ["Malicious", "bg-rose-50 text-rose-700"]].map(([label, style]) => <div key={label} className={`rounded-xl p-3 text-center ${style}`}><div className="font-display text-2xl font-extrabold">{counts[label]}</div><div className="mt-0.5 text-xs font-bold">{label}</div></div>)}</div><div className="overflow-x-auto rounded-xl border border-slate-100"><table className="w-full min-w-[520px] text-left text-sm"><thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-4 py-3">URL</th><th className="px-4 py-3">Risk score</th><th className="px-4 py-3">Assessment</th></tr></thead><tbody>{results.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="max-w-[280px] truncate px-4 py-3.5 text-slate-600" title={item.url}>{item.url}</td><td className="px-4 py-3.5 font-bold text-slate-800">{item.score}<span className="ml-1 text-xs font-normal text-slate-400">/ 100</span></td><td className="px-4 py-3.5"><RiskBadge score={item.score} level={item.level} /></td></tr>)}</tbody></table></div></div>}
      {!results.length && !loading && <div className="mt-6 flex items-center gap-3 rounded-xl bg-blue-50/70 p-4"><UploadCloud className="h-5 w-5 shrink-0 text-blue-600" /><p className="text-xs leading-relaxed text-slate-600">Tip: export scan results to share them with your security team. Uploaded files are processed in your browser.</p></div>}
    </div>
  );
}
