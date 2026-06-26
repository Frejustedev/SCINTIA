# 01 — Spécifications fonctionnelles (Scintia)

> Le « quoi » : périmètre et fonctionnalités. Architecture détaillée → `02_ARCHITECTURE.md`. Feuille de route → `06_ROADMAP.md`. Vocabulaire → `07_GLOSSAIRE.md`.

---

## 1. Vision & positionnement

**Problème.** L'analyse d'un SPECT/CT (segmentation, quantification, dosimétrie, rédaction du compte-rendu) est chronophage, dépendante de l'opérateur et peu standardisée. Les outils de dosimétrie existants sont coûteux, fragmentés et souvent liés à un constructeur.

**Utilisateurs.** Médecins nucléaires, radiophysiciens médicaux, manipulateurs, centres de médecine nucléaire (publics et privés).

**Proposition de valeur.** Un pipeline unique qui prend les DICOM bruts et produit, en quelques minutes, un tableau d'organes + volumes + dosimétrie + un brouillon de compte-rendu, **toujours relu et validé par le médecin**.

**Positionnement réglementaire (à cadrer dès le départ).**
- Un logiciel qui contribue au diagnostic ou calcule une dose absorbée relève du **dispositif médical** (vraisemblablement classe IIa/IIb sous le règlement UE 2017/745 MDR ; cadre national algérien à vérifier).
- **Phase 1 = outil de recherche / aide à la décision non clinique** : aucune décision médicale n'est prise par le logiciel, le médecin valide et signe tout.
- Prévoir dès maintenant : journal d'audit, traçabilité des versions de modèles, mention systématique « brouillon généré par IA — à valider ».
- *Ceci n'est pas un avis juridique : faire valider le statut réglementaire et le circuit des données par un spécialiste.*

---

## 2. Les 3 briques (vue d'ensemble)

Scintia s'articule en trois parties, détaillées dans `02_ARCHITECTURE.md` :
1. **Backend (FastAPI)** — réception et anonymisation des DICOM, séparation CT/SPECT, orchestration du pipeline (segmentation, quantification, dosimétrie), appel à Claude pour le compte-rendu.
2. **Frontend (Next.js)** — upload, suivi de progression, page résultats (organes, volumes, dosimétrie), visualiseur DICOM, éditeur de compte-rendu, export.
3. **Pipeline IA** — TotalSegmentator (segmentation du CT), moteur de dosimétrie (MIRDcalc/OLINDA), Claude (rédaction).

**Flux de données.** DICOM uploadés → anonymisation → tri CT/SPECT → segmentation du CT (masques + volumes) → recalage SPECT/CT → échantillonnage des coups SPECT dans les masques → conversion coups→activité (facteur de calibration) → dosimétrie → assemblage des données structurées → génération du CR par Claude → relecture/édition humaine → export. *(Détail complet du pipeline en `02_ARCHITECTURE.md`.)*

---

## 3. Catalogue complet des fonctionnalités

### A. Ingestion & gestion des données
- Upload par **glisser-déposer** : fichiers isolés, dossier complet, archive ZIP, ou dossier DICOMDIR.
- Support **multi-séries / multi-temps** (indispensable pour la dosimétrie sérielle).
- Lecture des en-têtes DICOM (modalité, isotope, activité injectée, heure d'injection, heure d'acquisition, constructeur, paramètres de reconstruction).
- **Anonymisation / dé-identification** automatique des tags DICOM avant tout traitement (nom, ID, dates, adresse, etc.), avec table de correspondance chiffrée côté serveur.
- Détection des doublons et des séries incomplètes.
- File d'attente de traitement (plusieurs patients en parallèle).
- Reprise sur erreur (un job qui échoue n'invalide pas les autres).
- Historique des examens par patient (pseudonymisé).
- Import depuis **PACS** (DICOM C-MOVE/C-GET) — *fonctionnalité avancée, phase ultérieure*.

### B. Pré-traitement DICOM & séparation CT/SPECT
- Tri automatique **CT vs SPECT** par modalité, géométrie et métadonnées.
- Reconstruction du volume 3D à partir des coupes.
- Identification de l'**isotope** et du radiopharmaceutique (à partir des tags, avec confirmation manuelle possible).
- **Recalage CT ↔ SPECT** (rigide par défaut ; élastique en option) — étape critique pour échantillonner correctement le SPECT dans les masques anatomiques.
- Corrections d'image : atténuation, diffusion (scatter), résolution / volume partiel (au moins signalées, idéalement appliquées).
- Contrôle qualité automatique : champ de vue tronqué, mouvement patient, extravasation au point d'injection, artéfacts métalliques.
- Conversion de format (DICOM → NIfTI) pour les modèles d'IA.

### C. Segmentation anatomique (TotalSegmentator v2 — sur le CT)
- Segmentation automatique de **117 structures** (organes, os, muscles, vaisseaux).
- **Volume de chaque organe** directement via le flag `--statistics` (sortie en mm³, à convertir en mL).
- Tâches spécialisées si besoin : chambres cardiaques haute résolution, types de tissus (graisse / muscle), structures crânio-faciales.
- Option `--roi_subset` pour ne segmenter que les organes pertinents à l'examen (gain de temps majeur sur CPU).
- **Édition manuelle des masques** : le médecin doit pouvoir corriger une segmentation ratée (rein partiellement manqué, foie débordant sur la rate, etc.). *Sans cette fonction, l'outil n'est pas utilisable cliniquement.*
- Visualisation 3D et superposition des masques sur le CT (axial / coronal / sagittal).
- Score de confiance / signalement des segmentations douteuses.
- ⚠️ TotalSegmentator est, selon ses auteurs, **non destiné à un usage clinique en l'état** — d'où l'obligation de relecture humaine et le positionnement « recherche ».

### D. Quantification fonctionnelle SPECT
- **Facteur de calibration** du système (sensibilité en coups/s par MBq) : saisie manuelle, ou calibration sur fantôme stockée par caméra.
- Conversion **coups → activité (MBq)** dans chaque volume d'intérêt.
- Échantillonnage des coups SPECT à l'intérieur des masques anatomiques issus du CT.
- Calcul de la **concentration d'activité** (MBq/mL) et de l'activité totale par organe.
- Décroissance physique prise en compte (correction par la demi-vie de l'isotope, recalage temporel à l'injection).
- Mesures semi-quantitatives standardisées par examen (voir section 4).
- Comparaison aux valeurs de référence (lésion vs bruit de fond, organe vs foie/rate selon l'examen).

**Métriques en pourcentage (à choisir selon l'examen) :**
- **% de l'activité injectée (%AI)** : activité dans l'organe ÷ activité injectée nette. S'appuie sur le facteur de calibration déjà nécessaire à la dosimétrie. Métrique la plus standardisée.
- **% de captation relative** : normalisation au segment/région de captation maximale (= 100 %) ; base des cartes polaires en perfusion myocardique.
- **Ratios standardisés** : lésion / bruit de fond, lésion / organe de référence (foie, rate selon l'examen).
- **Calcul de l'activité injectée nette** : activité seringue pleine − résiduelle, corrigée de la décroissance jusqu'à l'heure d'acquisition (brique commune au %AI et à la dosimétrie).
- *Extensions naturelles* : **fonction rénale séparée** en % (si ajout de la scintigraphie rénale DMSA/MAG3) ; **captation thyroïdienne (RAIU)** en % (si ajout du bilan thyroïdien).

### E. Dosimétrie (le module le plus délicat)
- **Saisie multi-temps** : import de plusieurs SPECT/CT acquis à des heures différentes.
- Construction de la **courbe activité-temps (TAC)** par organe et par lésion.
- **Fit mono- ou bi-exponentiel** et intégration → activité cumulée / temps de résidence (TIA).
- Calcul de la **dose absorbée (Gy)** selon le formalisme **MIRD** (valeurs S par organe).
- Intégration possible d'un moteur existant : **MIRDcalc** (gratuit, MIRD Pamphlet 28) ou **OLINDA/EXM** — plutôt que de réimplémenter les valeurs S.
- Niveaux de calcul, du plus simple au plus fin :
  1. Niveau organe (modèle anthropomorphe — type OLINDA).
  2. Niveau voxel (voxel S-values / dose point-kernel).
  3. Monte-Carlo (objectif lointain).
- **Mode single-time-point** explicitement étiqueté « estimation approximative » (méthodes de Hänscheid / Madsen) quand un seul temps est disponible.
- Doses aux **organes à risque** (reins, moelle, glandes salivaires…) et aux **lésions cibles**.
- **Incertitude** affichée sur chaque dose (la dosimétrie sans barre d'erreur est trompeuse).
- Respect des recommandations **EANM/MIRD Pamphlet 26** pour le Lu-177.

### F. Analyse par type d'examen
*(détail en section 4)* — six modules, chacun avec sa logique de détection, son score standardisé et ses sorties spécifiques.

**Atlas de biodistribution physiologique (fixations physiologiques) — composant transversal.**
Base de connaissance par traceur décrivant la captation *normale* attendue, ses intensités et ses pièges classiques. Branchée sur le moteur de détection, elle sert à :
- **filtrer** les faux positifs (ne pas signaler comme lésion une captation normale) ;
- **annoter** le compte-rendu (« captation physiologique de X ») ;
- **cadrer Claude** : on lui fournit explicitement ce qui est physiologique pour qu'il n'interprète pas une fixation normale comme pathologique.
Le **CT segmenté** est le levier clé : un foyer qui tombe sur les reins ou la vessie en scintigraphie osseuse est reconnu comme physiologique grâce à la localisation anatomique. *(Tables détaillées par traceur en section 4.)*

### G. Génération du compte-rendu (Claude API)
- Assemblage d'un **contexte structuré** (organes, volumes, scores, dosimétrie, antériorités) envoyé à Claude — **sans aucun identifiant patient**.
- Génération d'un CR au format radiologique : Indication / Technique / Résultats / Conclusion.
- **Modèles (templates) par type d'examen** et par établissement.
- Ton et longueur paramétrables (synthétique vs détaillé).
- Comparaison automatique avec l'examen antérieur (« progression », « stabilité », « réponse partielle »).
- Génération **multilingue** (français, arabe, anglais).
- Mention obligatoire et non supprimable : « Brouillon généré par IA — à valider par le médecin ».
- Garde-fous : Claude ne doit jamais inventer une mesure absente ; il reformule uniquement les données fournies.

### H. Édition & export
- **Éditeur de texte riche** : le médecin corrige et complète le CR.
- Conservation des deux versions (brouillon IA / version validée) pour audit.
- Export **PDF** mis en page (en-tête du centre, identité réintroduite localement, signature).
- Export **DICOM-SR** (structured report) et **FHIR** pour intégration au dossier patient.
- Export du tableau de données (CSV / Excel).
- Export des images annotées (masques, foyers localisés).
- Envoi vers **RIS / PACS** — *phase ultérieure*.

### I. Frontend / expérience utilisateur
- Page d'accueil : glisser-déposer + choix du type d'examen.
- **Barre de progression** détaillée par étape (anonymisation → tri → segmentation → quantification → CR).
- Page résultats : tableau organes/volumes/dosimétrie + visualiseur d'images.
- Visualiseur DICOM intégré (défilement des coupes, fenêtrage, superposition des masques, MIP).
- Vue comparative côte à côte avec l'antériorité.
- Tableau de bord : liste des examens, statuts, recherche.
- Mode sombre, interface responsive, raccourcis clavier pour les manipulateurs.
- Accessibilité (contraste, navigation clavier). *(Tout selon `03_CHARTE_GRAPHIQUE.md`.)*

### J. Sécurité, confidentialité, conformité
*(Détail complet et impératif dans `05_CONTRAINTES_SECURITE.md`.)*
- **Anonymisation avant traitement** + ré-identification uniquement locale au moment de l'export.
- Chiffrement en transit (TLS) et au repos.
- Aucune donnée identifiante envoyée à l'API externe ; activer les options de **zéro-rétention**.
- Gestion des accès (rôles : médecin, physicien, manipulateur, admin).
- Conformité **RGPD** / **loi 18-07** (Algérie) : registre des traitements, durée de conservation, droit à l'effacement.
- Hébergement de données de santé conforme (selon juridiction).
- Politique de suppression automatique des fichiers bruts après traitement.

### K. Traçabilité, qualité, validation
- **Journal d'audit** complet (qui a fait quoi, quand, sur quel examen).
- Versionnage des **modèles d'IA** et des paramètres de calcul (reproductibilité).
- Horodatage de chaque étape.
- Indicateurs de qualité par examen (segmentation corrigée ? dosimétrie mono- ou multi-temps ?).
- Jeu de données de **validation** pour comparer les sorties IA aux mesures de référence (essentiel pour la crédibilité scientifique et un futur dossier réglementaire).
- Retour utilisateur intégré (signaler une erreur de segmentation / de CR).

### L. Administration & déploiement
- Gestion des utilisateurs et des centres.
- Configuration des facteurs de calibration par caméra.
- Gestion des templates de CR.
- Tableau de bord d'usage et de coûts API.
- Déploiement conteneurisé (Docker) ; GPU recommandé pour TotalSegmentator.
- Mode **on-premise** (sur serveur du centre) pour les centres qui ne veulent pas que les images sortent de leurs murs.

### M. Fonctionnalités différenciantes (bonus)
- **Suivi longitudinal** automatique des lésions (appariement d'une lésion d'un examen à l'autre, courbes d'évolution).
- Bibliothèque de cas anonymisés pour l'enseignement.
- Aide à la **planification de traitement** (estimer l'activité à administrer pour ne pas dépasser la dose aux organes à risque).
- Statistiques de service (volumes d'activité, délais, types d'examens).
- API ouverte pour s'intégrer à d'autres logiciels.
- Intégration **TEP** (Ga-68 DOTATATE, qui remplace de plus en plus l'Octréotide SPECT) — extension naturelle.
- **Comparaison à une base de normaux** (surtout perfusion myocardique) : le % de déficit se calcule par rapport à une population normale — standard du domaine.
- **Détection d'artéfacts et de pièges** : extravasation au point d'injection, pertechnétate libre, mouvement patient, atténuation.
- **Score de réponse thérapeutique** : comparaison structurée à l'antériorité (réponse / stabilité / progression), utile en oncologie et suivi de PRRT.
- **Contextualisation biologique** : intégrer les labos pertinents — PSA (os prostatique), chromogranine A (TNE), calcémie/PTH (parathyroïde).
- **Alerte valeurs critiques** : dose rénale approchant le seuil, EP haute probabilité au V/P, etc.
- **Cartographie corporelle annotée** : schéma du corps avec lésions marquées, inséré dans le CR.
- **Quantification absolue type SUV en SPECT** (SPECT quantitatif / xSPECT) : prévoir l'architecture pour l'accueillir.
- **Demi-vie effective observée** chez le patient (temps multiples) vs valeur théorique — affine la dosimétrie.
- **Codification standardisée** : relier les trouvailles à SNOMED-CT (TotalSegmentator mappe déjà ses 117 classes vers SNOMED-CT).

---

## 4. Détail par examen

| Examen | Radiopharmaceutique | Ce que fait le module | Sortie standardisée |
|---|---|---|---|
| **Scintigraphie osseuse** | Tc-99m HMDP/HDP | Détecte et localise les foyers hyperfixants ; rattache chaque foyer à l'os concerné (vertèbre, côte, bassin) via le CT ; distingue profils bénin/malin ; repère le « super scan » | Cartographie des foyers + **Bone Scan Index (BSI)** pour le cancer prostatique |
| **SPECT myocardique** | Tc-99m sestamibi/tétrofosmine (ou Tl-201) | Calcule la **FEVG** (SPECT gated), analyse la perfusion par territoire (IVA / Cx / CD), distingue **ischémie réversible vs nécrose fixée**, détecte la dilatation ischémique transitoire (TID) | Modèle 17 segments, cartes polaires, scores **SSS / SRS / SDS** |
| **MIBG** | I-123 ou I-131 MIBG | Détecte et score l'atteinte tumorale par segment corporel (neuroblastome, phéochromocytome, paragangliome) ; dosimétrie pour la thérapie I-131 | **Score de Curie** (ou SIOPEN) + dosimétrie I-131 |
| **Octréotide / SSTR** | In-111 octréotide | Évalue l'expression des récepteurs de la somatostatine des lésions par rapport au foie/rate ; dosimétrie pour la thérapie Lu-177 | **Score de Krenning (0–4)** + dosimétrie Lu-177 |
| **Parathyroïde** | Tc-99m sestamibi (double phase + SPECT/CT) | Localise l'**adénome** (y compris ectopique / médiastinal) ; soustraction double-isotope possible | Localisation anatomique précise de l'adénome |
| **Poumon V/P** | Tc-99m MAA (perfusion) + Technegas/DTPA (ventilation) | Détecte les **mismatch** ventilation/perfusion ; applique les critères de probabilité d'embolie | Probabilité **PIOPED** (normal / faible / intermédiaire / haute) |

> Pour chaque module : détection automatique → mesure semi-quantitative → comparaison à l'antériorité → alimentation du CR. La **localisation anatomique via le CT segmenté** est le fil conducteur commun (ex. « foyer hyperfixant de la 8e côte droite » plutôt que « foyer thoracique »).

### Atlas de biodistribution physiologique (par traceur)

| Traceur | Fixation physiologique normale | Pièges classiques (faux positifs) |
|---|---|---|
| **Os** (Tc-99m HMDP/HDP) | Squelette entier (axial > appendiculaire), cartilages de croissance chez l'enfant, reins + vessie (élimination urinaire), point d'injection | Arthrose / dégénératif (sacro-iliaques, rachis) mimant des métastases ; jonctions chondro-costales ; contamination urinaire |
| **Perfusion myocardique** (sestamibi/tétrofosmine) | Myocarde ; foie, vésicule, anses digestives (élimination hépatobiliaire) | Atténuation mammaire (paroi antérieure) ; atténuation diaphragmatique (paroi inférieure) ; activité digestive sous-diaphragmatique parasitant la paroi inférieure |
| **MIBG** (I-123/I-131) | Myocarde (captation cardiaque normale), glandes salivaires, foie, rate, intestin, vessie, graisse brune ; blocage thyroïdien obligatoire | Captation myocardique/hépatique normales ; graisse brune ; thyroïde si blocage insuffisant |
| **Octréotide / SSTR** (In-111) | Rate (la plus intense), reins, foie, hypophyse, thyroïde, intestin, vessie | Rate accessoire mimant une lésion ; captation splénique/rénale normales ; processus unciné du pancréas |
| **Parathyroïde** (sestamibi double phase) | Thyroïde (lavage plus rapide que l'adénome), glandes salivaires, myocarde, foie | Nodule thyroïdien rétenteur de sestamibi = faux positif d'adénome parathyroïdien |
| **Poumon V/P** (MAA / Technegas) | Perfusion + ventilation homogènes, léger gradient gravitationnel (bases > sommets) | Pertechnétate libre (thyroïde/estomac/salivaire) ; amas de MAA = points chauds focaux ; gradient gravitationnel pris pour une anomalie |

---

## 5. Stack & feuille de route

- **Stack technique** → `02_ARCHITECTURE.md` (section stack & déploiement).
- **Modèle de données** → `04_MODELE_DONNEES.md`.
- **Feuille de route et phases** → `06_ROADMAP.md`.

---

## Références (à jour, juin 2026)
- TotalSegmentator v2 (117 structures, flag `--statistics`) — github.com/wasserth/TotalSegmentator
- EANM/MIRD Pamphlet 26 — guidelines quantification SPECT Lu-177
- MIRD Pamphlet 28 / MIRDcalc — outil de dosimétrie organe gratuit (SNMMI)
- OLINDA/EXM 2.x — dosimétrie organe de référence
- Études single-time-point vs multi-time-point dosimetry (Lu-177 PSMA / DOTATATE)
