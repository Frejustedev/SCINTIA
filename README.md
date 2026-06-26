# Scintia — aide à la décision en médecine nucléaire

Scintia (`cintiAI`) reçoit des fichiers **DICOM SPECT/CT**, sépare le CT du SPECT,
segmente les structures anatomiques, quantifie la fixation et la dosimétrie, et
génère un **brouillon de compte-rendu** que le médecin **relit, corrige et valide**.

> ⚠️ **Statut** : **prototype de recherche / aide à la décision**, **pas** un
> dispositif médical certifié. Le logiciel ne prend aucune décision médicale
> autonome. Tout compte-rendu porte la mention non supprimable
> « Brouillon généré par IA — à valider par le médecin » et reste sous la
> responsabilité du médecin.

---

## État du projet

**Phase 0 — Socle.** Monorepo qui démarre, **sans logique métier**. Voir
[`docs/06_ROADMAP.md`](docs/06_ROADMAP.md). Sont livrés : API FastAPI avec
`GET /health`, frontend Next.js (page d'accueil au thème de la charte, zone
d'upload **inactive** + sélecteur d'examen), `docker-compose` (backend, frontend,
postgres, redis), outillage qualité, `.gitignore` complet.

> **Code-complet, vérification d'exécution à faire.** Le socle est écrit et
> validé statiquement (compilation Python, configs, `docker compose config`).
> La vérification de bout en bout — `docker compose up`, `/health` 200, `pytest`,
> build front — reste à exécuter sur une machine avec **Docker + réseau**
> (cf. [`TODO.md`](TODO.md)).

## Prérequis

- **Docker** + **Docker Compose** (chemin recommandé).
- Pour le développement local : **Python 3.10+** (3.12 conseillé), **Node.js 18+**
  (testé sur 20/22), **npm**.

## Démarrage rapide (Docker)

```bash
# 1) Préparer l'environnement (génère .env avec des secrets locaux)
bash scripts/init-env.sh        # sous Windows : exécuter via Git Bash
#    (renseigner ANTHROPIC_API_KEY dans .env quand la génération de CR sera câblée)

# 2) Lancer toute la stack
docker compose up --build

# 3) Vérifier
#    Backend  : http://localhost:8000/health   -> 200 {"status":"ok",...}
#    API docs : http://localhost:8000/docs
#    Frontend : http://localhost:3000
```

`docker compose down` arrête la stack ; ajouter `-v` pour supprimer le volume Postgres.

## Développement local (sans Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload                        # http://localhost:8000
pytest                                               # tests
ruff check . && black --check .                      # lint / format

# Frontend
cd frontend
npm install
npm run dev                                          # http://localhost:3000
npm run lint
```

## Structure du dépôt

```
SCINTIA/
├── backend/      # FastAPI (routers / services / workers / models / schemas / core)
├── frontend/     # Next.js (App Router), React, Tailwind — thème de la charte
├── infra/        # Dockerfiles d'appoint, init Postgres
├── scripts/      # utilitaires (init-env, …)
├── docs/         # spécifications (font foi) + planche de marque
├── docker-compose.yml
├── .env.example  # variables d'environnement (jamais de secret réel)
├── CLAUDE.md · DECISIONS.md · TODO.md
```

## Qualité

- Backend : **ruff** (lint) + **black** (format), typage strict (mypy).
- Frontend : **eslint** + **prettier**.
- **pre-commit** : `pip install pre-commit && pre-commit install`
  (hooks de format + blocage des fichiers DICOM/secrets).

## Sécurité & confidentialité (non négociable)

Les règles de [`docs/05_CONTRAINTES_SECURITE.md`](docs/05_CONTRAINTES_SECURITE.md)
priment sur tout. En particulier : **dé-identification avant tout traitement**,
**aucun identifiant patient** envoyé à une API externe, chiffrement en transit et
au repos, journal d'audit. Le `.gitignore` exclut **DICOM, secrets et poids de
modèles** — ne jamais les committer.

## Documentation

Les documents de [`docs/`](docs/) font foi (contexte, spécifications, architecture,
charte graphique, modèle de données, contraintes de sécurité, roadmap, glossaire).
Les choix techniques sont consignés dans [`DECISIONS.md`](DECISIONS.md), le reste à
faire dans [`TODO.md`](TODO.md).

## Licence

À définir (le projet est destiné à être open-source — cf. charte). En attendant,
tous droits réservés.
