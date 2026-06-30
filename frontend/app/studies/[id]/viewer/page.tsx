"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

import { DicomViewer } from "@/components/DicomViewer";
import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";
import { getToken } from "@/lib/api";

export default function ViewerPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const studyId = params.id;

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
        <Link
          href={`/studies/${studyId}`}
          className="font-mono text-xs uppercase tracking-[0.1em] text-muted hover:text-ink-200"
        >
          ← Résultats
        </Link>
      </header>

      <main className="flex-1 py-2">
        <Card className="p-6 shadow-soft">
          <h1 className="mb-4 font-display text-lg text-ink-100">Visualiseur DICOM</h1>
          <DicomViewer studyId={studyId} />
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
