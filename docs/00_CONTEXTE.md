# 00 — Contexte du projet

> Ce document donne le « pourquoi » et le contexte métier. Il s'adresse à un développeur qui ne connaît pas forcément la médecine nucléaire. Pour le vocabulaire précis, voir `07_GLOSSAIRE.md`.

---

## 1. La médecine nucléaire en bref

La médecine nucléaire est une spécialité d'imagerie **fonctionnelle**. Contrairement au scanner ou à l'IRM qui montrent surtout l'**anatomie** (la forme des organes), elle montre le **fonctionnement** : on injecte au patient une faible quantité de **produit radioactif** (un « traceur ») qui se fixe préférentiellement sur certains tissus, puis une caméra détecte le rayonnement émis et reconstruit des images de cette fixation.

Deux modalités d'images nous concernent, presque toujours acquises ensemble sur la même machine :
- **SPECT** : l'image fonctionnelle (où le traceur s'est fixé, en 3D).
- **CT** (scanner) : l'image anatomique, qui sert à localiser précisément les fixations et à corriger les images.

L'examen complet s'appelle un **SPECT/CT**. Les fichiers sont au format **DICOM**, le standard universel de l'imagerie médicale.

**Le principe clé du projet :** le SPECT dit *« il se passe quelque chose ici »*, le CT dit *« ici = la 8e côte droite »*. En croisant les deux, on transforme une tache floue en information clinique précise.

---

## 2. Le problème qu'on résout

Aujourd'hui, pour chaque examen, le médecin nucléaire doit, à la main :
- repérer les zones de fixation anormale sur les images ;
- les localiser anatomiquement ;
- mesurer des volumes, des ratios, parfois des doses de rayonnement reçues ;
- appliquer des scores standardisés (selon l'examen) ;
- rédiger un compte-rendu structuré.

C'est **long, répétitif, dépendant de l'opérateur et peu standardisé**. Les outils existants (notamment pour la dosimétrie) sont coûteux, fragmentés, et souvent liés à un constructeur de caméra.

cintiAI automatise les étapes mécaniques (séparation, segmentation, quantification, premier jet du compte-rendu) pour que le médecin se concentre sur l'**interprétation** et la **validation**.

---

## 3. Les utilisateurs

- **Médecin nucléaire** — utilisateur principal. Charge les examens, vérifie les résultats, corrige et valide le compte-rendu. Veut gagner du temps sans perdre le contrôle.
- **Radiophysicien médical** — intervient surtout sur la **dosimétrie** (calculs de dose). Exigeant sur la rigueur des calculs et l'affichage des incertitudes.
- **Manipulateur (technicien)** — prépare et acquiert les examens, peut faire les premiers chargements. Apprécie la rapidité et les raccourcis.
- **Administrateur / chef de service** — gère les accès, les paramètres des caméras, suit l'activité.

---

## 4. Ce que fait cintiAI (le produit en une page)

1. Le médecin **dépose les fichiers DICOM** d'un examen (et choisit le type d'examen).
2. Le système **anonymise** les données, puis **sépare le CT du SPECT**.
3. Il **segmente** automatiquement les organes sur le CT (TotalSegmentator) et calcule leur **volume**.
4. Il **quantifie** la fixation du traceur (et, pour certains examens, la **dose absorbée** en Gray).
5. Selon l'examen, il applique le **score standardisé** adapté (voir périmètre ci-dessous).
6. Il envoie les **données chiffrées et anonymisées** à Claude, qui rédige un **brouillon de compte-rendu** structuré.
7. Le médecin **relit, corrige et valide**, puis **exporte** (PDF, etc.).

À aucun moment le logiciel ne décide à la place du médecin. Il propose ; le médecin tranche et signe.

---

## 5. Positionnement réglementaire (à garder en tête en permanence)

Un logiciel qui aide au diagnostic ou calcule des doses est juridiquement un **dispositif médical** (règlement UE 2017/745 MDR en Europe ; cadre national algérien à vérifier). Le faire certifier est un processus long.

**Décision pour le projet : phase de départ = prototype de recherche / aide à la décision, NON clinique.**
- Le logiciel ne pose pas de diagnostic ; il assiste un médecin qui valide tout.
- Mention « brouillon IA — à valider » non supprimable sur chaque compte-rendu.
- Journal d'audit et traçabilité dès le départ (indispensable pour une éventuelle certification future).

*Ceci n'est pas un avis juridique : le statut réglementaire et le circuit des données doivent être validés par un spécialiste.*

---

## 6. Périmètre — les 6 examens couverts

| Examen | Ce que l'IA produit |
|---|---|
| **Scintigraphie osseuse** | Détecte et localise les foyers hyperfixants + Bone Scan Index |
| **SPECT myocardique** | Fraction d'éjection (FEVG) + ischémie par territoire |
| **MIBG** | Score de Curie + dosimétrie I-131 |
| **Octréotide** | Score de Krenning + dosimétrie Lu-177 |
| **Parathyroïde** | Localisation de l'adénome |
| **Poumon V/P** | Probabilité d'embolie pulmonaire (PIOPED) |

Détail complet de chaque module dans `01_SPECIFICATIONS.md` (section 4) et termes définis dans `07_GLOSSAIRE.md`.

Composant transversal : l'**atlas de biodistribution physiologique** (où chaque traceur se fixe *normalement*), qui évite de prendre une fixation normale pour une lésion.

---

## 7. Le flux de travail type (une journée au service)

> Un médecin arrive le matin avec 15 examens SPECT/CT à interpréter.

1. Il sélectionne un patient, dépose le dossier DICOM, choisit « Octréotide ».
2. Pendant l'analyse (barre de progression), il passe au cas suivant.
3. Quand c'est prêt : il ouvre la page résultats — tableau des organes, volumes, score de Krenning, dosimétrie Lu-177, et le brouillon de compte-rendu.
4. Il vérifie les segmentations (en corrige une si besoin), ajuste deux phrases du compte-rendu.
5. Il valide, signe, exporte le PDF vers le dossier patient.
6. Temps passé : quelques minutes au lieu de beaucoup plus, avec un rendu standardisé.

C'est ce parcours que toute l'application doit rendre fluide.
