# Phishing Detection Web App: Frontend Build Guide (VS Code)

This guide walks you through building the frontend step by step, from an empty folder to a working app. Follow the steps in order and copy each file exactly as shown.

**What you will build**

| Feature | Description |
|---|---|
| Login page | Email and password form, protected routes, token stored in the browser |
| Dashboard | Main screen shown after login |
| Single URL scan | Paste one URL, run a scan, see a **risk score (0 to 100)**, level and reasons |
| Batch URL scan | Paste many URLs or upload a `.txt`/`.csv` file, scan them all, export results |
| Scan history | Searchable, filterable table of past scans, with export and clear |
| Educational aside | A side panel teaching users how to spot malicious messages and URLs |

**Tech stack:** React 18 + Vite, Tailwind CSS, React Router, Axios.

**Important design choice:** The frontend ships with a **mock mode** (`VITE_USE_MOCK=true`) that scores URLs with simple rules in the browser. This lets you build, demo and test the whole UI before your backend or ML model is ready. When the backend is ready, you flip one environment variable (Step 12).

---

## Step 1: Install the prerequisites

1. Install **Node.js LTS** (version 18 or newer) from https://nodejs.org.
2. Install **VS Code** from https://code.visualstudio.com.
3. Verify in a terminal:

```bash
node -v
npm -v
```

4. Install these VS Code extensions (Extensions icon, or `Ctrl+Shift+X`):
   - **ES7+ React/Redux/React-Native snippets**
   - **Tailwind CSS IntelliSense**
   - **Prettier - Code formatter**
   - **ESLint**

---

## Step 2: Create the project

Open VS Code, then open the integrated terminal (`` Ctrl+` ``) in the folder where you keep projects:

```bash
npm create vite@latest phishguard-frontend -- --template react
cd phishguard-frontend
npm install
```

Open the folder in VS Code: **File > Open Folder > phishguard-frontend**.

Install the dependencies:

```bash
npm install react-router-dom axios
npm install tailwindcss @tailwindcss/vite
```

---

## Step 3: Configure Tailwind CSS

**3.1** Replace the contents of `vite.config.js`:

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

**3.2** Replace **everything** in `src/index.css` with:

```css
@import "tailwindcss";

body {
  @apply bg-slate-50 text-slate-800 antialiased;
}
```

**3.3** Delete files you do not need: `src/App.css` and `src/assets/react.svg`.

---

## Step 4: Create the folder structure

In the terminal (Git Bash, macOS or Linux):

```bash
mkdir -p src/api src/context src/components src/pages src/utils
```

On Windows PowerShell:

```powershell
mkdir src\api, src\context, src\components, src\pages, src\utils
```

Final structure you are aiming for:

```
phishguard-frontend/
├── .env
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    │   ├── client.js
    │   └── scanService.js
    ├── context/
    │   ├── AuthContext.jsx
    │   └── ScanContext.jsx
    ├── utils/
    │   ├── risk.js
    │   └── exportCsv.js
    ├── components/
    │   ├── ProtectedRoute.jsx
    │   ├── RiskGauge.jsx
    │   ├── RiskBadge.jsx
    │   ├── ScanResultCard.jsx
    │   └── EducationAside.jsx
    └── pages/
        ├── Login.jsx
        ├── Dashboard.jsx
        ├── SingleScan.jsx
        ├── BatchScan.jsx
        └── ScanHistory.jsx
```

---

## Step 5: Environment variables

Create a file named `.env` in the project root (next to `package.json`):

```
VITE_API_URL=http://localhost:5000/api
VITE_USE_MOCK=true
```

> Restart `npm run dev` whenever you change `.env`.

---

## Step 6: Utilities (risk levels and CSV export)

**`src/utils/risk.js`**

```js
// Score bands: 0-29 Safe, 30-69 Suspicious, 70-100 Malicious
export function getLevel(score) {
  if (score >= 70) {
    return {
      key: "malicious",
      label: "Malicious",
      color: "#dc2626",
      badge: "bg-red-100 text-red-700 border-red-200",
      advice: "Do not open this link. Report it and delete the message it came from.",
    };
  }
  if (score >= 30) {
    return {
      key: "suspicious",
      label: "Suspicious",
      color: "#f59e0b",
      badge: "bg-amber-100 text-amber-700 border-amber-200",
      advice: "Be careful. Do not enter any personal details. Verify through the official website.",
    };
  }
  return {
    key: "safe",
    label: "Safe",
    color: "#16a34a",
    badge: "bg-green-100 text-green-700 border-green-200",
    advice: "No major warning signs found, but always stay alert.",
  };
}
```

**`src/utils/exportCsv.js`**

```js
export function exportResultsToCsv(results, filename = "scan-results.csv") {
  const header = ["URL", "Risk Score", "Level", "Reasons", "Scanned At"];
  const rows = results.map((r) => [
    `"${r.url.replace(/"/g, '""')}"`,
    r.score,
    r.level,
    `"${(r.reasons || []).join("; ").replace(/"/g, '""')}"`,
    r.scannedAt,
  ]);
  const csv = [header.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
```

---

## Step 7: API layer (with mock mode)

**`src/api/client.js`**: Axios instance that attaches the login token to every request.

```js
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
```

**`src/api/scanService.js`**: All scan calls live here. The mock scorer generates the risk score from URL features.

```js
import api from "./client";
import { getLevel } from "../utils/risk";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Normalise a URL so the user can type "example.com" without https://
export function normalizeUrl(input) {
  const trimmed = input.trim();
  return /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
}

export function isValidUrl(input) {
  try {
    const u = new URL(normalizeUrl(input));
    return u.hostname.includes(".");
  } catch {
    return false;
  }
}

// Simple rule-based scorer used ONLY in mock mode
function mockScan(rawUrl) {
  const url = normalizeUrl(rawUrl);
  let score = 0;
  const reasons = [];
  let host = "";
  try {
    host = new URL(url).hostname;
  } catch {
    /* ignore */
  }

  if (!/^https:\/\//i.test(url)) {
    score += 15;
    reasons.push("Does not use HTTPS encryption");
  }
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) {
    score += 30;
    reasons.push("Uses a raw IP address instead of a domain name");
  }
  if (url.includes("@")) {
    score += 20;
    reasons.push("Contains an '@' symbol, which can hide the real destination");
  }
  if (url.length > 75) {
    score += 10;
    reasons.push("Unusually long URL");
  }
  if ((host.match(/\./g) || []).length > 3) {
    score += 10;
    reasons.push("Too many subdomains");
  }
  if (/(login|verify|secure|update|account|banking|paypal|password|confirm|wallet)/i.test(url)) {
    score += 15;
    reasons.push("Contains sensitive keywords commonly used in phishing");
  }
  if (/\.(xyz|top|tk|ml|ga|cf|click|gq|zip)$/i.test(host)) {
    score += 15;
    reasons.push("Uses a top-level domain often abused by attackers");
  }
  if (/xn--/.test(host)) {
    score += 10;
    reasons.push("Contains punycode characters that may imitate a real brand");
  }
  if (/-/.test(host) && host.split("-").length > 2) {
    score += 5;
    reasons.push("Multiple hyphens in the domain name");
  }

  score = Math.min(100, score);
  if (reasons.length === 0) reasons.push("No suspicious patterns detected");

  return {
    id: crypto.randomUUID(),
    url: rawUrl.trim(),
    score,
    level: getLevel(score).label,
    reasons,
    scannedAt: new Date().toISOString(),
  };
}

export async function scanSingle(url) {
  if (USE_MOCK) {
    await sleep(900);
    return mockScan(url);
  }
  const { data } = await api.post("/scan/single", { url });
  return data; // expected shape: see Step 12
}

export async function scanBatch(urls, onProgress) {
  if (USE_MOCK) {
    const results = [];
    for (let i = 0; i < urls.length; i++) {
      await sleep(250);
      results.push(mockScan(urls[i]));
      onProgress?.(i + 1, urls.length);
    }
    return results;
  }
  const { data } = await api.post("/scan/batch", { urls });
  onProgress?.(urls.length, urls.length);
  return data.results;
}

export async function loginRequest(email, password) {
  if (USE_MOCK) {
    await sleep(600);
    if (password.length < 6) throw new Error("Password must be at least 6 characters");
    return { token: "mock-token", user: { email, name: email.split("@")[0] } };
  }
  const { data } = await api.post("/auth/login", { email, password });
  return data; // { token, user }
}
```

---

## Step 8: Context providers (login state and scan history)

**`src/context/AuthContext.jsx`**

```jsx
import { createContext, useContext, useState } from "react";
import { loginRequest } from "../api/scanService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  const login = async (email, password) => {
    const { token, user } = await loginRequest(email, password);
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

**`src/context/ScanContext.jsx`**: Shared history so both Single and Batch scans appear in the History tab.

```jsx
import { createContext, useContext, useEffect, useState } from "react";

const ScanContext = createContext(null);
const KEY = "scan_history";

export function ScanProvider({ children }) {
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(history));
  }, [history]);

  const addScans = (results) => setHistory((prev) => [...results, ...prev]);
  const clearHistory = () => setHistory([]);

  return (
    <ScanContext.Provider value={{ history, addScans, clearHistory }}>
      {children}
    </ScanContext.Provider>
  );
}

export const useScans = () => useContext(ScanContext);
```

---

## Step 9: Reusable components

**`src/components/ProtectedRoute.jsx`**

```jsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}
```

**`src/components/RiskGauge.jsx`**: The circular risk score meter.

```jsx
import { getLevel } from "../utils/risk";

export default function RiskGauge({ score }) {
  const r = 54;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const { color } = getLevel(score);

  return (
    <div className="relative h-40 w-40">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold" style={{ color }}>{score}</span>
        <span className="text-xs text-slate-500">Risk score / 100</span>
      </div>
    </div>
  );
}
```

**`src/components/RiskBadge.jsx`**

```jsx
import { getLevel } from "../utils/risk";

export default function RiskBadge({ score }) {
  const { label, badge } = getLevel(score);
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${badge}`}>
      {label}
    </span>
  );
}
```

**`src/components/ScanResultCard.jsx`**: Shown after a single scan completes.

```jsx
import RiskGauge from "./RiskGauge";
import RiskBadge from "./RiskBadge";
import { getLevel } from "../utils/risk";

export default function ScanResultCard({ result }) {
  const { advice } = getLevel(result.score);
  return (
    <div className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <RiskGauge score={result.score} />
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-2">
            <h3 className="text-lg font-semibold">Scan result</h3>
            <RiskBadge score={result.score} />
          </div>
          <p className="break-all text-sm text-slate-500">{result.url}</p>
          <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">{advice}</p>
        </div>
      </div>

      <div className="mt-5">
        <h4 className="mb-2 text-sm font-semibold">Why this score?</h4>
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
          {result.reasons.map((reason, i) => (
            <li key={i}>{reason}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

**`src/components/EducationAside.jsx`**: The educational side panel.

```jsx
const urlTips = [
  "Check the domain carefully. 'paypa1.com' or 'amazon-secure.co' is not the real site.",
  "Hover over links (or long-press on mobile) to see the real destination before clicking.",
  "Look for HTTPS, but remember that phishing sites can use HTTPS too.",
  "Be wary of IP addresses, '@' symbols and very long URLs.",
  "Beware of shortened links (bit.ly and similar) from unknown senders.",
  "Type the official address yourself instead of following a link.",
];

const messageTips = [
  "Urgent or threatening language: 'Your account will be closed in 24 hours!'",
  "Requests for passwords, PINs, OTP codes or card details. Real companies never ask.",
  "Generic greetings such as 'Dear customer' instead of your name.",
  "Spelling and grammar mistakes, or a sender address that does not match the company.",
  "Unexpected attachments (.zip, .exe, .html) or prizes you never entered for.",
  "Messages pretending to be your bank, mobile money provider, employer or a government office.",
];

const actions = [
  "Do not click, reply or download.",
  "Verify through the organisation's official website or phone number.",
  "Report the message and delete it.",
  "If you already entered details, change your password and contact your bank immediately.",
];

function Section({ title, icon, items, tone }) {
  return (
    <div className="mb-5">
      <h4 className={`mb-2 flex items-center gap-2 text-sm font-semibold ${tone}`}>
        <span>{icon}</span> {title}
      </h4>
      <ul className="space-y-2 text-sm text-slate-600">
        {items.map((t, i) => (
          <li key={i} className="flex gap-2">
            <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-slate-400" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function EducationAside() {
  return (
    <aside className="rounded-xl border bg-white p-5 shadow-sm lg:sticky lg:top-6">
      <h3 className="mb-1 text-lg font-bold">Stay safe online</h3>
      <p className="mb-5 text-sm text-slate-500">
        Learn to recognise phishing before a scanner has to.
      </p>
      <Section title="Spotting malicious URLs" icon="🔗" items={urlTips} tone="text-blue-700" />
      <Section title="Spotting malicious messages" icon="✉️" items={messageTips} tone="text-amber-700" />
      <Section title="If you suspect phishing" icon="🛡️" items={actions} tone="text-green-700" />
    </aside>
  );
}
```

---

## Step 10: Pages

### 10.1 Login page

**`src/pages/Login.jsx`**

```jsx
import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Enter a valid email address.");
    if (password.length < 6) return setError("Password must be at least 6 characters.");

    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.message || err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 to-blue-900 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-6 text-center">
          <div className="mb-2 text-4xl">🛡️</div>
          <h1 className="text-2xl font-bold">PhishGuard</h1>
          <p className="text-sm text-slate-500">Sign in to scan and analyse suspicious links</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 p-2 text-sm text-red-600">{error}</p>
          )}

          <button
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-slate-400">
          Demo mode: any valid email and a password of 6+ characters works.
        </p>
      </div>
    </div>
  );
}
```

### 10.2 Single URL scan

**`src/pages/SingleScan.jsx`**

```jsx
import { useState } from "react";
import { scanSingle, isValidUrl } from "../api/scanService";
import { useScans } from "../context/ScanContext";
import ScanResultCard from "../components/ScanResultCard";

export default function SingleScan() {
  const { addScans } = useScans();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScan = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    if (!isValidUrl(url)) return setError("Please enter a valid URL, e.g. https://example.com");

    setLoading(true);
    try {
      const data = await scanSingle(url);
      setResult(data);
      addScans([data]); // save to history
    } catch (err) {
      setError(err.response?.data?.message || "Scan failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Single URL scan</h2>
      <p className="mb-4 text-sm text-slate-500">Paste a link to check it before you click.</p>

      <form onSubmit={handleScan} className="flex flex-col gap-3 sm:flex-row">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://suspicious-link.example.com/login"
          className="flex-1 rounded-lg border px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          disabled={loading}
          className="rounded-lg bg-blue-600 px-6 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? "Scanning..." : "Scan URL"}
        </button>
      </form>

      {error && <p className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-600">{error}</p>}
      {loading && (
        <div className="mt-6 flex items-center gap-3 text-sm text-slate-500">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          Analysing URL...
        </div>
      )}
      {result && <ScanResultCard result={result} />}
    </div>
  );
}
```

### 10.3 Batch URL scan

**`src/pages/BatchScan.jsx`**

```jsx
import { useState } from "react";
import { scanBatch, isValidUrl } from "../api/scanService";
import { useScans } from "../context/ScanContext";
import RiskBadge from "../components/RiskBadge";
import { exportResultsToCsv } from "../utils/exportCsv";

const MAX_URLS = 50;

export default function BatchScan() {
  const { addScans } = useScans();
  const [text, setText] = useState("");
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      // supports .txt (one per line) and .csv (comma or newline separated)
      const urls = String(reader.result).split(/[\n,;\r]+/).map((s) => s.trim()).filter(Boolean);
      setText(urls.join("\n"));
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleScan = async () => {
    setError("");
    setResults([]);
    const all = [...new Set(text.split(/\r?\n/).map((s) => s.trim()).filter(Boolean))];
    if (all.length === 0) return setError("Add at least one URL.");
    if (all.length > MAX_URLS) return setError(`Maximum ${MAX_URLS} URLs per batch.`);

    const invalid = all.filter((u) => !isValidUrl(u));
    if (invalid.length) return setError(`Invalid URL(s): ${invalid.slice(0, 3).join(", ")}${invalid.length > 3 ? "..." : ""}`);

    setLoading(true);
    setProgress({ done: 0, total: all.length });
    try {
      const data = await scanBatch(all, (done, total) => setProgress({ done, total }));
      setResults(data);
      addScans(data);
    } catch (err) {
      setError(err.response?.data?.message || "Batch scan failed.");
    } finally {
      setLoading(false);
    }
  };

  const counts = {
    Safe: results.filter((r) => r.level === "Safe").length,
    Suspicious: results.filter((r) => r.level === "Suspicious").length,
    Malicious: results.filter((r) => r.level === "Malicious").length,
  };

  return (
    <div>
      <h2 className="text-xl font-semibold">Batch URL scan</h2>
      <p className="mb-4 text-sm text-slate-500">
        Enter one URL per line, or upload a .txt / .csv file (max {MAX_URLS}).
      </p>

      <textarea
        rows={7}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"https://example.com\nhttp://192.168.0.1/login\nhttps://paypa1-verify.xyz/account"}
        className="w-full rounded-lg border p-3 font-mono text-sm outline-none focus:ring-2 focus:ring-blue-500"
      />

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <label className="cursor-pointer rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50">
          Upload file
          <input type="file" accept=".txt,.csv" onChange={handleFile} className="hidden" />
        </label>
        <button
          onClick={handleScan}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-6 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? "Scanning..." : "Scan all"}
        </button>
        {results.length > 0 && (
          <button
            onClick={() => exportResultsToCsv(results, "batch-results.csv")}
            className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50"
          >
            Export CSV
          </button>
        )}
      </div>

      {error && <p className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-600">{error}</p>}

      {loading && (
        <div className="mt-4">
          <div className="mb-1 text-sm text-slate-500">
            Scanned {progress.done} of {progress.total}
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-blue-600 transition-all"
              style={{ width: `${(progress.done / (progress.total || 1)) * 100}%` }}
            />
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-6">
          <div className="mb-3 grid grid-cols-3 gap-3 text-center text-sm">
            <div className="rounded-lg bg-green-50 p-3 text-green-700"><b className="text-xl">{counts.Safe}</b><br />Safe</div>
            <div className="rounded-lg bg-amber-50 p-3 text-amber-700"><b className="text-xl">{counts.Suspicious}</b><br />Suspicious</div>
            <div className="rounded-lg bg-red-50 p-3 text-red-700"><b className="text-xl">{counts.Malicious}</b><br />Malicious</div>
          </div>

          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="p-3">URL</th>
                  <th className="p-3">Score</th>
                  <th className="p-3">Level</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="max-w-xs break-all p-3">{r.url}</td>
                    <td className="p-3 font-semibold">{r.score}</td>
                    <td className="p-3"><RiskBadge score={r.score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 10.4 Scan history

**`src/pages/ScanHistory.jsx`**

```jsx
import { useState, useMemo } from "react";
import { useScans } from "../context/ScanContext";
import RiskBadge from "../components/RiskBadge";
import { exportResultsToCsv } from "../utils/exportCsv";

export default function ScanHistory() {
  const { history, clearHistory } = useScans();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");

  const filtered = useMemo(
    () =>
      history.filter(
        (h) =>
          h.url.toLowerCase().includes(query.toLowerCase()) &&
          (filter === "All" || h.level === filter)
      ),
    [history, query, filter]
  );

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-semibold">Scan history</h2>
          <p className="text-sm text-slate-500">{history.length} scan(s) recorded</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportResultsToCsv(filtered, "scan-history.csv")}
            disabled={!filtered.length}
            className="rounded-lg border px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
          >
            Export CSV
          </button>
          <button
            onClick={() => window.confirm("Delete all scan history?") && clearHistory()}
            disabled={!history.length}
            className="rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search URLs..."
          className="flex-1 rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          {["All", "Safe", "Suspicious", "Malicious"].map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-10 text-center text-sm text-slate-400">
          No scans to show yet.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-3">URL</th>
                <th className="p-3">Score</th>
                <th className="p-3">Level</th>
                <th className="p-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((h) => (
                <tr key={h.id} className="border-t">
                  <td className="max-w-xs break-all p-3">{h.url}</td>
                  <td className="p-3 font-semibold">{h.score}</td>
                  <td className="p-3"><RiskBadge score={h.score} /></td>
                  <td className="whitespace-nowrap p-3 text-slate-500">
                    {new Date(h.scannedAt).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### 10.5 Dashboard (ties everything together)

**`src/pages/Dashboard.jsx`**

```jsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useScans } from "../context/ScanContext";
import SingleScan from "./SingleScan";
import BatchScan from "./BatchScan";
import ScanHistory from "./ScanHistory";
import EducationAside from "../components/EducationAside";

const tabs = [
  { id: "single", label: "Single URL scan" },
  { id: "batch", label: "Batch scan" },
  { id: "history", label: "Scan history" },
];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { history } = useScans();
  const [active, setActive] = useState("single");

  const stats = [
    { label: "Total scans", value: history.length, color: "text-blue-600" },
    { label: "Safe", value: history.filter((h) => h.level === "Safe").length, color: "text-green-600" },
    { label: "Suspicious", value: history.filter((h) => h.level === "Suspicious").length, color: "text-amber-600" },
    { label: "Malicious", value: history.filter((h) => h.level === "Malicious").length, color: "text-red-600" },
  ];

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2 text-lg font-bold">
            <span>🛡️</span> PhishGuard
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-slate-500 sm:inline">{user?.email}</span>
            <button
              onClick={logout}
              className="rounded-lg border px-3 py-1.5 hover:bg-slate-50"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl p-4">
        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-xl border bg-white p-4 shadow-sm">
              <div className="text-xs uppercase text-slate-500">{s.label}</div>
              <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main column */}
          <section className="lg:col-span-2">
            <div className="mb-4 flex gap-1 overflow-x-auto rounded-lg bg-slate-200 p-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActive(t.id)}
                  className={`flex-1 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition ${
                    active === t.id ? "bg-white shadow" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="rounded-xl border bg-white p-5 shadow-sm">
              {active === "single" && <SingleScan />}
              {active === "batch" && <BatchScan />}
              {active === "history" && <ScanHistory />}
            </div>
          </section>

          {/* Educational aside */}
          <EducationAside />
        </div>
      </main>
    </div>
  );
}
```

---

## Step 11: Routing and app entry

**`src/App.jsx`**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ScanProvider } from "./context/ScanContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <AuthProvider>
      <ScanProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </ScanProvider>
    </AuthProvider>
  );
}
```

**`src/main.jsx`**

```jsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

Update the `<title>` in `index.html` to `PhishGuard | Phishing Detection`.

---

## Step 12: Run and test the app

```bash
npm run dev
```

Open the URL shown (usually http://localhost:5173).

**Test checklist**

| # | Test | Expected result |
|---|---|---|
| 1 | Open `/dashboard` while logged out | Redirected to `/login` |
| 2 | Log in with `test@mail.com` / `123456` | Dashboard appears |
| 3 | Single scan: `https://www.google.com` | Low score (Safe, green) |
| 4 | Single scan: `http://192.168.1.5/secure-login/verify` | High score (Malicious, red) with reasons listed |
| 5 | Batch scan: paste 3 to 5 URLs | Progress bar, summary counts, results table |
| 6 | Upload a `.txt` file with URLs | Textarea fills automatically |
| 7 | Open Scan history | All scans listed, search and filter work |
| 8 | Refresh the page | You stay logged in and history persists |
| 9 | Click Log out | Back to the login page |
| 10 | Resize the browser to phone width | Layout stacks, nothing overflows |

---

## Step 13: Connect to your real backend

When your backend or ML model is ready:

1. In `.env`, set:

```
VITE_API_URL=https://your-backend-url/api
VITE_USE_MOCK=false
```

2. Restart the dev server.
3. Make sure your backend exposes these endpoints and returns these shapes:

**`POST /auth/login`**

```json
// request
{ "email": "user@mail.com", "password": "secret123" }
// response
{ "token": "jwt-token-here", "user": { "email": "user@mail.com", "name": "User" } }
```

**`POST /scan/single`**

```json
// request
{ "url": "https://example.com" }
// response
{
  "id": "unique-id",
  "url": "https://example.com",
  "score": 82,
  "level": "Malicious",
  "reasons": ["Uses a raw IP address", "Contains phishing keywords"],
  "scannedAt": "2026-10-03T10:15:00Z"
}
```

**`POST /scan/batch`**

```json
// request
{ "urls": ["https://a.com", "https://b.com"] }
// response
{ "results": [ { /* same shape as single scan */ }, { } ] }
```

> `level` must be exactly `Safe`, `Suspicious` or `Malicious`, and `score` must be a number from 0 to 100. If your model returns a probability (0 to 1), multiply by 100 and round before sending.

4. **CORS:** The backend must allow your frontend origin (e.g. `http://localhost:5173`), otherwise the browser will block requests.

---

## Step 14: Build for production (optional)

```bash
npm run build
npm run preview
```

The `dist/` folder can be deployed to Netlify, Vercel or GitHub Pages. For Netlify or Vercel, add a rewrite rule so all routes serve `index.html` (needed for React Router).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Styles not applying | Confirm `@import "tailwindcss";` is the first line of `src/index.css`, the Tailwind plugin is in `vite.config.js`, and `index.css` is imported in `main.jsx`. Restart the dev server. |
| `.env` values are `undefined` | Variables must start with `VITE_`. Restart the dev server after editing. |
| Blank page | Open the browser console (`F12`) and read the first red error, which is usually a wrong import path or file name case. |
| Network or CORS error with real backend | Enable CORS on the backend for the frontend origin. |
| Page refresh gives 404 after deploying | Add an SPA rewrite rule to `index.html`. |
| Cannot log in with the backend | Check the response includes `token` and `user`, and inspect the request in the browser Network tab. |

---

## Suggested project report talking points

- **Architecture:** React SPA, context-based state, service layer separating UI from API.
- **Security considerations:** Token-based auth, protected routes, input validation on URLs, no secrets in frontend code. Note that localStorage tokens are a known tradeoff versus httpOnly cookies, which you can mention as future work.
- **Usability:** Explainable results (reasons list), colour-coded risk levels, an educational panel to improve user awareness.
- **Future improvements:** Registration and password reset, charts of scan trends, browser extension, scanning pasted email or SMS text, role-based admin dashboard.

---

**You now have a complete frontend:** login, dashboard with single scan, batch scan, scan history, risk score generation and an educational aside. Build it in the order above and test after each step.
