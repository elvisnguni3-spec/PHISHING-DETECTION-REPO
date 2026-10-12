export function exportResultsToCsv(results, filename = "scan-results.csv") {
  const quote = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const rows = [
    ["URL", "Risk Score", "Level", "Reasons", "Scanned At"],
    ...results.map((result) => [result.url, result.score, result.level, (result.reasons || []).join("; "), result.scannedAt]),
  ];
  const csv = rows.map((row) => row.map(quote).join(",")).join("\r\n");
  const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
