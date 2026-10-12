export function getLevel(score) {
  if (score >= 70) return { key: "malicious", label: "Malicious", color: "#e05a69", advice: "Avoid opening this link. Report it and remove the message it came from." };
  if (score >= 30) return { key: "suspicious", label: "Suspicious", color: "#e6a23c", advice: "Proceed carefully. Never enter personal details; verify via the official website." };
  return { key: "safe", label: "Safe", color: "#18a77a", advice: "No major warning signs detected. Keep your usual online safety habits." };
}
