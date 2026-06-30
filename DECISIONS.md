# DECISIONS — journal des décisions techniques

Format : une décision = contexte court + choix + justification. Le plus récent en haut.

---

## Phase 1 — MVP scintigraphie osseuse

### D-1.1 — Examen MVP : scintigraphie osseuse (BSI)
**Choix :** la chaîne de bout en bout est prouvée d'abord sur la **scintigraphie
osseuse** (sortie : cartographie des foyers + Bone Scan Index).
**Justification :** examen le plus courant et **prompt de CR déjà rédigé**
([`docs/08_PROMPT_CR_SCINTI_OSSEUSE.md`](docs/08_PROMPT_CR_SCINTI_OSSEUSE.md)).
La détection de foyers + BSI est plus exigeante qu'un Krenning ; traitée
progressivement en 1.3.

### D-1.2 — Anonymisation DICOM
**Choix :** service `app/services/anonymization.py` — PHI de Type 2 blanchis,
Type 3 supprimés, tags privés retirés ; **dates décalées d'un offset cohérent
par patient** (intervalles préservés pour la dosimétrie multi-temps) ; **UID
régénérés via un mapping partagé** (liaison CT/SPECT conservée). L'identité réelle
capturée est chiffrée (Fernet, `app/core/crypto.py`) pour `patient_identities`.
**Clé :** une clé Fernet valide est **dérivée** de `IDENTITY_ENCRYPTION_KEY`
(SHA-256 → base64), pour découpler le format du secret de l'exigence Fernet.
**À finaliser (Pass B) :** la **persistance/dérivation de l'offset par patient**
(aujourd'hui passé au service) pour garantir sa stabilité entre examens.

### D-1.3 — Migrations : Alembic, autogénérées au runtime
**Choix :** scaffold Alembic (`alembic.ini`, `alembic/env.py` câblé sur
`Base.metadata` + URL via settings). La **migration initiale est générée au
premier run avec Postgres** (`alembic revision --autogenerate`), pas hors-ligne.

### D-1.4 — Types de colonnes portables (PG ↔ SQLite)
**Choix :** types fidèles à Postgres mais testables sur SQLite via
`with_variant` : `JSONB`→`JSON`, `INET`→`String(45)`, enums **natifs** avec
`values_callable` (stocke les `.value`, ex. `Tc-99m`), `UUID`/`timestamptz`/`bytea`
via les types génériques SQLAlchemy 2.0.

---

## Phase 0 — Socle

### D-0.14 — « 10 modules » = les 10 étapes du pipeline
**Contexte :** le prompt évoque « l'application complète à 10 modules ».
**Choix :** interpréter « 10 modules » comme les **10 étapes du pipeline**
(`02_ARCHITECTURE.md` §3 : Ingestion → Anonymisation → Séparation → Conversion →
Segmentation → Recalage → Quantification → Dosimétrie → Analyse par examen →
Compte-rendu).
**Justification :** réconcilie le prompt et les specs sans rien inventer. Les
autres regroupements restent distincts : **13 rubriques fonctionnelles A–M**
(`01_SPECIFICATIONS.md`) et **6 analyseurs d'examen** (pattern stratégie).
À confirmer avec le porteur si une autre lecture était visée.

### D-0.13 — Licence : Apache-2.0
**Choix :** publier le dépôt sous **Apache-2.0** (fichier `LICENSE` ajouté ;
`backend/pyproject.toml` mis à jour).
**Justification :** permissive **avec clause de brevet** (utile pour un logiciel
médical/régulé), cohérente avec les dépendances (TotalSegmentator est Apache-2.0),
compatible avec une éventuelle certification/commercialisation. Révisable avant
toute contribution externe ; **revue juridique conseillée** avant usage clinique.

### D-0.12 — Moteur de dosimétrie : MIRDcalc par défaut, derrière une abstraction
**Choix :** **MIRDcalc** (gratuit, SNMMI, MIRD Pamphlet 28) comme moteur par
défaut, exposé via une interface `DosimetryEngine` ; **OLINDA/EXM** branchable en
option (licence). Ne **pas** réimplémenter les valeurs S.
**Justification :** cohérent avec un prototype ouvert, abstraction pour les
centres disposant d'OLINDA. **À valider par le radiophysicien** en Phase 2
(exigence `06_ROADMAP.md`).

### D-0.11 — Visualiseur DICOM : Cornerstone3D
**Choix :** **Cornerstone3D** (`@cornerstonejs/core` + `@cornerstonejs/tools`),
embarqué dans nos composants React, plutôt qu'OHIF.
**Justification :** bibliothèque intégrable avec contrôle total de l'UI (charte,
superposition de masques, défilement/fenêtrage/MIP) ; OHIF est une **application
complète** (bâtie sur Cornerstone), plus lourde à personnaliser pour notre page
résultats sur mesure. Révisable en Phase 1.

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

- **Stockage objet** : volume local vs MinIO (Phase 1).
- **Statut réglementaire / circuit des données** : validation par un spécialiste
  (RGPD / loi 18-07) — hors compétence logicielle.

> Résolues le 2026-06-26 : visualiseur DICOM → D-0.11 ; moteur dosimétrie →
> D-0.12 ; licence → D-0.13 ; « 10 modules » → D-0.14.
