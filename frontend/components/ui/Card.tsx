import type { HTMLAttributes } from "react";

/** Surface panel: ink-800 background, ink-700 border, lg radius (charte §6). */
export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={["rounded-lg border border-border bg-surface", className].join(" ")}
      {...props}
    />
  );
}
