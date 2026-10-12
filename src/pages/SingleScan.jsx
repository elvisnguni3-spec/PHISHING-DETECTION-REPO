import { useState } from "react";
import { ArrowRight, ClipboardPaste, Link2, ScanSearch, ShieldCheck } from "lucide-react";
import { isValidUrl, scanSingle } from "../api/scanService";
import { useScans } from "../context/ScanContext";
import ScanResultCard from "../components/ScanResultCard";

export default function SingleScan() {
  const { addScans } = useScans();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault(); setError(""); setResult(null);
    if (!isValidUrl(url)) return setError("Enter a valid web address, such as example.com or https://example.com.");
    setLoading(true);
    try { const data = await scanSingle(url); setResult(data); addScans([data]); }
    catch (exception) { setError(exception.response?.data?.message || "The scan could not be completed. Please try again."); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="mb-6 flex items-start gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><ScanSearch className="h-5 w-5" /></div><div><h2 className="font-display text-lg font-extrabold text-slate-900">Check a link</h2><p className="mt-1 text-sm text-slate-500">Paste a URL below to see if it’s safe to visit.</p></div></div>
      <form onSubmit={submit}>
        <label htmlFor="single-url" className="mb-2 block text-xs font-bold uppercase tracking-wider text-slate-500">Website URL</label>
        <div className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-slate-50/70 p-2 sm:flex-row sm:items-center"><div className="flex min-w-0 flex-1 items-center gap-2 px-2"><Link2 className="h-4 w-4 shrink-0 text-blue-500" /><input id="single-url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="Paste a suspicious link here…" className="h-11 min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400" /></div><button disabled={loading} className="flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 text-sm font-bold text-white shadow-sm transition hover:bg-blue-800 disabled:opacity-60">{loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />Checking link…</> : <>Scan link <ArrowRight className="h-4 w-4" /></>}</button></div>
      </form>
      {error && <p role="alert" className="mt-3 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {!result && !loading && <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dashed border-blue-200 bg-blue-50/45 px-4 py-3.5"><div className="flex items-center gap-2 text-xs text-slate-600"><ShieldCheck className="h-4 w-4 text-blue-600" /><span>We’ll look for common signs of phishing and suspicious domains.</span></div><button type="button" onClick={() => setUrl("https://accounts-verify.example-login.xyz/secure")} className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-900"><ClipboardPaste className="h-3.5 w-3.5" /> Try a sample</button></div>}
      {loading && <div className="mt-7 animate-pulse rounded-2xl border border-blue-100 bg-blue-50/50 p-8"><div className="mx-auto h-3 w-36 rounded bg-blue-100" /><div className="mx-auto mt-4 h-16 w-16 rounded-full bg-blue-100" /><p className="mt-4 text-center text-sm font-medium text-slate-500">Checking domain patterns and URL signals…</p></div>}
      {result && <ScanResultCard result={result} />}
    </div>
  );
}
