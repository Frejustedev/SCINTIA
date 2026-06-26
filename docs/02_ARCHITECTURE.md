# 02 — Architecture technique

> Le « comment ». À lire avec `01_SPECIFICATIONS.md` (le quoi) et `05_CONTRAINTES_SECURITE.md` (les règles de données). Vocabulaire dans `07_GLOSSAIRE.md`.

---

## 1. Principes d'architecture

1. **Anonymisation en amont de tout.** Aucune donnée n'entre dans le pipeline avant dé-identification.
2. **Pipeline par étapes, asynchrone.** L'analyse est longue (segmentation GPU) → tâches de fond + progression en temps réel.
3. **Séparation des responsabilités.** Un service = un rôle. La logique par examen est isolée (un module par type d'examen).
4. **Humain dans la boucle.** Toute sortie est un brouillon ; rien n'est « définitif » sans validation médecin.
5. **Traçabilité native.** Chaque étape, chaque version de modèle, chaque action est journalisée.
6. **Sans état côté traitement.** Les workers sont sans état ; tout l'état vit en base + stockage objet.

---

## 2. Vue d'ensemble

```
┌──────────────────────────── FRONTEND (Next.js) ─────────────────────────────┐
│  Upload → progression (WebSocket) → résultats → visualiseur → CR → export    │
└───────────────────────────────────┬──────────────────────────────────────────┘
                     REST (HTTP) + WebSocket (progression)
┌───────────────────────────────────▼──────────────────────────────────────────┐
│  API (FastAPI)                                                                │
│  Auth · routers · validation (Pydantic) · orchestration des jobs · audit     │
└───────┬───────────────────────────────────────────────────────┬──────────────┘
        │ pousse les tâches                                       │ lit/écrit
┌───────▼─────────────┐                                  ┌────────▼─────────────┐
│ Broker / Workers     │   chaîne de tâches Celery        │ PostgreSQL           │
│ (Celery + Redis)     │ ───────────────────────────────▶│ métadonnées, mesures,│
│                      │                                  │ scores, doses,       │
│  étapes du pipeline  │                                  │ versions de CR, audit│
└───────┬──────────────┘                                  └──────────────────────┘
        │ fichiers (masques, NIfTI, PDF)
┌───────▼──────────────┐        ┌─────────────────┐       ┌──────────────────────┐
│ Stockage objet       │        │ TotalSegmentator│       │ Claude API            │
│ (volume / MinIO)      │       │ (GPU)           │       │ (CR, zéro-rétention)  │
└──────────────────────┘        └─────────────────┘       └──────────────────────┘
                                ┌─────────────────┐
                                │ MIRDcalc/OLINDA │  (dosimétrie)
                                └─────────────────┘
```

---

## 3. Le pipeline de traitement (cœur du système)

Chaque étape est une **tâche Celley** chaînée. Le statut de l'examen avance à chaque étape et est publié au frontend.

| # | Étape | Service | Entrée → Sortie |
|---|---|---|---|
| 1 | **Ingestion** | `IngestionService` | DICOM bruts → série(s) parsées + métadonnées |
| 2 | **Anonymisation** | `AnonymizationService` | DICOM → DICOM dé-identifié + table de ré-identification chiffrée |
| 3 | **Séparation CT/SPECT** | `SeparationService` | séries → volume CT + volume SPECT identifiés |
| 4 | **Conversion** | `ConversionService` | DICOM → NIfTI (pour les modèles) |
| 5 | **Segmentation** | `SegmentationService` | CT → masques (117 structures) + volumes (mm³→mL) via `--statistics` |
| 6 | **Recalage** | `RegistrationService` | aligne SPECT sur CT (rigide par défaut) |
| 7 | **Quantification** | `QuantificationService` | échantillonne les coups SPECT dans les masques → activité (MBq), %AI, ratios |
| 8 | **Dosimétrie** *(si applicable)* | `DosimetryService` | (multi-temps) TAC → TIA → dose (Gy) via MIRDcalc/OLINDA + incertitude |
| 9 | **Analyse par examen** | `ExamAnalysisService` (stratégie) | applique le score adapté (Krenning, Curie, PIOPED, BSI, FEVG…) + atlas physiologique |
| 10 | **Compte-rendu** | `ReportService` | assemble un contexte **anonymisé** → Claude → brouillon structuré |
| — | **Validation** | (médecin, via l'UI) | relecture, correction, signature |
| — | **Export** | `ExportService` | PDF / DICOM-SR / FHIR (ré-identification **locale**) |

**Statuts de l'examen** : `uploaded → anonymizing → separating → converting → segmenting → registering → quantifying → dosimetry → analyzing → generating_report → ready` (+ `error` à toute étape, avec reprise possible).

**Étape 9 — pattern stratégie.** Chaque examen implémente une interface commune `ExamAnalyzer` :
```
ExamAnalyzer.analyze(study, organs, quantification, dosimetry) -> ExamResult
```
Implémentations : `BoneScanAnalyzer`, `MyocardialSpectAnalyzer`, `MibgAnalyzer`, `OctreotideAnalyzer`, `ParathyroidAnalyzer`, `LungVQAnalyzer`. Ajouter un examen = ajouter une classe, sans toucher au reste.

---

## 4. Backend (FastAPI)

```
backend/app/
├── routers/        # endpoints HTTP (studies, reports, calibration, auth, export)
├── services/       # logique métier (les services du pipeline ci-dessus)
│   └── exams/      # un analyzer par type d'examen (stratégie)
├── workers/        # tâches Celery + chaînage du pipeline
├── models/         # ORM SQLAlchemy
├── schemas/        # Pydantic (I/O API, validation)
└── core/           # config, sécurité, anonymisation, audit, exceptions
```

- **Orchestration** : un endpoint déclenche une **chaîne Celery** (`chain(task1, task2, …)`). Chaque tâche met à jour le statut et publie un événement de progression dans Redis.
- **Progression temps réel** : le worker publie sur un canal Redis → l'API relaie via **WebSocket** au frontend (ou polling `GET /status` en repli).
- **Reprise sur erreur** : une tâche qui échoue marque l'examen `error` avec le message ; on peut relancer à partir de l'étape fautive sans tout reprendre.
- **Validation** : tous les corps de requête passent par des schémas Pydantic (typage strict).

---

## 5. Contrat d'API (endpoints principaux)

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/studies` | Crée un examen, upload des DICOM (multipart), choix du type d'examen → `study_id` |
| `GET` | `/api/studies/{id}` | Métadonnées + statut |
| `WS` | `/api/studies/{id}/progress` | Flux de progression temps réel |
| `POST` | `/api/studies/{id}/analyze` | (Re)lance le pipeline |
| `GET` | `/api/studies/{id}/results` | Organes, volumes, %AI, scores, dosimétrie |
| `GET` | `/api/studies/{id}/segmentation` | Masques (références stockage) |
| `PATCH` | `/api/studies/{id}/segmentation` | Enregistre une correction de masque (recalcule volumes/quantif) |
| `GET` | `/api/studies/{id}/report` | Brouillon de compte-rendu |
| `PATCH` | `/api/studies/{id}/report` | Enregistre la version éditée |
| `POST` | `/api/studies/{id}/report/validate` | Valide / signe (verrouille, journalise) |
| `GET` | `/api/studies/{id}/export?format=pdf` | Export (ré-identification locale) |
| `POST` | `/api/calibration` | Enregistre un facteur de calibration par caméra/isotope |
| `POST` | `/api/auth/login` · `/logout` · `/me` | Authentification, rôle |

Conventions : JSON, codes HTTP standards, erreurs structurées `{code, message, details}`, pagination sur les listes. Versionner sous `/api/v1/`.

---

## 6. Frontend (Next.js)

```
frontend/
├── app/            # App Router : / (upload), /studies/[id] (résultats), /studies/[id]/report
├── components/     # UploadZone, ProgressTracker, OrganTable, DicomViewer, ReportEditor, ScoreChip…
└── lib/            # client API, hooks (useStudy, useProgress), i18n, thème (charte)
```

- **Page d'accueil** : zone de glisser-déposer + sélecteur d'examen.
- **Suivi** : composant de progression branché sur le WebSocket.
- **Résultats** : tableau d'organes (valeurs en mono), visualiseur DICOM (**Cornerstone.js** ou **OHIF**) avec superposition des masques, scores, dosimétrie.
- **Éditeur de CR** : texte riche, conserve brouillon IA + version éditée, badge « à valider » non supprimable, bouton de validation puis export.
- **Thème** : strictement selon `03_CHARTE_GRAPHIQUE.md` (mode sombre par défaut, mono pour les valeurs).

---

## 7. Stockage — qui stocke quoi

| Donnée | Où | Note |
|---|---|---|
| Métadonnées examen, mesures, scores, doses | **PostgreSQL** | structuré, requêtable |
| Versions de compte-rendu | **PostgreSQL** | brouillon IA + éditions + validée |
| Journal d'audit | **PostgreSQL** | append-only |
| Masques de segmentation, NIfTI, images annotées, PDF | **Stockage objet** (volume / MinIO) | fichiers volumineux |
| DICOM bruts | **Stockage objet, temporaire** | **supprimés après traitement** (cf. sécurité) |
| Table de ré-identification | **Stockage chiffré, accès restreint** | jamais exposée à l'API externe |

---

## 8. Intégrations externes

- **TotalSegmentator v2** — appelé en sous-processus (ou API Python) sur le CT, GPU. Option `--roi_subset` pour limiter aux organes pertinents (gain de temps). `--statistics` pour les volumes.
- **MIRDcalc / OLINDA/EXM** — moteur de dosimétrie (valeurs S). On lui fournit les TIA calculées ; on récupère les doses. *Ne pas réimplémenter les valeurs S.*
- **Claude API** — génération de CR. Contexte **strictement anonymisé** (aucun identifiant). Option zéro-rétention. Garde-fous : Claude reformule les données fournies, n'invente rien.

---

## 9. Déploiement

- **docker-compose** : services `backend`, `worker` (Celery), `frontend`, `postgres`, `redis`, `minio` (optionnel), `totalsegmentator` (ou intégré au worker GPU).
- **GPU** requis sur le worker de segmentation (CPU possible avec `--fast`/`--roi_subset`, mais lent).
- **On-premise** possible (les centres sensibles ne laissent pas sortir les images).
- Variables d'environnement pour toute la config ; secrets jamais en dur.

---

## 10. Décisions techniques & justifications (à tenir à jour dans `DECISIONS.md`)

| Décision | Pourquoi |
|---|---|
| Celery + Redis pour le pipeline | étapes longues, besoin de progression et de reprise |
| Pattern stratégie par examen | ajouter un examen sans casser l'existant |
| Stockage objet séparé de la base | fichiers lourds (masques, NIfTI) hors SQL |
| Suppression des DICOM bruts post-traitement | minimisation des données patient |
| MIRDcalc/OLINDA plutôt que réimplémentation | rigueur et validité des doses |
| Mode sombre par défaut | environnement de lecture radiologique |
