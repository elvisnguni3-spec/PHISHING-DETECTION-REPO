import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, Check, Eye, EyeOff, Link2, LockKeyhole, Mail, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Enter a valid email address.");
    if (password.length < 6) return setError("Your password must be at least 6 characters.");
    setLoading(true);
    try { await login(email, password); navigate("/dashboard"); }
    catch (exception) { setError(exception.response?.data?.detail || exception.response?.data?.message || exception.message || "Unable to sign in. Please try again."); }
    finally { setLoading(false); }
  };

  return (
    <main className="min-h-screen bg-white lg:grid lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden min-h-screen overflow-hidden bg-[#0b3677] px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
        <div className="absolute inset-0 soft-grid opacity-[0.16]" /><div className="absolute -right-32 top-24 h-[500px] w-[500px] rounded-full border border-white/10" /><div className="absolute -right-20 top-36 h-[360px] w-[360px] rounded-full border border-white/10" />
        <Brand light />
        <div className="relative z-10 max-w-xl pb-12">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-blue-100"><Sparkles className="h-3.5 w-3.5" /> A clearer way to browse safely</div>
          <h1 className="font-display text-5xl font-extrabold leading-[1.12] tracking-tight xl:text-6xl">Know the link.<br /><span className="text-blue-300">Trust the click.</span></h1>
          <p className="mt-6 max-w-md text-base leading-7 text-blue-100/80">Check suspicious URLs in seconds with a friendly, easy-to-understand risk analysis.</p>
          <div className="mt-10 space-y-4">{["Instant URL risk insights", "Bulk scan links in one go", "Your scan history, always at hand"].map((item) => <div key={item} className="flex items-center gap-3 text-sm font-medium text-blue-50"><span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-400/20"><Check className="h-3 w-3 text-blue-200" /></span>{item}</div>)}</div>
        </div>
        <p className="relative z-10 text-xs text-blue-200/60">© 2026 PhishGuard · Stay one step ahead</p>
      </section>
      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-10">
        <div className="w-full max-w-[420px]">
          <div className="mb-12 lg:hidden"><Brand /></div>
          <div className="mb-8"><div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><ShieldCheck className="h-6 w-6" /></div><p className="mb-2 text-xs font-extrabold uppercase tracking-[0.18em] text-blue-600">Welcome back</p><h2 className="font-display text-3xl font-extrabold tracking-tight text-slate-900">Sign in to PhishGuard</h2><p className="mt-2 text-sm text-slate-500">Your personal link-safety workspace awaits.</p></div>
          <form onSubmit={submit} className="space-y-5">
            <label className="block"><span className="mb-2 block text-sm font-bold text-slate-700">Email address</span><span className="relative block"><Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input autoComplete="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className="focus-ring h-12 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400" /></span></label>
            <label className="block"><span className="mb-2 block text-sm font-bold text-slate-700">Password</span><span className="relative block"><LockKeyhole className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input autoComplete="current-password" type={visible ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" className="focus-ring h-12 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-12 text-sm text-slate-800 placeholder:text-slate-400" /><button type="button" onClick={() => setVisible((value) => !value)} aria-label={visible ? "Hide password" : "Show password"} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700">{visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></span></label>
            {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 px-3.5 py-3 text-sm text-rose-700">{error}</p>}
            <button disabled={loading} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-700 text-sm font-bold text-white shadow-lg shadow-blue-700/15 transition hover:bg-blue-800 disabled:cursor-wait disabled:opacity-70">{loading ? "Signing you in…" : <>Continue to dashboard <ArrowRight className="h-4 w-4" /></>}</button>
          </form>
          <div className="mt-7 flex items-start gap-2.5 rounded-xl bg-slate-50 p-3.5"><LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" /><p className="text-xs leading-relaxed text-slate-500">Demo mode is enabled. Use any valid email and a password with 6 or more characters to explore.</p></div>
          <p className="mt-9 text-center text-xs text-slate-400">Protected workspace · Your links stay yours</p>
        </div>
      </section>
    </main>
  );
}

function Brand({ light = false }) {
  return <div className="relative z-10 flex items-center gap-2.5"><div className={`flex h-10 w-10 items-center justify-center rounded-xl ${light ? "bg-white/15 text-white" : "bg-blue-700 text-white"}`}><ShieldCheck className="h-5 w-5" /></div><span className={`font-display text-lg font-extrabold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>PhishGuard<span className={light ? "text-blue-300" : "text-blue-700"}>.</span></span><Link2 className={`ml-1 h-4 w-4 ${light ? "text-blue-300" : "hidden"}`} /></div>;
}
