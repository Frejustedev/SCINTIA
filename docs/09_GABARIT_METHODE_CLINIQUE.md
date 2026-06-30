# 09 — Gabarit de spécification d'une méthode clinique

> **Pourquoi ce document existe.** Scintia **n'invente jamais** une règle clinique
> (score, seuil, formule de dose). Tant qu'une méthode n'est pas **validée et
> consignée ici** par le médecin nucléaire (et le radiophysicien pour la
> dosimétrie), l'application n'affiche qu'un **proxy explicitement étiqueté
> « non validé cliniquement »** ou un cadre vide.
>
> **Comment l'utiliser.** Pour chaque score/examen, copiez le bloc *Gabarit*
> ci-dessous, remplissez **tous** les champs, citez **au moins une référence**,
> faites **signer**. Une fois rempli et signé, le développeur l'implémente
> **fidèlement** (aucune valeur n'est devinée). Les champs « À COMPLÉTER » sont des
> emplacements : ne pas y mettre de valeur inventée.

---

## Gabarit (à copier pour chaque score)

### Examen / score : `À COMPLÉTER`

| Champ | À renseigner |
|---|---|
| **Responsable de la validation** | Nom, fonction (médecin nucléaire / radiophysicien) |
| **Date de validation** | AAAA-MM-JJ |
| **Référence(s)** *(obligatoire)* | Article(s) / guideline(s) — ex. EANM, SNMMI, société savante |
| **Statut** | proxy non validé · validé cliniquement |

**1. Objectif clinique.** Ce que le score mesure et la décision qu'il éclaire.
`À COMPLÉTER`

**2. Entrées requises** (parmi les données déjà produites par l'app — cocher) :
- [ ] Volumes par organe (mL) — `organ_measurements.volume_ml`
- [ ] Activité par organe (MBq) — `organ_measurements.activity_mbq`
- [ ] % activité injectée (%AI) — `organ_measurements.pct_injected_activity`
- [ ] Concentration (MBq/mL) — `organ_measurements.concentration_mbq_ml`
- [ ] Coups SPECT échantillonnés dans les masques
- [ ] Ratios lésion/fond — `lesions.ratio`
- [ ] Autre : `À COMPLÉTER`

**3. Pré-traitements nécessaires** (recalage SPECT/CT, seuillage, normalisation…).
`À COMPLÉTER`

**4. Algorithme / formule** (précis, étape par étape, sans ambiguïté).
`À COMPLÉTER`

**5. Catégorisation / seuils** (table valeur → catégorie, si applicable).

| Intervalle / condition | Catégorie / interprétation |
|---|---|
| `À COMPLÉTER` | `À COMPLÉTER` |

**6. Détection de foyers** (si applicable) : critère de détection, seuil
(ratio/contraste), méthode de localisation anatomique (via le CT segmenté).
`À COMPLÉTER`

**7. Cas limites & données manquantes** : conduite à tenir si une entrée manque,
si le volume est nul, si la qualité est insuffisante (→ ne pas afficher / signaler).
`À COMPLÉTER`

**8. Unités & arrondis** : unité de sortie, nombre de décimales.
`À COMPLÉTER`

**9. Jeu de cas de validation** (≥ 5 cas : entrées → sortie attendue, cotée
manuellement par le validateur — sert de tests automatiques).

| Cas | Entrées | Sortie attendue |
|---|---|---|
| 1 | `À COMPLÉTER` | `À COMPLÉTER` |

**10. Mention imposée dans le compte-rendu** (texte exact à afficher, en plus du
bandeau « Brouillon généré par IA — à valider par le médecin »).
`À COMPLÉTER`

**Signature du validateur :** `___________________`  **Date :** `__________`

---

## Fiches à remplir (périmètre actuel)

> Les **noms de référence** ci-dessous ne sont que des **pointeurs** vers la méthode
> standard à utiliser — **aucune valeur n'est fournie ici**, elle doit venir du
> validateur et de la littérature citée.

1. **Scintigraphie osseuse — BSI + détection de foyers.** Remplace le proxy
   `bsi_proxy` actuel. Référence à préciser (méthode BSI validée, ex. type aBSI).
2. **Octréotide / SSTR — score de Krenning** (échelle visuelle 0–4 vs foie/rate).
3. **MIBG — score de Curie et/ou SIOPEN** (cotation segmentale).
4. **Poumon V/P — critères PIOPED** (analyse des discordances ventilation/perfusion).
5. **Myocarde — FEVG + SSS / SRS / SDS** (modèle 17 segments, acquisition *gated*).
6. **Parathyroïde — localisation d'adénome** (double phase + SPECT/CT).
7. **Dosimétrie (Phase 2) — MIRD multi-temps** : TAC → activité cumulée (TIA) →
   dose (Gy) **avec incertitude**, facteurs de calibration caméra.
   **Radiophysicien obligatoire.**

> Dès qu'une fiche est remplie et signée, transmettez-la : son algorithme est
> implémenté dans l'analyseur correspondant (`backend/app/services/exams/…`) avec
> ses cas de validation convertis en tests, sans aucune interprétation ajoutée.
