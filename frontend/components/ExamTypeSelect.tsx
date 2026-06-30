"use client";

import { useState } from "react";

import { EXAM_OPTIONS, type ExamType } from "@/lib/exams";

/**
 * Exam-type selector. Selection is visual only in Phase 0 (no submission).
 */
export function ExamTypeSelect() {
  const [selected, setSelected] = useState<ExamType | null>(null);

  return (
    <div
      role="radiogroup"
      aria-label="Type d'examen"
      className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3"
    >
      {EXAM_OPTIONS.map((option) => {
        const active = option.value === selected;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => setSelected(option.value)}
            className={[
              "flex min-h-[44px] flex-col items-start gap-0.5 rounded-md border px-4 py-3 text-left",
              "transition duration-200 ease-soft",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris",
              active ? "border-iris bg-iris/10" : "border-border bg-surface hover:border-ink-400",
            ].join(" ")}
          >
            <span className="text-sm font-medium text-ink-100">{option.label}</span>
            <span className="font-mono text-xs text-muted">{option.tracer}</span>
          </button>
        );
      })}
    </div>
  );
}
