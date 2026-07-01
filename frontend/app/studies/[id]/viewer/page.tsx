"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import { DicomViewerPro } from "@/components/DicomViewerPro";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";
import { getToken } from "@/lib/api";
import { useT } from "@/lib/locale";

export default function ViewerPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const studyId = params.id;
  const t = useT();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={32} />
          <span className="font-display text-xl font-semibold tracking-tight text-ink-100">
            Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <Link
            href={`/studies/${studyId}`}
            className="font-mono text-xs uppercase tracking-[0.1em] text-muted hover:text-ink-200"
          >
            {t("viewer.back")}
          </Link>
        </div>
      </header>

      <main className="flex-1 py-2">
        <Card className="p-6 shadow-soft">
          <h1 className="mb-4 font-display text-lg text-ink-100">{t("viewer.title")}</h1>
          <DicomViewerPro studyId={studyId} />
        </Card>
      </main>

      <footer className="border-t border-border py-6">
        <p className="text-sm text-muted">
          Images dé-identifiées. Prototype de recherche, non destiné au diagnostic autonome.
        </p>
      </footer>
    </div>
  );
}
