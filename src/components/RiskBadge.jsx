import { getLevel } from "../utils/risk";

const styles = {
  safe: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  suspicious: "bg-amber-50 text-amber-700 ring-amber-200",
  malicious: "bg-rose-50 text-rose-700 ring-rose-200",
};

export default function RiskBadge({ score, level }) {
  const result = getLevel(Number.isFinite(Number(score)) ? Number(score) : 0);
  const label = level || result.label;
  const key = label.toLowerCase();
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${styles[key] || styles.safe}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{label}</span>;
}
