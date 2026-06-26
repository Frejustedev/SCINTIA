# 05 — Contraintes de sécurité, confidentialité & conformité

> Ces règles **priment sur tout**. Elles protègent les patients et le projet. Tout code qui manipule des données patient doit s'y conformer. *Ce document n'est pas un avis juridique : faire valider le dispositif réglementaire et le circuit des données par un spécialiste.*

---

## 1. Principes directeurs

1. **Confidentialité dès la conception** (privacy by design).
2. **Anonymisation en amont de tout traitement.**
3. **Minimisation des données** : on ne collecte / ne transmet que le strict nécessaire.
4. **Moindre privilège** : chacun n'accède qu'à ce dont il a besoin.
5. **Humain dans la boucle** : aucune décision médicale automatisée.
6. **Auditabilité** : tout est tracé, rien d'effaçable silencieusement.

---

## 2. Dé-identification DICOM (étape critique)

Les fichiers DICOM contiennent de nombreux identifiants. La dé-identification suit l'esprit du **profil de confidentialité DICOM (PS3.15)**.

**Tags à supprimer ou pseudonymiser** (liste non exhaustive) :
- `PatientName (0010,0010)`, `PatientID (0010,0020)`, `PatientBirthDate (0010,0030)`
- `PatientAddress`, `OtherPatientIDs`, `PatientTelephoneNumbers`
- `ReferringPhysicianName`, `InstitutionName`, `InstitutionAddress`, `OperatorsName`
- `AccessionNumber`, `StudyID` (remplacés par des identifiants internes)
- **Tags privés** : supprimés par défaut (sauf liste blanche connue et sûre).

**Cas particuliers à gérer :**
- **Dates** : ne pas simplement supprimer — **décaler toutes les dates d'un même patient d'un offset cohérent** (préserve les écarts temporels, indispensables à la dosimétrie multi-temps).
- **UID** (`StudyInstanceUID`, `SeriesInstanceUID`…) : régénérer, mais **conserver la correspondance** pour que le CT et le SPECT d'un même examen restent liés.
- **PHI « brûlée » dans les pixels** (texte incrusté sur certaines captures secondaires) : détecter et nettoyer (option *Clean Pixel Data*). Rare en SPECT/CT brut, possible sur les captures écran.

**Table de ré-identification** : la correspondance pseudonyme ↔ identité réelle est **chiffrée**, stockée à part (`patient_identities`), accès strictement restreint. La **ré-identification n'a lieu que localement, au moment de l'export** (en-tête du PDF, dossier patient) — jamais côté traitement, jamais vers l'extérieur.

---

## 3. Données & API externes (Claude)

- **Aucun identifiant direct** (nom, date de naissance, ID, adresse) n'est envoyé à une API externe — **jamais**.
- Ce qui est envoyé à Claude pour le compte-rendu : **uniquement des données cliniques structurées et anonymisées** (organes, volumes, scores, dosimétrie, antériorités pseudonymisées).
- Activer l'option **zéro-rétention** côté API.
- Minimiser : ne transmettre que les champs nécessaires à la rédaction.
- Garde-fou produit : Claude **reformule** les données fournies ; il n'invente aucune mesure (cf. prompt de génération).

---

## 4. Chiffrement

- **En transit** : TLS partout (frontend ↔ API ↔ services).
- **Au repos** : base de données et stockage objet chiffrés. Table de ré-identification chiffrée au niveau applicatif (clé gérée hors base).
- **Gestion des clés** : hors dépôt, via variables d'environnement / coffre de secrets. Rotation possible.

---

## 5. Contrôle d'accès

- **Authentification** robuste (mots de passe hachés — argon2/bcrypt ; **MFA recommandée**).
- **RBAC** par rôle : `medecin`, `physicien`, `manipulateur`, `admin`. Exemple : seul le médecin valide un CR ; seul l'admin gère les utilisateurs ; le physicien accède aux modules de dosimétrie.
- Sessions à durée limitée, déconnexion, révocation.
- L'accès à `patient_identities` est une permission distincte et restreinte.

---

## 6. Journal d'audit

- **Append-only**, non modifiable.
- Journalise au minimum : connexion/déconnexion, upload, correction de segmentation, édition et **validation** de CR, **export**, accès à l'identité réelle, suppression.
- Chaque entrée : utilisateur, action, examen concerné, horodatage, (IP).
- Conservé selon la politique de rétention.

---

## 7. Rétention & suppression

- **DICOM bruts supprimés après traitement** (minimisation). On conserve les dérivés nécessaires (mesures, masques, CR), pas les images sources identifiantes plus que de besoin.
- Politique de durée de conservation explicite, configurable.
- **Droit à l'effacement** (RGPD / loi 18-07) : procédure pour supprimer les données d'un patient, y compris l'identité chiffrée et les dérivés, avec trace de la suppression dans l'audit.

---

## 8. Conformité réglementaire

- **RGPD** (si données de ressortissants UE) et **loi algérienne 18-07** sur la protection des données personnelles : base légale, information des personnes, registre des traitements, durées de conservation, sécurité.
- **Hébergement de données de santé** conforme à la juridiction (équivalent HDS) ; option **on-premise** pour les centres qui l'exigent.
- **Statut dispositif médical** : rappel permanent — phase de départ = **prototype de recherche / aide à la décision**, non clinique. La traçabilité et la validation mises en place dès maintenant servent une éventuelle certification (MDR ou cadre national) ultérieure.
- *Validation par un spécialiste réglementaire requise avant tout usage clinique.*

---

## 9. Gouvernance des modèles (traçabilité scientifique)

- **Versionner** les modèles d'IA (TotalSegmentator, version du prompt de CR) et les **paramètres de calcul** (valeurs S, facteurs de calibration).
- Chaque résultat porte la **version du modèle / des paramètres** qui l'a produit (`model_version`, `ai_model_version`) → reproductibilité.
- Constituer un **jeu de validation** (cas de référence) pour comparer les sorties IA aux mesures manuelles — base de la crédibilité et d'une future certification.

---

## 10. Secrets & dépôt

- **Aucun secret en dur.** Tout par variables d'environnement ; `.env` ignoré, `.env.example` versionné.
- **`.gitignore`** exclut : `.env`, données patient (DICOM), poids de modèles, dossiers de sortie, identifiants.
- Pas de données patient ni de secrets dans les logs applicatifs.

---

## 11. Lignes rouges (rappel)

- ❌ Envoyer un identifiant patient vers une API externe.
- ❌ Commiter DICOM, secrets ou poids de modèles.
- ❌ Stocker l'identité réelle en clair ou la mêler aux données cliniques.
- ❌ Présenter une sortie comme un diagnostic.
- ❌ Supprimer la mention « brouillon IA — à valider ».
- ❌ Contourner le journal d'audit sur une action sensible.
- ❌ Produire une dose sans incertitude, ou une dose single-time-point non étiquetée comme approximative.
