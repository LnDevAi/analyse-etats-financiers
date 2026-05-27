import { clsx } from "clsx";

type RiskLevel = "VERT" | "ORANGE" | "ROUGE";

const config = {
  VERT: { label: "Conforme", className: "risk-badge-vert", dot: "bg-green-500" },
  ORANGE: { label: "Vigilance", className: "risk-badge-orange", dot: "bg-amber-500" },
  ROUGE: { label: "Alerte", className: "risk-badge-rouge", dot: "bg-red-500" },
};

export default function RiskBadge({ level, showDot = true }: { level: RiskLevel | string; showDot?: boolean }) {
  const c = config[level as RiskLevel] || config.ORANGE;
  return (
    <span className={c.className}>
      {showDot && <span className={clsx("w-1.5 h-1.5 rounded-full", c.dot)} />}
      {c.label}
    </span>
  );
}
