import type { InputHTMLAttributes } from "react";

/** Charte-compliant text field: ink-850 bg, visible Iris focus ring. */
export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={[
        "min-h-[44px] w-full rounded-md border border-border bg-ink-850 px-3",
        "text-sm text-ink-100 placeholder:text-muted",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris",
        className,
      ].join(" ")}
      {...props}
    />
  );
}
