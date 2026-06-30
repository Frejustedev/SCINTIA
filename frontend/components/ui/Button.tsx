import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "signal";

const VARIANTS: Record<Variant, string> = {
  // Primary action = solid Iris with dark-ink text (charte §6).
  primary: "bg-primary text-ink-900 hover:opacity-90",
  // Secondary = ink-700 outline.
  secondary: "border border-border bg-transparent text-text hover:bg-ink-800",
  // Hot gradient — reserved for rare "signal" actions (e.g. start analysis).
  signal: "bg-grad-hot text-ink-900 hover:opacity-95",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

/** Charte-compliant button. Labels are imperative and constant across a flow. */
export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex min-h-[44px] items-center justify-center gap-2 rounded-md px-4",
        "text-sm font-medium transition duration-200 ease-soft",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VARIANTS[variant],
        className,
      ].join(" ")}
      {...props}
    />
  );
}
