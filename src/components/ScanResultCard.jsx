import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import RiskBadge from "./RiskBadge";
import RiskGauge from "./RiskGauge";
import { getLevel } from "../utils/risk";

const icons = { safe: CheckCircle2, suspicious: AlertTriangle, malicious: ShieldAlert };

export default function ScanResultCard({ result }) {
  const risk = getLevel(result.score);
  const Icon = icons[risk.key];
  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-blue-100 bg-white card-shadow">
      <div className="flex flex-col items-center gap-5 border-b border-slate-100 bg-gradient-to-r from-white to-blue-50/60 p-6 sm:flex-row sm:p-7">
        <RiskGauge score={result.score} />
        <div className="min-w-0 flex-1 text-center sm:text-left">
          <div className="mb-2 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
            <h3 className="font-display text-xl font-extrabold text-slate-900">Analysis complete</h3>
            <RiskBadge score={result.score} />
          </div>
          <p className="break-all text-sm text-slate-500">{result.url}</p>
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-blue-100 bg-white/80 p-3.5 text-left text-sm leading-relaxed text-slate-600">
            <Icon className="mt-0.5 h-4 w-4 shrink-0" style={{ color: risk.color }} />{risk.advice}
          </div>
        </div>
      </div>
      <div className="p-6 sm:px-8">
        <h4 className="mb-3 text-sm font-bold text-slate-800">What we noticed</h4>
        <ul className="grid gap-2 sm:grid-cols-2">
          {result.reasons.map((reason, index) => <li key={`${reason}-${index}`} className="flex items-start gap-2.5 rounded-lg bg-slate-50 px-3 py-2.5 text-sm text-slate-600"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />{reason}</li>)}
        </ul>
        <p className="mt-4 text-xs text-slate-400">Automated analysis is a helpful signal, not a guarantee. When in doubt, don’t click.</p>
      </div>
    </section>
  );
}
