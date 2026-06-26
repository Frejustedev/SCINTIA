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
- [ ] **À faire en ligne (réseau requis) :**
  - [ ] `git push -u origin main` vers `https://github.com/Frejustedev/SCINTIA.git`.
  - [ ] `docker compose up --build` → vérifier les 4 services + `GET /health` = 200.
  - [ ] `cd backend && pip install -e ".[dev]" && pytest` (vert).
  - [ ] `cd frontend && npm install && npm run build && npm run lint` (vert).
  - [ ] Générer + committer le lockfile front (`package-lock.json`) puis passer à `npm ci`.
  - [ ] `pre-commit install` et lancer `pre-commit run --all-files`.

## Phase 1 — MVP (1 examen de bout en bout)

- [ ] Ingestion DICOM (dossier / ZIP / DICOMDIR) + file d'attente (Celery worker).
- [ ] **Anonymisation / dé-identification** (PS3.15) + table `patient_identities` chiffrée.
- [ ] Tri CT/SPECT + conversion NIfTI.
- [ ] Modèle de données SQLAlchemy (15 tables) + migrations + journal d'audit.
- [ ] Segmentation TotalSegmentator + volumes + **édition manuelle des masques**.
- [ ] Quantification SPECT basique + un examen (Octréotide/Krenning ou osseuse).
- [ ] Génération de CR (Claude, contexte anonymisé) + éditeur + validation + export PDF.
- [ ] Visualiseur DICOM (Cornerstone.js ou OHIF) + auth/RBAC (4 rôles).

## Phase 2 — Dosimétrie

- [ ] Multi-temps, TAC → TIA → dose (MIRDcalc/OLINDA), **incertitudes**, calibration caméra.

## Phase 3 — Élargissement

- [ ] Autres examens via le pattern stratégie ; suivi longitudinal.

## Phase 4 — Industrialisation

- [ ] PACS/RIS, DICOM-SR/FHIR, jeu de validation, dossier de conformité.
