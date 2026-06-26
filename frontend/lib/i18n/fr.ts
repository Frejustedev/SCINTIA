/** French strings (default locale). Arabic (RTL) and English added later. */
export const fr = {
  appName: "Scintia",
  tagline: { before: "Révéler la ", accent: "fonction", after: "." },
  sub:
    "Analyse des examens SPECT/CT — segmentation, quantification, dosimétrie et " +
    "premier jet du compte-rendu. Toujours sous le contrôle du médecin.",
  home: {
    eyebrow: "Nouvel examen",
    chooseExam: "Choisir le type d'examen",
    uploadTitle: "Déposer les fichiers DICOM",
    uploadHint: "Glissez un dossier, un .zip ou un DICOMDIR ici",
    uploadInactive: "Interface de démonstration — le chargement n'est pas actif en Phase 0.",
    browse: "Parcourir",
    researchBadge: "Prototype de recherche",
    disclaimer:
      "Aide à la décision sous contrôle médical. Le logiciel propose ; le médecin " +
      "relit, valide et signe.",
  },
} as const;
