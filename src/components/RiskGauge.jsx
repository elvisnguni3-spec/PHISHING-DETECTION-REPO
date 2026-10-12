import { getLevel } from "../utils/risk";

export default function RiskGauge({ score }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.max(0, Math.min(100, score));
  const { color } = getLevel(progress);
  return (
    <div className="relative h-40 w-40 shrink-0" aria-label={`Risk score ${progress} out of 100`}>
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="#e9f0f9" strokeWidth="9" />
        <circle cx="60" cy="60" r={radius} fill="none" stroke={color} strokeWidth="9" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference - (progress / 100) * circumference} style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-4xl font-extrabold tracking-tight" style={{ color }}>{progress}</span>
        <span className="mt-0.5 text-[11px] font-semibold text-slate-400">RISK SCORE / 100</span>
      </div>
    </div>
  );
}
