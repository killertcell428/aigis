"use client";

import { Lang } from "@/lib/lang";

interface Props {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

export default function LangToggle({ lang, onChange }: Props) {
  return (
    <div className="flex items-center gap-0.5 bg-gd-surface border border-gd-subtle rounded-lg p-0.5">
      <button
        onClick={() => onChange("en")}
        className={`px-2.5 py-1 rounded text-xs transition-all ${
          lang === "en"
            ? "bg-gd-accent-glow text-gd-text-primary"
            : "text-gd-text-muted hover:text-gd-text-secondary"
        }`}
        style={{ fontWeight: lang === "en" ? 520 : 440 }}
      >
        EN
      </button>
      <button
        onClick={() => onChange("ja")}
        className={`px-2.5 py-1 rounded text-xs transition-all ${
          lang === "ja"
            ? "bg-gd-accent-glow text-gd-text-primary"
            : "text-gd-text-muted hover:text-gd-text-secondary"
        }`}
        style={{ fontWeight: lang === "ja" ? 520 : 440 }}
      >
        JA
      </button>
    </div>
  );
}
