"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  editReport,
  exportPdf,
  getReport,
  getResults,
  getToken,
  progressSocketUrl,
  validateReport,
  type ReportRead,
  type StudyResults,
} from "@/lib/api";

function formatVolume(value: string | number | null): string {
  if (value === null) return "—";
  const numeric = typeof value === "string" ? Number.parseFloat(value) : value;
  return Number.isFinite(numeric) ? numeric.toFixed(1).replace(".", ",") : "—";
}

export default function StudyResultsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const studyId = params.id;

  const [results, setResults] = useState<StudyResults | null>(null);
  const [report, setReport] = useState<ReportRead | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [liveStatus, setLiveStatus] = useState<string | null>(null);

  const load = useCallback(async () => {
    const data = await getResults(studyId);
    setResults(data);
    try {
      const current = await getReport(studyId);
      setReport(current);
      setDraft(current.content ?? "");
    } catch {
      /* no report drafted yet */
    }
  }, [studyId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    load().catch((err) => setError((err as Error).message));
  }, [load, router]);

  useEffect(() => {
    if (!getToken()) return undefined;
    const socket = new WebSocket(progressSocketUrl(studyId));
    socket.onmessage = (event) => {
      let data: { status?: string };
      try {
        data = JSON.parse(event.data as string) as { status?: string };
      } catch {
        return;
      }
      if (typeof data.status === "string") {
        setLiveStatus(data.status);
        if (data.status === "ready") {
          load().catch(() => undefined);
        }
      }
    };
    // Auth-rejected (1008) or network failure: degrade silently, the page still loaded once.
    socket.onerror = () => undefined;
    return () => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
    };
  }, [studyId, load]);

  async function handleSave() {
    setBusy(true);
    setError(null);
    try {
      const updated = await editReport(studyId, draft);
      setReport(updated);
      setDraft(updated.content ?? "");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleValidate() {
    setBusy(true);
    setError(null);
    try {
      const updated = await validateReport(studyId);
      setReport(updated);
      setDraft(updated.content ?? "");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    setError(null);
    try {
      const blob = await exportPdf(studyId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `CR_${studyId}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const score = results?.score ?? null;
  const proxyDisclaimer =
    score && typeof score.details?.disclaimer === "string" ? score.details.disclaimer : null;
  const validated = report?.status === "validated";

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={32} />
          <span className="font-display text-xl font-semibold tracking-tight text-ink-100">
            Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href={`/studies/${studyId}/viewer`}
            className="font-mono text-xs uppercase tracking-[0.1em] text-muted hover:text-ink-200"
          >
            Visualiseur DICOM →
          </Link>
          {results ? (
            <Badge tone="info">
              {results.study.exam_type} · {liveStatus ?? results.study.status}
            </Badge>
          ) : null}
        </div>
      </header>

      {error ? (
        <p role="alert" className="mb-4 text-sm text-crit">
          {error}
        </p>
      ) : null}

      <main className="grid flex-1 gap-6 py-2 lg:grid-cols-2">
        <Card className="p-6 shadow-soft">
          <h2 className="mb-4 font-display text-lg text-ink-100">Organes &amp; volumes</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left font-mono text-xs uppercase tracking-[0.1em] text-muted">
                <th className="pb-2">Structure</th>
                <th className="pb-2 text-right">Volume (mL)</th>
              </tr>
            </thead>
            <tbody>
              {(results?.organs ?? []).map((organ) => (
                <tr key={organ.id} className="border-t border-border">
                  <td className="py-1.5 text-ink-200">
                    {organ.organ_name}
                    {organ.segmentation_corrected ? (
                      <span className="ml-2 font-mono text-xs text-ok">corrigé</span>
                    ) : null}
                  </td>
                  <td className="py-1.5 text-right font-mono tabular-nums text-ink-100">
                    {formatVolume(organ.volume_ml)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {results && results.organs.length === 0 ? (
            <p className="text-sm text-muted">Aucune mesure (lancez l&apos;analyse).</p>
          ) : null}

          {score ? (
            <div className="mt-6 border-t border-border pt-4">
              <p className="font-mono text-xs uppercase tracking-[0.1em] text-muted">
                Score — {score.score_type.toUpperCase()}
              </p>
              <p className="mt-1 font-mono text-2xl tabular-nums text-ink-100">{score.value}</p>
              {proxyDisclaimer ? (
                <div className="mt-2">
                  <Badge tone="warn">à valider cliniquement</Badge>
                  <p className="mt-2 text-xs text-muted">{proxyDisclaimer}</p>
                </div>
              ) : null}
            </div>
          ) : null}
        </Card>

        <Card className="p-6 shadow-soft">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-lg text-ink-100">Compte-rendu</h2>
            {validated ? (
              <Badge tone="ok">validé</Badge>
            ) : (
              <Badge tone="ai-draft">Brouillon IA — à valider</Badge>
            )}
          </div>

          {report ? (
            <>
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                readOnly={validated}
                rows={16}
                className="w-full rounded-md border border-border bg-ink-850 p-3 font-mono text-xs leading-relaxed text-ink-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris"
              />
              <div className="mt-4 flex flex-wrap gap-3">
                {!validated ? (
                  <>
                    <Button variant="secondary" onClick={handleSave} disabled={busy}>
                      Enregistrer
                    </Button>
                    <Button onClick={handleValidate} disabled={busy}>
                      Valider et signer
                    </Button>
                  </>
                ) : (
                  <Button variant="signal" onClick={handleExport}>
                    Exporter en PDF
                  </Button>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted">
              Aucun brouillon disponible. Lancez l&apos;analyse depuis un nouvel examen.
            </p>
          )}
        </Card>
      </main>

      <footer className="border-t border-border py-6">
        <p className="text-sm text-muted">
          Aide à la décision — le médecin relit, corrige, valide et signe. Prototype de recherche,
          non destiné au diagnostic autonome.
        </p>
      </footer>
    </div>
  );
}
