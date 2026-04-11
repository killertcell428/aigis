import clsx from "clsx";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "default" | "red" | "yellow" | "green";
}

const accentBorder: Record<string, string> = {
  default: "border-l-gd-text-dim",
  red: "border-l-gd-danger",
  yellow: "border-l-gd-warn",
  green: "border-l-gd-safe",
};

export default function StatCard({ title, value, subtitle, color = "default" }: Props) {
  return (
    <div
      className={clsx(
        "bg-gd-surface border border-gd-subtle rounded-xl p-5 shadow-gd-card",
        "border-l-[3px]",
        accentBorder[color]
      )}
    >
      <p className="text-xs text-gd-text-muted" style={{ fontWeight: 480 }}>{title}</p>
      <p className="text-2xl text-gd-text-primary mt-1.5 tracking-tight" style={{ fontWeight: 580 }}>
        {value}
      </p>
      {subtitle && (
        <p className="text-[11px] text-gd-text-dim mt-1">{subtitle}</p>
      )}
    </div>
  );
}
