import api from "./client";
import { getLevel } from "../utils/risk";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export function normalizeUrl(input) {
  const value = input.trim();
  return /^https?:\/\//i.test(value) ? value : `https://${value}`;
}

export function isValidUrl(input) {
  try {
    const parsed = new URL(normalizeUrl(input));
    return parsed.hostname.includes(".") && !/\s/.test(parsed.hostname);
  } catch { return false; }
}

function mockScan(rawUrl) {
  const url = normalizeUrl(rawUrl);
  let score = 0;
  const reasons = [];
  let hostname = "";
  try { hostname = new URL(url).hostname; } catch { /* invalid urls are rejected before scanning */ }
  if (!/^https:\/\//i.test(url)) { score += 15; reasons.push("Does not use HTTPS encryption"); }
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) { score += 30; reasons.push("Uses a raw IP address instead of a domain name"); }
  if (url.includes("@")) { score += 20; reasons.push("Contains an @ symbol that may hide its destination"); }
  if (url.length > 75) { score += 10; reasons.push("Unusually long URL"); }
  if ((hostname.match(/\./g) || []).length > 3) { score += 10; reasons.push("Contains an unusually large number of subdomains"); }
  if (/(login|verify|secure|update|account|banking|paypal|password|confirm|wallet)/i.test(url)) { score += 15; reasons.push("Uses sensitive keywords commonly found in phishing links"); }
  if (/\.(xyz|top|tk|ml|ga|cf|click|gq|zip)$/i.test(hostname)) { score += 15; reasons.push("Uses a top-level domain frequently abused by attackers"); }
  if (/xn--/i.test(hostname)) { score += 10; reasons.push("Contains punycode that may imitate a trusted brand"); }
  if (/-/.test(hostname) && hostname.split("-").length > 2) { score += 5; reasons.push("Contains multiple hyphens in the domain name"); }
  score = Math.min(100, score);
  if (!reasons.length) reasons.push("No suspicious patterns detected");
  return { id: crypto.randomUUID(), url: rawUrl.trim(), score, level: getLevel(score).label, reasons, scannedAt: new Date().toISOString() };
}

export async function scanSingle(url) {
  if (USE_MOCK) {
    await sleep(850);
    return mockScan(url);
  }

  const { data } = await api.post("/detect", {
    url: normalizeUrl(url),
  });

  const score = data.analysis.score;

  return {
    id: crypto.randomUUID(),
    url: data.input,
    score,
    level: getLevel(score).label,
    reasons: (data.explanation || []).map((item) => item.reason),
    scannedAt: data.metadata?.scan_time || new Date().toISOString(),
    verdict: data.analysis.verdict,
    confidence: data.analysis.confidence,
    riskBreakdown: data.risk_breakdown,
    features: data.features,
    recommendation: data.recommendation,
  };
}

export async function scanBatch(urls, onProgress) {
  if (USE_MOCK) {
    const results = [];
    for (let index = 0; index < urls.length; index += 1) {
      await sleep(220);
      results.push(mockScan(urls[index]));
      onProgress?.(index + 1, urls.length);
    }
    return results;
  }
  const { data } = await api.post("/scan/batch", { urls: urls.map(normalizeUrl) });
  onProgress?.(urls.length, urls.length);
  return data.results;
}


export async function loginRequest(email, password) {
  if (USE_MOCK) {
    await sleep(500);
    if (password.length < 6) {
      throw new Error("Password must be at least 6 characters.");
    }
    return {
      token: "mock-token",
      user: { email, name: email.split("@")[0] },
    };
  }

  const { data } = await api.post("/login", {
    email: email,
    password: password,
  });

  return {
    token: data.access_token,
    user: data.user,
  };
}

