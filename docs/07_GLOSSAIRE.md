# 07 — Glossaire de médecine nucléaire

> Vocabulaire pour comprendre le domaine et le code. Destiné autant au développeur qu'à l'agent. Les définitions sont volontairement courtes et opérationnelles.

---

## Imagerie & acquisition

- **DICOM** — *Digital Imaging and Communications in Medicine.* Format et protocole standard de l'imagerie médicale. Chaque fichier contient l'image **et** des métadonnées (tags) : patient, examen, machine, isotope, activité, heures, paramètres de reconstruction. ⚠️ Les tags contiennent des identifiants patient → à anonymiser.
- **SPECT** — *Single Photon Emission Computed Tomography.* Imagerie fonctionnelle 3D basée sur un traceur émetteur de photons gamma. Montre **où le traceur se fixe**.
- **CT** — *Computed Tomography* (scanner). Imagerie anatomique en rayons X. Dans un SPECT/CT, sert à **localiser** les fixations et à **corriger** le SPECT (atténuation).
- **SPECT/CT** — examen hybride combinant les deux sur la même machine, recalés.
- **Planaire** — image 2D « à plat » (vue de face/dos), par opposition au SPECT 3D. La scintigraphie osseuse classique est souvent planaire corps entier.
- **Gated (synchronisé ECG)** — acquisition synchronisée au battement cardiaque ; permet de calculer la fonction du cœur (FEVG) en SPECT myocardique.
- **MIP** — *Maximum Intensity Projection.* Vue de synthèse qui projette les pixels les plus intenses ; utile pour visualiser rapidement les fixations.
- **Reconstruction** — calcul qui transforme les données brutes de la caméra en images 3D exploitables.
- **Correction d'atténuation / de diffusion (scatter) / de volume partiel** — corrections d'image nécessaires à une **quantification** fiable (sinon les valeurs sont faussées).
- **Recalage (registration)** — alignement spatial de deux images (ici CT et SPECT) pour qu'un même point corresponde au même endroit. Rigide (translation/rotation) ou élastique (déformable).

---

## Radiopharmaceutiques & isotopes

Un **radiopharmaceutique** = un vecteur (qui cible un tissu) + un isotope radioactif (qui émet le signal).

**Isotopes**
- **Tc-99m** (technétium-99m) — l'isotope « cheval de bataille », demi-vie ~6 h, photon 140 keV. Utilisé pour la majorité des scintigraphies.
- **I-123 / I-131** (iode) — I-123 (~13 h) pour l'imagerie ; I-131 (~8 jours) émet aussi des bêta → utilisé en **thérapie** + imagerie.
- **In-111** (indium-111) — demi-vie ~2,8 jours ; utilisé pour l'OctreoScan (octréotide).
- **Lu-177** (lutétium-177) — demi-vie ~6,6 jours, émetteur bêta + gamma ; utilisé en **thérapie** ciblée (DOTATATE, PSMA) et imageable pour la dosimétrie.

**Vecteurs / traceurs**
- **HMDP / HDP / MDP** — diphosphonates marqués au Tc-99m ; se fixent sur l'os → **scintigraphie osseuse**.
- **Sestamibi (MIBI) / Tétrofosmine** — traceurs Tc-99m de **perfusion myocardique** ; le sestamibi sert aussi à localiser les **adénomes parathyroïdiens**.
- **MIBG** — *méta-iodobenzylguanidine* (marquée I-123 ou I-131) ; analogue de la noradrénaline → tumeurs **neuroendocrines sympathiques** (neuroblastome, phéochromocytome, paragangliome).
- **Octréotide** — analogue de la somatostatine (marqué In-111) ; cible les **récepteurs de la somatostatine** des tumeurs neuroendocrines (TNE).
- **DOTATATE** — peptide analogue de la somatostatine, utilisé en TEP (Ga-68) ou en **thérapie** (Lu-177) des TNE.
- **MAA** — *macroagrégats d'albumine* (Tc-99m) ; bloqués dans les capillaires pulmonaires → cartographie de la **perfusion** pulmonaire.
- **Technegas** — aérosol de nanoparticules de carbone (Tc-99m) inhalé → cartographie de la **ventilation** pulmonaire.

---

## Examens & abréviations

- **Scintigraphie osseuse** — recherche de lésions osseuses (métastases, fractures, infections) via fixation des diphosphonates.
- **SPECT myocardique / Perfusion myocardique (MPI)** — évalue la perfusion du muscle cardiaque au repos et à l'effort ; détecte ischémie et nécrose.
- **MIBG** (examen) — bilan d'extension des tumeurs neuroendocrines sympathiques.
- **Octréotide / SSTR** — bilan des TNE exprimant les récepteurs de la somatostatine. *SSTR = Somatostatin Receptor.*
- **Parathyroïde (scintigraphie)** — localise un **adénome parathyroïdien** (cause d'hyperparathyroïdie), y compris ectopique.
- **V/P (ou V/Q)** — *Ventilation/Perfusion.* Compare ventilation et perfusion pulmonaires pour rechercher une **embolie pulmonaire**.

---

## Scores & critères cliniques

- **Score de Krenning** — échelle 0–4 de l'intensité de fixation de l'octréotide d'une lésion par rapport au foie/rate. Plus c'est élevé, plus la lésion exprime les récepteurs (et plus elle est éligible à une thérapie Lu-177).
- **Score de Curie / SIOPEN** — scores semi-quantitatifs de l'atteinte tumorale à la MIBG (neuroblastome) : le corps est divisé en segments, chacun coté selon la fixation.
- **PIOPED** — critères de **probabilité d'embolie pulmonaire** au V/P : normale / faible / intermédiaire / haute probabilité.
- **BSI** — *Bone Scan Index.* Pourcentage de la masse squelettique atteinte par la tumeur (suivi du cancer de la prostate).
- **FEVG / LVEF** — *Fraction d'Éjection du Ventricule Gauche.* % du sang éjecté à chaque battement ; marqueur clé de la fonction cardiaque.
- **Modèle 17 segments** — découpage standard du ventricule gauche en 17 segments pour coter la perfusion ; visualisé en **carte polaire** (bull's-eye).
- **SSS / SRS / SDS** — *Summed Stress / Rest / Difference Score.* Sommes des cotations (0–4) des 17 segments à l'effort, au repos, et leur différence. Le **SDS** reflète l'**ischémie** (réversible) ; un déficit fixe reflète une **nécrose**.
- **TID** — *Transient Ischemic Dilation.* Dilatation transitoire du ventricule à l'effort ; signe d'ischémie sévère.

---

## Quantification & dosimétrie

- **Facteur de calibration (sensibilité)** — relation coups détectés ↔ activité réelle (en coups/s par MBq), obtenue sur **fantôme**. Indispensable pour convertir les images en activité (MBq).
- **%AI** — *pourcentage de l'activité injectée* présente dans un organe. Mesure standardisée de fixation.
- **Activité injectée nette** — activité réellement administrée = seringue pleine − résidu, corrigée de la décroissance jusqu'à l'heure d'acquisition.
- **Dose absorbée** — énergie de rayonnement déposée par unité de masse, en **Gray (Gy)**. C'est ce qu'on cherche à estimer en dosimétrie thérapeutique.
- **MIRD** — *Medical Internal Radiation Dose.* Formalisme de référence pour calculer les doses internes.
- **Courbe activité-temps (TAC)** — évolution de l'activité dans un organe au cours du temps, reconstruite à partir de **plusieurs acquisitions** à des heures différentes.
- **TIA / TIAC** — *Time-Integrated Activity (Coefficient).* Intégrale de la courbe activité-temps = activité cumulée (anciennement « temps de résidence »). Brique centrale du calcul de dose.
- **Valeur S (S-value)** — dose reçue par un organe cible par unité d'activité cumulée dans un organe source. Dépend d'un modèle anatomique (fantôme).
- **Demi-vie effective** — combinaison de la demi-vie physique (décroissance radioactive) et biologique (élimination par le corps).
- **OLINDA/EXM** — logiciel de référence de dosimétrie au niveau organe (modèles fantômes).
- **MIRDcalc** — outil **gratuit** de dosimétrie organe (MIRD Pamphlet 28), basé sur tableur.
- **Voxel S-value / dosimétrie voxel** — dosimétrie fine au niveau de chaque voxel de l'image (plus précise que le niveau organe).
- **Organes à risque** — organes sensibles dont on surveille la dose pour ne pas dépasser un seuil (reins, moelle osseuse, glandes salivaires selon le traitement).
- **EANM / MIRD Pamphlet 26** — recommandations pour la quantification SPECT du Lu-177 et la dosimétrie associée.
- **Méthode « single-time-point » (STP)** — dosimétrie à partir d'une **seule** acquisition (au lieu de plusieurs) ; pratique mais **approximative**, à étiqueter comme telle.

---

## Segmentation & anatomie

- **TotalSegmentator** — modèle d'IA open-source qui segmente automatiquement **117 structures anatomiques** sur un CT. On l'utilise pour délimiter les organes et calculer leurs volumes. *(Non destiné à un usage clinique en l'état → relecture humaine obligatoire.)*
- **Segmentation** — délimitation automatique ou manuelle d'un organe/d'une lésion sur l'image.
- **Masque** — image binaire indiquant les voxels appartenant à une structure (1 = dans l'organe, 0 = dehors).
- **ROI** — *Region Of Interest.* Zone d'intérêt sur laquelle on fait des mesures.
- **NIfTI** — format d'image courant en imagerie de recherche/IA ; on convertit souvent le DICOM en NIfTI pour les modèles.

---

## Termes métier fréquents

- **Fixation / captation (uptake)** — quantité de traceur capté par un tissu. « Hyperfixation » = fixation anormalement élevée.
- **Foyer** — zone localisée de fixation anormale.
- **Fixation physiologique** — fixation **normale** du traceur dans certains organes (ex. reins et vessie en scintigraphie osseuse). À ne pas confondre avec une lésion.
- **Mismatch (V/P)** — discordance ventilation/perfusion (zone ventilée mais non perfusée) ; évoque une embolie.
- **Washout (lavage)** — vitesse à laquelle un traceur quitte un tissu ; clé en scintigraphie parathyroïdienne (l'adénome retient plus longtemps que la thyroïde).
- **Biodistribution** — répartition du traceur dans l'ensemble du corps.
- **Extravasation** — fuite du traceur hors de la veine au point d'injection ; artefact à détecter.
- **Pertechnétate libre** — Tc-99m non lié au vecteur ; se fixe sur thyroïde/estomac/glandes salivaires → artefact.
- **PRRT** — *Peptide Receptor Radionuclide Therapy.* Thérapie par radioligand (ex. Lu-177 DOTATATE) des TNE ; nécessite une dosimétrie.
