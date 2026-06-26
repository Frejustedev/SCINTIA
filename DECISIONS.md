# DECISIONS — journal des décisions techniques

Format : une décision = contexte court + choix + justification. Le plus récent en haut.

---

## Phase 0 — Socle

### D-0.10 — Dépôt Git indépendant dans `SCINTIA/`
**Contexte :** `C:\Users\agbot\Desktop` est lui-même un dépôt Git (accidentel,
remote `presidentdubenin.git`) ; les docs Scintia y étaient **non suivies**.
**Choix :** initialiser un dépôt Git **dédié et isolé** à la racine `SCINTIA/`
(`git init -b main`), remote `origin = https://github.com/Frejustedev/SCINTIA.git`.
Le `commit` initial est local ; le `push` est effectué dès qu'un réseau est
disponible (l'environnement de build était hors-ligne).
**Justification :** historique propre, indépendant du dépôt parent — **non
modifié** (à assainir séparément côté utilisateur, p. ex. ignorer `SCINTIA/` ou
retirer le `.git` accidentel du Bureau).

### D-0.9 — Marque affichée : « Scintia »
**Choix :** l'UI affiche **Scintia** (charte + planche de marque). Le code/repo
utilise `scintia` ; `cintiAI` reste le nom interne mentionné dans `CLAUDE.md`.
**Justification :** cohérence avec `03_CHARTE_GRAPHIQUE.md` et `scintia_brand_board.html`.

### D-0.8 — Frontend : Next.js 15 (App Router) + React 19 + TypeScript
**Contexte :** la doc mentionne « Next.js 18+ », version inexistante.
**Choix :** dernière version stable, **Next.js 15 / React 19**.
**Justification :** « 18+ » est une coquille ; on pin la dernière majeure stable.

### D-0.7 — Design tokens implémentés via Tailwind + variables CSS
**Choix :** palette/typo/rayons de la charte dans `tailwind.config.ts` ; les rôles
dépendant du thème (`bg/surface/border/text/primary`) via variables CSS dans
`globals.css`. **Mode sombre par défaut**, mode clair pour rapports/PDF
(action principale en Iris `#4B4DE0`). Rayon `lg` fixé à **18px** (plage 16–20).
**Justification :** tokens fidèles à `03_CHARTE_GRAPHIQUE.md`, bascule de thème propre.

### D-0.6 — `docker-compose.yml` à la racine
**Choix :** compose à la racine (commande unique `docker compose up`), Dockerfiles
**par application** (`backend/`, `frontend/`), `infra/` pour l'init Postgres et les
configs d'appoint.
**Justification :** respecte littéralement le critère de fin Phase 0 ; léger écart
documenté vs `CLAUDE.md` (qui plaçait le compose dans `infra/`).

### D-0.5 — 4 services en Phase 0 (worker Celery différé)
**Choix :** `backend`, `frontend`, `postgres`, `redis` uniquement. Le service
`worker` (Celery) est ajouté en Phase 1 quand des tâches existent. `celery_app`
est configuré mais dormant.
**Justification :** « sans logique métier » ; le pipeline asynchrone arrive en Phase 1.

### D-0.4 — `/health` à la racine, business sous `/api/v1`
**Choix :** liveness non versionnée (`GET /health`, critère de fin Phase 0) ; les
routes métier seront préfixées `/api/v1` (convention `02_ARCHITECTURE.md`).
**Justification :** sépare la sonde de santé des routes versionnées.

### D-0.3 — Squelette modulaire complet dès maintenant (stubs)
**Choix :** créer toute l'arborescence `routers/services/services.exams/workers/
models/schemas/core` avec des `__init__.py` documentés, l'interface `ExamAnalyzer`
(contrat seul) et le `Base` SQLAlchemy — sans logique clinique.
**Justification :** fige l'architecture cible sans introduire de métier.

### D-0.2 — Backend Python 3.12, gestionnaire front npm
**Choix :** Python 3.12 (≥ 3.10 requis) ; npm côté front.
**Justification :** versions installées localement ; npm est cohérent avec les
commandes de `CLAUDE.md`.

### D-0.1 — Outillage qualité
**Choix :** ruff + black + mypy (backend) ; eslint + prettier (frontend) ;
pre-commit avec hooks standards + **blocage des fichiers DICOM** + détection de
clés privées.
**Justification :** « sécurité d'abord » et conventions de `CLAUDE.md`.

---

## Décisions à prendre (différées, hors Phase 0)

- **Visualiseur DICOM** : Cornerstone.js vs OHIF (Phase 1).
- **Moteur de dosimétrie** : MIRDcalc vs OLINDA/EXM (Phase 2).
- **Stockage objet** : volume local vs MinIO (Phase 1).
- **Licence open-source** du dépôt.
- **« 10 modules »** : clarifier le décompte (le corpus décrit 13 rubriques A–M
  + 6 modules d'examen + un pipeline en 10 étapes).
- **Statut réglementaire / circuit des données** : validation par un spécialiste
  (RGPD / loi 18-07).
