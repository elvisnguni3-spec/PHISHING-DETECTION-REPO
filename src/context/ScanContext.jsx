import { createContext, useContext, useEffect, useState } from "react";

const ScanContext = createContext(null);
const KEY = "scan_history";

export function ScanProvider({ children }) {
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; }
  });

  useEffect(() => { localStorage.setItem(KEY, JSON.stringify(history)); }, [history]);
  const addScans = (results) => setHistory((previous) => [...results, ...previous]);
  const clearHistory = () => setHistory([]);

  return <ScanContext.Provider value={{ history, addScans, clearHistory }}>{children}</ScanContext.Provider>;
}

export const useScans = () => useContext(ScanContext);
