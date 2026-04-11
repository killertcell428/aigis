/**
 * Aigis Trust Badge — React Component
 *
 * Drop this into any React/Next.js app to show that it's protected by Aigis.
 *
 * Usage:
 *   import { AIGuardianBadge } from "@/components/AIGuardianBadge";
 *   <AIGuardianBadge />
 *   <AIGuardianBadge variant="dark" />
 *   <AIGuardianBadge variant="minimal" />
 */

interface AIGuardianBadgeProps {
  variant?: "light" | "dark" | "minimal";
  href?: string;
  className?: string;
}

export function AIGuardianBadge({
  variant = "light",
  href = "https://aigis-mauve.vercel.app",
  className = "",
}: AIGuardianBadgeProps) {
  const styles = {
    light: {
      bg: "bg-gradient-to-r from-blue-800 to-blue-700",
      text: "text-white",
      shield: "text-white/80",
      check: "text-white",
    },
    dark: {
      bg: "bg-slate-900 border border-slate-700",
      text: "text-slate-200",
      shield: "text-blue-400",
      check: "text-blue-400",
    },
    minimal: {
      bg: "bg-white border border-slate-200",
      text: "text-slate-700",
      shield: "text-blue-600",
      check: "text-blue-600",
    },
  };

  const s = styles[variant];

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title="Protected by Aigis — All AI requests are scanned and monitored"
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold no-underline transition-opacity hover:opacity-90 ${s.bg} ${s.text} ${className}`}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className={s.shield}>
        <path
          d="M12 2L3 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-9-4z"
          fill="currentColor"
          fillOpacity="0.2"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M9 12l2 2 4-4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={s.check}
        />
      </svg>
      Protected by Aigis
    </a>
  );
}

export default AIGuardianBadge;
