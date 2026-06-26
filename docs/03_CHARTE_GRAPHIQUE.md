# 03 — Charte graphique (design system)

> Source de vérité pour toute l'interface. Implémenter ces tokens tels quels (variables CSS / config Tailwind). La planche visuelle de référence est `scintia_brand_board.html`.

---

## 1. Marque

- **Nom** : **Scintia** *(modulable — alternatives : Scintilla, Becq)*.
- **Concept directeur** : **Structure × Fonction**. L'anatomie (CT, froid, structuré) rencontre la fonction (SPECT, chaud, lumineux). Tout découle de cette fusion.
- **Origine** : *scintilla* (latin) = « étincelle, trace infime » — la physique des caméras gamma (scintillation) ET la promesse de révéler la plus petite trace. Le « -ia » fait écho à l'IA.
- **Promesse** : aide à la décision sous contrôle médical. Jamais « diagnostic » ; toujours « brouillon à valider ».
- **Tagline** : « Révéler la fonction. » *(alt : « De l'image au compte-rendu. »)*

---

## 2. Logo

**Symbole** : un anneau fin et froid (la coupe tomographique / l'ouverture du scanner) + un cœur lumineux décentré en dégradé chaud (le foyer de fixation / le noyau émetteur). Trois lectures : la coupe, l'ouverture (l'œil), le noyau émetteur.

**Règles**
- Zone de protection : au moins la hauteur du cœur lumineux sur tous les côtés.
- Taille minimale du symbole : 20 px (favicon), 24 px en interface.
- Variantes : couleur sur sombre (défaut), couleur sur clair (anneau en Iris `#4B4DE0`), monochrome (anneau + cœur pleins, une seule teinte).
- Le **mot-symbole** « Scintia » est en Space Grotesk 600, tracking `-0.035em`. Le symbole porte la couleur ; le mot reste blanc/encre.
- ❌ Ne jamais : déformer, ajouter d'ombre portée dure, recolorer le cœur en aplat, mettre le logo sur un fond chargé sans voile.

---

## 3. Couleur

### Le spectre Scintia (froid → chaud)
Un système unique, comme l'échelle d'intensité d'une image nucléaire. Froid = interface/structure. Chaud = signal (réservé, à fort impact).

| Token | Hex | Rôle |
|---|---|---|
| `--halo` | `#34E3E3` | Cyan — structure, interface calme, données anatomiques |
| `--iris` | `#6E6FFF` | Indigo — **action principale**, liens, le pont vers le signal |
| `--magenta` | `#EC4899` | Signal — foyers, accents forts |
| `--amber` | `#FFB13D` | Pic de fixation — valeurs maximales, points chauds |

Dégradés :
- `--grad` (spectre complet) : `linear-gradient(100deg, #34E3E3, #6E6FFF 38%, #EC4899 70%, #FFB13D)`
- `--grad-hot` (foyer/signal) : `linear-gradient(120deg, #6E6FFF, #EC4899 55%, #FFB13D)`

> **Discipline d'usage** : 90 % de l'écran est encre + froid. Le chaud (magenta/ambre, gradients) est réservé aux moments de signal : le logo, l'analyse en cours, le pic de données, l'alerte critique. C'est cette retenue qui rend l'identité premium.

### Encre (la salle de lecture) — neutres bleutés
| Token | Hex | Rôle |
|---|---|---|
| `--ink-1000` | `#07090F` | Fond le plus profond |
| `--ink-900` | `#0B0E15` | Fond de page (mode sombre par défaut) |
| `--ink-850` | `#10141D` | Fond surélevé |
| `--ink-800` | `#161B26` | Cartes / panneaux |
| `--ink-750` | `#1C2230` | Séparateurs subtils |
| `--ink-700` | `#262E3D` | Bordures |
| `--ink-400` | `#6B7689` | Texte tertiaire / labels |
| `--ink-300` | `#98A2B3` | Texte secondaire |
| `--ink-200` | `#C4CBD6` | Texte courant (sur sombre) |
| `--ink-100` | `#E7EAF0` | Titres / texte fort |
| `--paper` | `#F5F7FB` | Fond mode clair (rapports, PDF) |
| `--white` | `#FFFFFF` | — |

### Sémantique
| Token | Hex | Sens |
|---|---|---|
| `--ok` | `#1FBF8F` | Normal / fixation physiologique |
| `--info` | `#34E3E3` | Information |
| `--warn` | `#FFB13D` | À vérifier |
| `--crit` | `#FF4D6D` | Critique / foyer marquant |

**Mode sombre = défaut** (salle de lecture, images qui ressortent, fatigue oculaire). **Mode clair** pour les comptes-rendus et exports PDF. Sur clair, l'action principale passe en Iris `#4B4DE0` pour le contraste.

---

## 4. Typographie

| Rôle | Police | Usage |
|---|---|---|
| **Display** | **Space Grotesk** (500/600/700) | Logo, titres, grands chiffres. Tracking serré `-0.02em` à `-0.035em`. |
| **Texte / UI** | **IBM Plex Sans** (400/500/600) | Corps, libellés, boutons, formulaires. |
| **Données** | **IBM Plex Mono** (400/500) | **Toute valeur chiffrée** : volumes, MBq, Gy, %, scores, dates. Chiffres tabulaires. |

Toutes open-source (cohérent avec le projet open-source).

**Échelle type (rem, base 16px)**
| Niveau | Taille | Police / poids |
|---|---|---|
| Display XL | 3.0–4.0 | Space Grotesk 600 |
| H1 | 1.875 | Space Grotesk 600 |
| H2 | 1.5 | Space Grotesk 600 |
| H3 | 1.25 | Space Grotesk 500 |
| Corps | 1.0 (16px) | Plex Sans 400 |
| Petit | 0.875 | Plex Sans 400/500 |
| Label/mono | 0.75–0.8125 | Plex Mono 500, lettrage `+0.04em` à `+0.1em`, majuscules pour les eyebrows |

**Règle d'or** : une mesure clinique ne s'écrit jamais en police de texte. `1 450 mL`, `12,4 Gy`, `4 / 4` → toujours en Plex Mono. Décimale française (virgule).

---

## 5. Mise en page, espacement, élévation

- **Grille d'espacement** : base 4 px (4, 8, 12, 16, 24, 32, 48, 64).
- **Rayons** : `sm 10px`, `md 14px`, `lg 16–20px`, pilule `999px`. Cohérent, jamais à angle vif total ni trop arrondi.
- **Bordures** : 1 px `--ink-700` ; séparateurs internes `--ink-750`.
- **Élévation** : pas d'ombres dures. Profondeur par la teinte (surface plus claire = plus haute) + ombres très douces et larges (`0 40px 90px -50px rgba(0,0,0,.9)`).
- **Densité** : interface dense mais lisible (les médecins traitent beaucoup d'examens). Aération maîtrisée, jamais étouffée.
- **Eyebrows numérotées** (`01 · …`) : autorisées **uniquement** quand le contenu est une vraie séquence/étape. Sinon, label simple.

---

## 6. Composants — principes

- **Boutons** : primaire = Iris plein, texte encre foncée ; secondaire = contour `--ink-700` ; le **gradient chaud** est réservé aux actions « signal » rares (ex. lancer l'analyse). Libellés à l'impératif et constants (« Lancer l'analyse » → toast « Analyse lancée »).
- **Badges / puces** : statut sémantique. La puce « **Brouillon IA — à valider** » (contour ambre) est **présente et non supprimable** sur tout compte-rendu.
- **Cartes** : `--ink-800`, bordure `--ink-700`, rayon `lg`.
- **Barres d'intensité** : remplissage en `--grad-hot`, la largeur = niveau de fixation (donnée, pas décor).
- **Tableaux d'organes** : nom en Plex Sans, valeurs en Plex Mono alignées à droite.
- **Champs** : fond `--ink-850`, focus visible en Iris (anneau 2 px).

---

## 7. Data-visualisation

Calquée sur l'imagerie nucléaire :
- **Échelle d'intensité** = le spectre Scintia (froid → chaud). Le froid = faible/structure, le chaud = élevé/signal.
- **Anatomie / référence** en encre et froid ; **fonction / lésions** en chaud.
- **Accessibilité daltonien** : ne jamais coder une information *uniquement* par la teinte — toujours doubler par la valeur chiffrée, l'étiquette ou la position.
- Courbes (activité-temps, décroissance) : trait fin, points marqués, grille discrète `--ink-750`.

---

## 8. Iconographie & motifs

- Style : trait fin géométrique, cohérent avec l'anneau du logo.
- Motifs de marque : anneaux concentriques (coupes), courbe de décroissance, point de scintillation, l'ouverture. À utiliser avec parcimonie, jamais en fond chargé.

---

## 9. Mouvement

- **Sobre.** Trop d'animation = effet « généré ». 
- Signature autorisée : une **respiration douce** du cœur lumineux (logo) et un **balayage du spectre** pendant l'analyse en cours (le scan « s'allume »).
- Micro-interactions : transitions 150–220 ms, courbe douce. 
- **Respecter `prefers-reduced-motion`** : couper les animations d'ambiance.

---

## 10. Ton & écriture (FR)

- **Clinique, précis, sobre, confiant.** Pas de jargon inutile, pas de familiarité déplacée.
- Toujours « **aide à la décision** », jamais « diagnostic ». Le logiciel **propose**, le médecin **décide**.
- Voix active, libellés constants d'un bout à l'autre d'un flux.
- Erreurs : dire ce qui s'est passé et comment corriger, sans s'excuser ni rester vague.
- Écrans vides : une invitation à agir, pas un décor.
- i18n : FR par défaut, structure prête pour **arabe** (RTL à prévoir) et **anglais**.

---

## 11. Accessibilité (plancher non négociable)

- Contraste AA minimum sur tout texte (vérifier les valeurs claires sur encre).
- Focus clavier visible partout (anneau Iris).
- Cibles tactiles ≥ 44 px.
- Pas d'information portée uniquement par la couleur.
- `prefers-reduced-motion` respecté.

---

## 12. À faire / à éviter

**À faire** — encre + froid pour 90 % de l'écran ; chaud réservé au signal ; valeurs en mono ; badge « brouillon IA » toujours visible ; densité lisible.

**À éviter** — bleu médical générique et cartes arrondies passe-partout ; gradient chaud partout (il perd son sens) ; mesures en police de texte ; ombres dures ; animation d'ambiance non coupable ; information codée par la seule couleur.
