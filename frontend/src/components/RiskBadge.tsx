import clsx from "clsx";

interface Props {
  level: "low" | "medium" | "high" | "critical" | string;
  score?: number;
  lang?: "en" | "ja";
}

const config: Record<string, { bg: string; text: string; en: string; ja: string }> = {
  low:      { bg: "bg-gd-safe-bg",   text: "text-gd-safe",   en: "Low",      ja: "低" },
  medium:   { bg: "bg-gd-warn-bg",   text: "text-gd-warn",   en: "Medium",   ja: "中" },
  high:     { bg: "bg-gd-danger-bg",  text: "text-gd-danger",  en: "High",     ja: "高" },
  critical: { bg: "bg-gd-danger-bg",  text: "text-gd-danger",  en: "Critical", ja: "重大" },
};

export default function RiskBadge({ level, score, lang = "ja" }: Props) {
  const c = config[level] ?? config["low"];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px]",
        c.bg, c.text
      )}
      style={{ fontWeight: 520 }}
    >
      {lang === "ja" ? c.ja : c.en}
      {score !== undefined && <span className="opacity-60">({score})</span>}
    </span>
  );
}
