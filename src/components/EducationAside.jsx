import { ArrowUpRight, BadgeCheck, Link2, MailWarning, ShieldCheck } from "lucide-react";

const tips = [
  { icon: Link2, title: "Inspect the domain", text: "Look for misspellings, extra words, or odd characters before the first slash." },
  { icon: MailWarning, title: "Pause on urgency", text: "Threats, prizes, and urgent requests are common pressure tactics." },
  { icon: ShieldCheck, title: "Verify independently", text: "Visit the organisation’s official site directly instead of using a message link." },
];

export default function EducationAside() {
  return (
    <aside className="overflow-hidden rounded-2xl border border-blue-100 bg-white card-shadow">
      <div className="relative overflow-hidden bg-[#eaf3ff] p-5">
        <div className="absolute -right-5 -top-8 h-28 w-28 rounded-full border-[16px] border-white/50" />
        <div className="relative flex items-center gap-2 text-blue-700"><BadgeCheck className="h-5 w-5" /><span className="text-[11px] font-extrabold uppercase tracking-[0.16em]">Security playbook</span></div>
        <h3 className="relative mt-3 font-display text-lg font-extrabold text-slate-900">A little caution goes a long way.</h3>
        <p className="relative mt-1 text-sm leading-relaxed text-slate-600">Build these quick checks into your everyday browsing.</p>
      </div>
      <div className="space-y-5 p-5">
        {tips.map(({ icon: Icon, title, text }, index) => <div key={title} className="flex gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Icon className="h-4 w-4" /></div><div><h4 className="text-sm font-bold text-slate-800"><span className="mr-1.5 text-xs text-blue-400">0{index + 1}</span>{title}</h4><p className="mt-1 text-xs leading-relaxed text-slate-500">{text}</p></div></div>)}
        <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-3.5"><div className="flex items-center gap-2 text-xs font-bold text-blue-800"><ShieldCheck className="h-4 w-4" /> Remember</div><p className="mt-1.5 text-xs leading-relaxed text-blue-900/70">HTTPS means a connection is encrypted. It doesn’t prove a site is trustworthy.</p></div>
        <a href="https://www.cisa.gov/secure-our-world/recognize-and-report-phishing" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-900">More phishing safety tips <ArrowUpRight className="h-3.5 w-3.5" /></a>
      </div>
    </aside>
  );
}
