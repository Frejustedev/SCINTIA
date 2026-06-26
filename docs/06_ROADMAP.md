# 06 — Feuille de route (Scintia)

> Le séquençage du développement. À suivre **phase par phase** : ne jamais tout construire d'un coup. Chaque phase a un objectif et un critère de fin clair. Périmètre détaillé → `01_SPECIFICATIONS.md`.

---

## Principe

Tout construire d'un coup représente des années de travail à plusieurs. Ce séquençage donne de la valeur vite, en réduisant le risque à chaque étape. **Claude Code doit demander la validation du plan avant de coder chaque phase.**

---

## Phase 0 — Socle (2–4 semaines)
**Objectif :** un monorepo qui démarre, sans IA.
- Upload DICOM + anonymisation + tri CT/SPECT + visualiseur basique.
- Backend FastAPI (`/health`, structure modulaire), frontend Next.js (page d'accueil + zone d'upload), docker-compose (backend, frontend, postgres, redis).
- Outillage qualité (linters, pré-commit), `.gitignore` complet, README.

**Fin de phase :** `docker-compose up` lance tout ; `/health` répond ; la page d'accueil s'affiche au thème de la charte ; un tiers peut tout relancer depuis le README.

---

## Phase 1 — MVP : 1 seul examen (6–10 semaines)
**Objectif :** prouver la chaîne complète, de bout en bout, sur un examen.
- Choisir **un** examen à fort impact et géométrie simple — recommandation : **Octréotide (score de Krenning)** ou **scintigraphie osseuse**.
- Segmentation TotalSegmentator + volumes + quantification SPECT basique.
- Génération du CR par Claude + éditeur + export PDF.
- **Édition manuelle des masques** (indispensable).

**Fin de phase :** un médecin peut charger un examen du type choisi, voir organes/volumes/score, corriger une segmentation, obtenir un brouillon de CR, le valider et l'exporter en PDF.

---

## Phase 2 — Dosimétrie correcte (8–12 semaines)
**Objectif :** une dosimétrie rigoureuse, pas une approximation cachée.
- Support **multi-temps** + courbe activité-temps + intégration → dose via MIRDcalc/OLINDA.
- Facteurs de calibration par caméra.
- **Affichage des incertitudes**. Mode single-time-point clairement étiqueté « approximatif ».

**Fin de phase :** pour un traitement Lu-177/I-131 avec plusieurs temps, le physicien obtient des doses aux organes à risque avec leur incertitude et la méthode utilisée.

---

## Phase 3 — Élargissement (itératif)
**Objectif :** couvrir les autres examens, un par un.
- Ajout des autres modules (myocarde, MIBG, parathyroïde, V/P) via le pattern stratégie — sans casser l'existant.
- Suivi longitudinal, comparaison aux antériorités.

**Fin de phase :** les 6 examens du périmètre sont couverts, chacun avec son score standardisé.

---

## Phase 4 — Industrialisation
**Objectif :** passer du prototype à un outil déployable.
- Intégration PACS/RIS, export DICOM-SR/FHIR, gestion fine des rôles.
- **Jeu de validation** (cas de référence), dossier de conformité, préparation d'un éventuel marquage dispositif médical.

**Fin de phase :** déploiement reproductible, traçabilité complète, base de validation constituée.

---

## Points de vigilance critiques

1. **Réglementaire d'abord.** Décider tôt si l'on vise « recherche » ou « dispositif médical certifié ». Ça conditionne tout le reste (documentation, validation, responsabilité).
2. **Dosimétrie = multi-temps + calibration.** Un SPECT unique ne donne pas une vraie dose. Ne jamais livrer une dose en Gy sans préciser la méthode et l'incertitude.
3. **Données patient.** Anonymiser avant traitement ; ne jamais faire sortir d'identifiant vers l'API. Activer la zéro-rétention. RGPD / loi 18-07.
4. **Humain dans la boucle.** Le médecin valide et signe. L'IA propose, elle ne décide pas. Mention non supprimable sur chaque CR.
5. **Segmentation corrigeable.** Sans édition manuelle des masques, l'outil est inutilisable en pratique.
6. **Claude ne doit pas inventer.** Le CR reformule uniquement les données fournies ; pas de mesure « hallucinée ».
7. **Validation scientifique.** Constituer un jeu de cas de référence pour comparer les sorties IA aux mesures manuelles — c'est ce qui rendra l'outil crédible (et publiable).

---

## Ce qu'il faut pour démarrer

- **Python 3.10+** (backend) et **Node.js 18+** (frontend).
- **GPU NVIDIA** (≥ 8 Go) recommandé pour TotalSegmentator.
- **Clé API Anthropic** (génération des CR) — avec option zéro-rétention.
- **Moteur de dosimétrie** : MIRDcalc (gratuit) ou licence OLINDA/EXM.
- **Fichiers DICOM de test** anonymisés (idéalement un de chaque type d'examen, et pour la dosimétrie, une série multi-temps).
- Un **radiophysicien** dans la boucle pour valider le module dosimétrie.
