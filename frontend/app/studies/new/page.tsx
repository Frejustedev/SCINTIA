"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { analyze, createStudy, getToken, uploadFiles } from "@/lib/api";
import { EXAM_OPTIONS } from "@/lib/exams";

export default function NewStudyPage() {
  const router = useRouter();
  const [examType, setExamType] = useState<string>("bone");
  const [name, setName] = useState("");
  const [patientId, setPatientId] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (files.length === 0) {
      setError("Sélectionnez des fichiers DICOM (SPECT/CT).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setProgress("Création de l'examen…");
      const study = await createStudy(examType, {
        name: name || undefined,
        patient_id: patientId || undefined,
        birth_date: birthDate || undefined,
      });
      setProgress("Anonymisation et envoi des fichiers…");
      await uploadFiles(study.id, files);
      setProgress("Analyse en cours (segmentation, score, brouillon de compte-rendu)…");
      await analyze(study.id);
      router.push(`/studies/${study.id}`);
    } catch (err) {
      setError((err as Error).message);
      setProgress(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col px-6">
      <header className="flex items-center justify-between py-6">
        <Link href="/" className="flex items-center gap-3">
          <Logo size={32} />
          <span className="font-display text-xl font-semibold tracking-tight text-ink-100">
            Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
          </span>
        </Link>
      </header>

      <main className="flex-1 py-6">
        <h1 className="mb-1 font-display text-2xl text-ink-100">Nouvel examen</h1>
        <p className="mb-6 text-sm text-muted">
          L&apos;identité saisie est chiffrée côté serveur ; les fichiers sont anonymisés avant tout
          traitement.
        </p>

        <Card className="p-6 shadow-soft">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-[0.1em] text-muted">
                Type d&apos;examen
              </label>
              <select
                value={examType}
                onChange={(e) => setExamType(e.target.value)}
                className="min-h-[44px] w-full rounded-md border border-border bg-ink-850 px-3 text-sm text-ink-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris"
              >
                {EXAM_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label} — {option.tracer}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <Input
                placeholder="Nom du patient"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <Input
                placeholder="Identifiant"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
              />
              <Input
                placeholder="Naissance (AAAAMMJJ)"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
              />
            </div>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                setFiles(Array.from(e.dataTransfer.files));
              }}
              className="rounded-lg border border-dashed border-border bg-ink-850/50 px-6 py-8 text-center"
            >
              <p className="text-sm text-muted">Glissez les fichiers DICOM ici, ou</p>
              <label className="mt-2 inline-block cursor-pointer font-mono text-xs uppercase tracking-[0.1em] text-iris hover:underline">
                parcourir…
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                />
              </label>
              {files.length > 0 ? (
                <p className="mt-2 font-mono text-xs text-ink-300">
                  {files.length} fichier(s) sélectionné(s)
                </p>
              ) : null}
            </div>

            {progress ? <p className="font-mono text-xs text-info">{progress}</p> : null}
            {error ? (
              <p role="alert" className="text-sm text-crit">
                {error}
              </p>
            ) : null}

            <Button type="submit" variant="signal" disabled={busy}>
              {busy ? "Traitement…" : "Lancer l'analyse"}
            </Button>
          </form>
        </Card>
      </main>
    </div>
  );
}
