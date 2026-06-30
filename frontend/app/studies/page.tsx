"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/Logo";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { getToken, listStudies, type StudyRead } from "@/lib/api";

type Tone = "neutral" | "ok" | "info" | "warn" | "crit";

function statusTone(status: string): Tone {
  if (status === "ready") return "ok";
  if (status === "error") return "crit";
  return "info";
}

export default function StudiesPage() {
  const router = useRouter();
  const [studies, setStudies] = useState<StudyRead[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    listStudies()
      .then(setStudies)
      .catch((err) => setError((err as Error).message));
  }, [router]);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={32} />
          <span className="font-display text-xl font-semibold tracking-tight text-ink-100">
            Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
          </span>
        </Link>
        <Link
          href="/studies/new"
          className="inline-flex min-h-[44px] items-center justify-center rounded-md bg-grad-hot px-4 text-sm font-medium text-ink-900 transition duration-200 ease-soft hover:opacity-95"
        >
          Nouvel examen
        </Link>
      </header>

      <main className="flex-1 py-2">
        <h1 className="mb-4 font-display text-2xl text-ink-100">Examens</h1>
        {error ? <p className="mb-4 text-sm text-crit">{error}</p> : null}

        <Card className="p-6 shadow-soft">
          {studies.length === 0 ? (
            <p className="text-sm text-muted">
              Aucun examen pour l&apos;instant. Lancez-en un depuis « Nouvel examen ».
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-xs uppercase tracking-[0.1em] text-muted">
                  <th className="pb-2">Pseudonyme</th>
                  <th className="pb-2">Examen</th>
                  <th className="pb-2">Statut</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody>
                {studies.map((study) => (
                  <tr key={study.id} className="border-t border-border">
                    <td className="py-2 font-mono text-ink-200">{study.patient_pseudonym}</td>
                    <td className="py-2 text-ink-200">{study.exam_type}</td>
                    <td className="py-2">
                      <Badge tone={statusTone(study.status)}>{study.status}</Badge>
                    </td>
                    <td className="py-2 text-right">
                      <Link
                        href={`/studies/${study.id}`}
                        className="font-mono text-xs uppercase tracking-[0.1em] text-iris hover:underline"
                      >
                        Ouvrir →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </main>
    </div>
  );
}
