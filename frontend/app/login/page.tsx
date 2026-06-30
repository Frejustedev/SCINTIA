"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { bootstrapAdmin, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [bootstrap, setBootstrap] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (bootstrap) {
        await bootstrapAdmin(email, fullName || "Administrateur", password);
      }
      await login(email, password);
      router.push("/studies/new");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <div className="mb-8 flex items-center gap-3">
        <Logo size={36} />
        <span className="font-display text-2xl font-semibold tracking-tight text-ink-100">
          Scinti<span className="bg-grad-hot bg-clip-text text-transparent">a</span>
        </span>
      </div>

      <Card className="p-6 shadow-soft">
        <h1 className="mb-1 font-display text-lg text-ink-100">
          {bootstrap ? "Créer le premier administrateur" : "Connexion"}
        </h1>
        <p className="mb-5 text-sm text-muted">
          Aide à la décision en médecine nucléaire — accès réservé.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {bootstrap ? (
            <Input
              placeholder="Nom complet"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
            />
          ) : null}
          <Input
            type="email"
            placeholder="E-mail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />
          <Input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          {error ? (
            <p role="alert" className="text-sm text-crit">
              {error}
            </p>
          ) : null}
          <Button type="submit" disabled={busy}>
            {busy ? "Veuillez patienter…" : bootstrap ? "Créer et se connecter" : "Se connecter"}
          </Button>
        </form>

        <button
          type="button"
          onClick={() => setBootstrap((value) => !value)}
          className="mt-4 font-mono text-xs uppercase tracking-[0.1em] text-iris hover:underline"
        >
          {bootstrap
            ? "← Revenir à la connexion"
            : "Première installation : créer un administrateur"}
        </button>
      </Card>
    </div>
  );
}
