import type { HTMLAttributes } from "react";

type Tone = "neutral" | "ok" | "info" | "warn" | "crit" | "ai-draft";

const TONES: Record<Tone, string> = {
  neutral: "border-border text-muted",
  ok: "border-ok/40 text-ok",
  info: "border-info/40 text-info",
  warn: "border-warn/40 text-warn",
  crit: "border-crit/40 text-crit",
  // The mandatory, non-removable "Brouillon IA — à valider" chip (amber outline).
  "ai-draft": "border-warn/40 text-warn bg-warn/5",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

/** Status chip. Use `tone="ai-draft"` for the non-removable AI-draft notice. */
export function Badge({ tone = "neutral", className = "", ...props }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-pill border px-3 py-1",
        "font-mono text-xs tracking-wide",
        TONES[tone],
        className,
      ].join(" ")}
      {...props}
    />
  );
}
