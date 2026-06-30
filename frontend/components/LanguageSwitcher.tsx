"use client";

import { LOCALES, useLocale } from "@/lib/locale";

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocale();
  return (
    <div className="flex gap-1 font-mono text-xs" aria-label="Langue">
      {LOCALES.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => setLocale(option)}
          aria-pressed={option === locale}
          className={`rounded px-2 py-1 uppercase ${
            option === locale ? "bg-iris/15 text-ink-100" : "text-muted hover:text-ink-200"
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
