# TODO — reste à faire, par phase

Suit [`docs/06_ROADMAP.md`](docs/06_ROADMAP.md). Une phase à la fois.

> **Phase 0 : code-complet, pas encore vérifié à l'exécution.** Les items de
> construction sont faits ; les critères de fin (exécution + push) sont
> regroupés ci-dessous sous « À faire en ligne » (réseau/Docker requis).

---

## Phase 0 — Socle

- [x] Monorepo (`backend`, `frontend`, `infra`, `scripts`, `docs`).
- [x] Backend FastAPI : `GET /health`, structure modulaire, config par env.
- [x] Frontend Next.js : page d'accueil au thème, zone d'upload inactive, sélecteur d'examen.
- [x] `docker-compose.yml` : backend, frontend, postgres, redis.
- [x] Outillage qualité : ruff/black, eslint/prettier, pre-commit, `.gitignore`, `.env.example`.
- [x] `README.md`, `DECISIONS.md`, `TODO.md`.
- [x] Test backend `/health`.
- [x] `git push -u origin main` vers `https://github.com/Frejustedev/SCINTIA.git` (poussé, vérifié).
- [x] `backend` : `pip install -e ".[dev]"` + `pytest` (2 passés) + `ruff`/`black`/`mypy` verts.
- [x] `frontend` : `npm install` + `npm run build` + `npm run lint` verts ; `package-lock.json` commité ; Dockerfile en `npm ci`.
- [ ] **Reste à vérifier (démon Docker requis) :**
  - [ ] Démarrer Docker Desktop, puis `docker compose up --build` → 4 services + `GET /health` = 200 + page sur http://localhost:3000.
  - [ ] `pre-commit install` puis `pre-commit run --all-files`.

## Phase 1 — MVP scintigraphie osseuse (BSI)

**1.0 Fondations** (sécurité d'abord)
- [x] Modèle de données SQLAlchemy (15 tables) + enums centralisés.
- [x] Session DB + scaffold Alembic (migration auto-générée au 1er run Postgres).
- [x] **Service d'anonymisation DICOM** (PS3.15 : PHI, dates décalées, UID remappés, tags privés) + crypto identité (Fernet) + tests de sécurité.
- [x] Auth/RBAC (argon2 + JWT, 4 rôles) + writer de journal d'audit append-only.
- [x] Abstraction stockage objet (volume local, anti-traversal) + tests.
- [x] Routers : `auth` (login/me), `users` (bootstrap-admin/CRUD admin), `studies` (create/list/get) + tests d'intégration.
- [ ] Worker Celery (broker/result) + tâche pipeline + machine à états `study.status` *(câblé en 1.1 avec l'ingestion)*.

**1.1 Ingestion** — [x] upload multi-fichiers, parse pydicom, **anonymisation avant stockage**, **tri CT/SPECT** (par Modality), stockage objet par série + tests. [ ] reste : extraction ZIP/DICOMDIR, conversion DICOM→NIfTI (faite en 1.2 pour la segmentation), passage en tâche Celery.
**1.2 Segmentation** — [x] interface `Segmenter` + `StubSegmenter` (offline), `run_segmentation` (volumes mL → `organ_measurements`), **correction manuelle** (PATCH) + tests. [ ] adaptateur **TotalSegmentator** réel (GPU, DICOM→NIfTI, `--statistics`/`--roi_subset`), masques NIfTI stockés + visualiseur Cornerstone3D (frontend).
**1.3 Quantification + analyseur osseux** — [x] formules quantification (counts→activité, %AI, ratios) testées ; framework `ExamAnalyzer` (stratégie) + `BoneScanAnalyzer` (**proxy BSI transparent, NON validé cliniquement** + flag) + `run_analysis` + endpoint `/score` + tests ; **les 6 examens ont un analyseur** (osseux = proxy BSI ; myocarde/MIBG/octréotide/parathyroïde/V/P = frameworks flaggés `needs_clinical_validation`). [ ] **À valider avec le médecin nucléaire** : recalage SPECT/CT + échantillonnage des coups dans les masques + **détection de foyers** (données réelles) + **méthode BSI validée**.
**1.4 Compte-rendu** — [x] interface `ReportGenerator` : `TemplateReportGenerator` (offline, **sans invention**) + adaptateur `ClaudeReportGenerator` (zéro-rétention, clé requise) ; **bandeau non supprimable** ; brouillon/édition/validation (verrou, **médecin only**) + **export PDF** (ré-identification locale, audit `identity.access`/`export.pdf`) + tests. [ ] reste : appel Claude réel via prompt [`docs/08_`](docs/08_PROMPT_CR_SCINTI_OSSEUSE.md).
**1.5 Chaînage E2E** — [x] orchestration `run_pipeline` (synchrone, offline-testable) : segmentation→quantification→analyse→CR + **machine à états** ; tâche Celery `run_pipeline_task` (prod) ; endpoints `POST /analyze` + `GET /results` ; **test E2E** (ingest→analyze→results→brouillon) ; **progression WebSocket** (endpoint `/progress` + test). [ ] reste : exécution Celery réelle (broker Redis).

**Frontend (flux fonctionnel)** — [x] client API typé (`lib/api.ts`), login + bootstrap admin, nouvel examen (sélecteur + identité + upload → création/anonymisation/analyse), page résultats (table organes/volumes, score + disclaimer proxy, éditeur de CR avec **bandeau non supprimable**, validation médecin, **export PDF**), **tableau de bord des examens** + **statut live via WebSocket** ; build Next 15 + lint OK. [ ] reste : visualiseur DICOM **Cornerstone3D** + superposition masques, mode clair PDF.

> **À valider en conditions réelles (côté porteur)** : GPU NVIDIA (TotalSegmentator), DICOM de test anonymisés, clé Anthropic zéro-rétention, exécution `docker compose up` (Postgres/Redis) + interaction navigateur.

## Phase 2 — Dosimétrie

- [ ] Multi-temps, TAC → TIA → dose (MIRDcalc/OLINDA), **incertitudes**, calibration caméra.

## Phase 3 — Élargissement

- [ ] Autres examens via le pattern stratégie ; suivi longitudinal.

## Phase 4 — Industrialisation

- [ ] PACS/RIS, DICOM-SR/FHIR, jeu de validation, dossier de conformité.
