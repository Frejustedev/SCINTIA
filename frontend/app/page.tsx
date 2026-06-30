import Link from "next/link";

import { ExamTypeSelect } from "@/components/ExamTypeSelect";
import { Logo } from "@/components/Logo";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { UploadZone } from "@/components/UploadZone";
import { getDictionary } from "@/lib/i18n";

export default function Home() {
  const t = getDictionary();

  return (
    <div className="relative mx-auto flex min-h-screen max-w-5xl flex-col px-6">
      {/* Header / lockup */}
      <header className="flex items-center justify-between py-6">
        <div className="flex items-center gap-3">
          <Logo size={36} />
          <span className="font-display text-2xl font-semibold tracking-tight text-ink-100">
            Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Badge tone="info">{t.home.researchBadge}</Badge>
          <Link
            href="/studies"
            className="font-mono text-xs uppercase tracking-[0.1em] text-iris hover:underline"
          >
            Examens
          </Link>
          <Link
            href="/login"
            className="font-mono text-xs uppercase tracking-[0.1em] text-iris hover:underline"
          >
            Se connecter
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main className="flex flex-1 flex-col gap-10 py-10">
        <section className="max-w-2xl">
          <h1 className="font-display text-4xl font-semibold tracking-tight text-ink-100">
            {t.tagline.before}
            <span className="bg-grad-hot bg-clip-text text-transparent">{t.tagline.accent}</span>
            {t.tagline.after}
          </h1>
          <p className="mt-4 text-base text-ink-300">{t.sub}</p>
        </section>

        {/* New-exam card */}
        <Card className="p-6 shadow-soft">
          <p className="mb-4 font-mono text-xs uppercase tracking-[0.1em] text-muted">
            {t.home.eyebrow}
          </p>

          <h2 className="mb-3 font-display text-lg text-ink-100">{t.home.chooseExam}</h2>
          <ExamTypeSelect />

          <div className="mt-6">
            <UploadZone />
          </div>
        </Card>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/studies/new"
            className="inline-flex min-h-[44px] items-center justify-center rounded-md bg-grad-hot px-5 text-sm font-medium text-ink-900 transition duration-200 ease-soft hover:opacity-95"
          >
            Commencer un examen
          </Link>
        </div>
      </main>

      {/* Footer disclaimer */}
      <footer className="border-t border-border py-6">
        <p className="text-sm text-muted">{t.home.disclaimer}</p>
      </footer>
    </div>
  );
}
