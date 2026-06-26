# cintiAI — Instructions permanentes (Claude Code)

> Ce fichier est rechargé à **chaque session**. Il fait foi avec les documents du dossier `/docs`. Lis-le en entier avant toute action.

---

## Le projet en une phrase

cintiAI est une application web d'**aide à la décision** pour la médecine nucléaire : elle reçoit des fichiers DICOM SPECT/CT, sépare automatiquement le CT du SPECT, segmente les structures anatomiques (TotalSegmentator), quantifie la fixation et la dosimétrie, et génère un **brouillon de compte-rendu** que le médecin relit, corrige et valide.

Détail métier → `00_CONTEXTE.md`. Fonctionnalités → `01_SPECIFICATIONS.md`. Vocabulaire → `07_GLOSSAIRE.md`.

---

## Statut & contraintes NON NÉGOCIABLES

Ces règles s'appliquent à **tout** le code, sans exception.

1. **Statut réglementaire** — prototype de **recherche / aide à la décision**, PAS un dispositif médical certifié. Aucune décision médicale autonome.
2. **Humain dans la boucle** — tout compte-rendu est relu, corrigé et validé par le médecin. La mention « **Brouillon généré par IA — à valider par le médecin** » est présente et **non supprimable**.
3. **Données patient** — **anonymisation / dé-identification AVANT tout traitement**. Aucun identifiant direct ne sort vers une API externe (Claude inclus). Chiffrement en transit et au repos.
4. **Aucune invention** — la génération de compte-rendu **reformule uniquement les données fournies**. Jamais de mesure, score ou constat inventé.
5. **Traçabilité** — journal d'audit + versionnage des modèles et paramètres de calcul, dès le départ.
6. **Git propre** — **jamais** de DICOM, de secrets/clés, ni de poids de modèles dans le dépôt.

---

## Stack (ne pas changer sans validation explicite)

**Backend** — Python 3.10+, FastAPI, Celery + Redis (jobs longs), PostgreSQL, `pydicom`, TotalSegmentator v2, SimpleITK / nibabel.
**Frontend** — Next.js 18+, React, Tailwind CSS, visualiseur DICOM (Cornerstone.js ou OHIF).
**Infra** — Docker / docker-compose. GPU recommandé pour la segmentation.
**IA** — SDK Anthropic pour les comptes-rendus (option zéro-rétention).

---

## Structure du dépôt

```
cintiAI/
├── backend/                # FastAPI, Python 3.10+
│   ├── app/
│   │   ├── routers/        # endpoints HTTP
│   │   ├── services/       # logique métier (DICOM, segmentation, dosimétrie, CR)
│   │   ├── models/         # modèles ORM (SQLAlchemy)
│   │   ├── schemas/        # schémas Pydantic (I/O API)
│   │   ├── workers/        # tâches Celery
│   │   └── core/           # config, sécurité, anonymisation, audit
│   └── tests/
├── frontend/               # Next.js 18+, React, Tailwind
│   ├── app/                # pages (App Router)
│   ├── components/         # composants UI
│   └── lib/                # appels API, utilitaires
├── infra/                  # docker-compose, Dockerfiles
├── scripts/                # scripts utilitaires
├── docs/                   # documentation (ce dossier)
├── DECISIONS.md            # journal des décisions techniques
└── TODO.md                 # reste à faire, par phase
```

---

## Conventions de code

- **Code, variables et commentaires techniques en anglais** ; **textes utilisateur en français** (i18n prévue pour arabe + anglais).
- Backend : `ruff` + `black`. Frontend : `eslint` + `prettier`. Pré-commit configuré.
- **Pas de secret en dur** : tout par variables d'environnement (`.env.example` versionné, `.env` ignoré).
- Typage strict : type hints Python partout, TypeScript côté front.
- Fonctions courtes, responsabilités séparées (un service = un rôle).

---

## Méthode de travail (impérative)

- **Par phases.** Jamais tout d'un coup. On suit `06_ROADMAP.md`, **une phase à la fois**.
- **Plan avant code.** Pour toute phase ou tâche structurante, propose d'abord un **plan court** (fichiers, approche, risques) et **attends la validation**.
- **Incrémental.** Commits atomiques, messages clairs.
- **Tests au fil de l'eau**, en priorité sur le backend critique : anonymisation, tri CT/SPECT, volumes, doses.
- **Sécurité d'abord** : à chaque manipulation de données patient, vérifier explicitement l'anonymisation.
- **Respecter la charte** (`03_CHARTE_GRAPHIQUE.md`) pour toute l'UI.
- **Demander** si une spec est ambiguë ou manquante — surtout une exigence médicale. Ne jamais inventer une règle clinique.
- **Tenir à jour** `DECISIONS.md` et `TODO.md`.

---

## Commandes utiles (à compléter au fil du projet)

- Lancer toute la stack : `docker-compose up`
- Tests backend : `cd backend && pytest`
- Lint backend : `ruff check . && black --check .`
- Lint frontend : `cd frontend && npm run lint`

---

## Documents de référence (`/docs`)

| Fichier | Contenu |
|---|---|
| `00_CONTEXTE.md` | Métier, problème, utilisateurs, positionnement |
| `01_SPECIFICATIONS.md` | Fonctionnalités détaillées |
| `02_ARCHITECTURE.md` | Technique, flux de données, choix d'implémentation |
| `03_CHARTE_GRAPHIQUE.md` | Design system (couleurs, typo, composants, ton) |
| `04_MODELE_DONNEES.md` | Entités, schéma de base |
| `05_CONTRAINTES_SECURITE.md` | Anonymisation, confidentialité, conformité, audit |
| `06_ROADMAP.md` | Phases de développement + critères de fin |
| `07_GLOSSAIRE.md` | Vocabulaire de médecine nucléaire |

---

## Lignes rouges — ce que tu ne dois JAMAIS faire

- Commiter des DICOM, des secrets/clés API, ou des poids de modèles.
- Envoyer un identifiant patient (nom, date de naissance, ID) vers une API externe.
- Inventer ou extrapoler une mesure médicale dans un compte-rendu.
- Supprimer ou masquer la mention « brouillon IA — à valider ».
- Présenter une sortie du logiciel comme une décision ou un diagnostic médical.
- Changer la stack ou prendre une décision d'architecture majeure sans validation.
- Tout construire d'un coup au lieu de suivre la roadmap.
