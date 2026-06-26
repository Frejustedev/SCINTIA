import { Button } from "@/components/ui/Button";
import { getDictionary } from "@/lib/i18n";

/**
 * Drag-and-drop area — UI only, intentionally inactive in Phase 0.
 * Real ingestion + anonymization is wired in Phase 1.
 */
export function UploadZone() {
  const t = getDictionary().home;
  return (
    <div
      aria-disabled="true"
      className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border bg-ink-850/50 px-6 py-10 text-center"
    >
      <svg
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-muted"
        aria-hidden="true"
      >
        <path
          d="M12 16V4m0 0L8 8m4-4 4 4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <p className="font-display text-lg text-ink-100">{t.uploadTitle}</p>
      <p className="text-sm text-muted">{t.uploadHint}</p>
      <Button variant="secondary" disabled aria-disabled="true">
        {t.browse}
      </Button>
      <p className="mt-1 font-mono text-xs text-muted">{t.uploadInactive}</p>
    </div>
  );
}
