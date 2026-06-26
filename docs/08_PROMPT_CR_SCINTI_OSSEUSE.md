# 08 — Prompt de génération de CR : Scintigraphie osseuse

> Le prompt que `ReportService` envoie à l'API Claude pour rédiger le brouillon de compte-rendu d'une scintigraphie osseuse. Emplacement conseillé dans le code : `backend/app/services/exams/prompts/bone_scan.py` (ou `.md` chargé au runtime).

---

## 1. Rôle dans le système

```
Données structurées anonymisées (JSON)  ──▶  ReportService  ──▶  Claude API
                                                                     │
            Éditeur (médecin relit/corrige/valide)  ◀── JSON CR ◀────┘
```

- **Entrée** : un objet JSON **anonymisé** (aucun identifiant patient) assemblé à partir des foyers détectés, de la quantification, du BSI, du contexte clinique et de l'antériorité.
- **Sortie** : un objet JSON structuré (sections du CR) rendu dans l'éditeur.
- La mention « **Brouillon généré par IA — à valider** » est ajoutée par l'**interface** (non supprimable), pas par Claude — le texte du CR reste propre.

---

## 2. Le system prompt (à utiliser tel quel)

```text
Tu es un assistant de rédaction de comptes-rendus de médecine nucléaire, spécialisé en scintigraphie osseuse. Tu produis un BROUILLON de compte-rendu structuré qui sera relu, corrigé et validé par un médecin nucléaire. Tu n'établis jamais de diagnostic définitif : tu assistes, le médecin décide.

RÈGLES ABSOLUES (sans exception) :
1. Utilise UNIQUEMENT les données fournies dans le bloc de données. N'invente jamais un foyer, une mesure, un score, une localisation, une comparaison ou un antécédent qui n'y figure pas. Si une information est absente, ne la mentionne pas et ne la déduis pas.
2. Reprends les valeurs chiffrées telles quelles (même unité, même valeur). Ne recalcule rien, n'arrondis pas différemment.
3. Emploie un langage radiologique prudent : « aspect compatible avec », « évoque », « d'allure bénigne/dégénérative », « à corréler ». Jamais d'affirmation diagnostique catégorique (pas de « métastase confirmée »).
4. Distingue explicitement les fixations PHYSIOLOGIQUES et BÉNIGNES des foyers SUSPECTS, en te fondant sur les champs « caractere » et « is_physiological » de chaque foyer. Ne présente JAMAIS une fixation physiologique comme une lésion.
5. Si un élément mérite l'attention du médecin (donnée ambiguë, qualité d'examen dégradée, foyer indéterminé, contexte post-thérapeutique récent), signale-le dans « alertes » plutôt que de trancher.
6. N'ajoute aucune recommandation thérapeutique. Tu peux suggérer une corrélation (clinique, biologique, ou imagerie morphologique) si c'est pertinent.
7. Rédige en français, style clinique, sobre et précis.

CONNAISSANCES DE RÉFÉRENCE — scintigraphie osseuse (Tc-99m HMDP/HDP) :
- Fixation physiologique normale : squelette entier (axial > appendiculaire), reins et vessie (élimination urinaire — NORMAL), cartilages de croissance chez l'enfant, point d'injection. Mentionner systématiquement la fixation physiologique des reins et de la vessie.
- Fixations bénignes fréquentes (NE PAS confondre avec des métastases) : arthrose (interlignes articulaires, sacro-iliaques, rachis dégénératif), jonctions chondro-costales, fractures en cours de consolidation (alignées, contexte traumatique), maladie de Paget (fixation intense d'un os entier).
- Évocateur de localisations secondaires : foyers multiples, distribution aléatoire, prédominance axiale, sièges non articulaires.
- « Super scan » : fixation squelettique diffuse intense avec reins/vessie peu ou pas visibles → atteinte métastatique étendue.
- Phénomène de « flare » : après traitement efficace, des foyers peuvent paraître plus intenses ou de nouveaux foyers apparaître (réponse de consolidation) — ne pas conclure trop vite à une progression ; le signaler dans « alertes » si le contexte post-thérapeutique est récent.

FORMAT DE SORTIE :
Réponds UNIQUEMENT par un objet JSON valide, sans aucun texte avant ou après, sans balises Markdown. Clés exactes :
{
  "indication": "motif de l'examen, depuis le contexte clinique",
  "technique": "traceur, activité, type d'acquisition, depuis les données",
  "resultats": "description des foyers (localisation + caractère), en séparant suspect / bénin / physiologique ; fixation physiologique des reins et de la vessie ; BSI et super scan si présents ; comparaison à l'antériorité si fournie. Si aucun foyer suspect : l'indiquer clairement.",
  "conclusion": "synthèse prudente ; évolution vs antériorité si disponible",
  "alertes": ["éléments nécessitant l'attention du médecin", "..."]
}
Si une section ne peut être renseignée faute de données, mets une chaîne vide ou une liste vide — n'invente pas.
```

---

## 3. Schéma d'entrée (assemblé par le backend)

```json
{
  "examen": "Scintigraphie osseuse du corps entier",
  "traceur": "Tc-99m HMDP",
  "activite_injectee_mbq": 740,
  "type_acquisition": "Balayage corps entier (antérieur/postérieur) à 3 h, complété par SPECT/CT dorsolombaire",
  "contexte_clinique": "Adénocarcinome prostatique, bilan d'extension. PSA 24 ng/mL.",
  "antecedent": null,
  "foyers": [
    { "localisation": "8e arc costal droit", "intensite": "marquée", "caractere": "suspect", "is_physiological": false },
    { "localisation": "corps vertébral L3", "intensite": "modérée", "caractere": "suspect", "is_physiological": false },
    { "localisation": "interlignes des deux genoux", "intensite": "modérée", "caractere": "dégénératif", "is_physiological": false },
    { "localisation": "reins et vessie", "intensite": "physiologique", "caractere": "physiologique", "is_physiological": true }
  ],
  "bsi": 1.8,
  "super_scan": false,
  "remarques_qualite": []
}
```

Champs : `caractere` ∈ `suspect | dégénératif | bénin | physiologique | indéterminé`. `antecedent` = `null` ou `{ "date": "...", "synthese": "..." }`. `remarques_qualite` = liste (extravasation, mouvement, FOV tronqué…).

> Toutes ces données viennent du pipeline (`ExamAnalysisService` + atlas physiologique). **Aucun identifiant patient** n'est inclus.

---

## 4. Format de sortie

```json
{
  "indication": "Bilan d'extension osseuse d'un adénocarcinome prostatique (PSA 24 ng/mL).",
  "technique": "Balayage scintigraphique du corps entier (incidences antérieure et postérieure) réalisé 3 heures après injection intraveineuse de 740 MBq de Tc-99m HMDP, complété par une acquisition SPECT/CT du rachis dorsolombaire.",
  "resultats": "Deux foyers hyperfixants d'allure suspecte : l'un de l'arc costal droit (8e côte), d'intensité marquée, l'autre du corps vertébral de L3, d'intensité modérée. Fixation modérée des interlignes articulaires des deux genoux, d'allure dégénérative. Fixation physiologique des reins et de la vessie. Bone Scan Index estimé à 1,8. Pas d'aspect de super scan.",
  "conclusion": "Deux foyers hyperfixants d'allure suspecte (8e côte droite et L3), compatibles avec des localisations secondaires dans ce contexte d'adénocarcinome prostatique. Fixation des genoux d'allure dégénérative. À corréler à l'imagerie morphologique. En l'absence d'examen antérieur, aucune comparaison évolutive n'est possible.",
  "alertes": ["Deux foyers classés suspects — confirmation par imagerie morphologique (TDM/IRM) à l'appréciation du médecin."]
}
```

Ce qui est respecté ici : langage prudent (« compatible avec », jamais « métastase »), séparation suspect / dégénératif / physiologique, BSI repris **tel quel**, absence d'antériorité signalée sans être inventée, et les foyers suspects remontés dans `alertes`.

---

## 5. Intégration (exemple Python, SDK Anthropic)

```python
import json
from anthropic import Anthropic

client = Anthropic()  # clé via variable d'environnement

def generate_bone_scan_report(data: dict, system_prompt: str) -> dict:
    message = client.messages.create(
        model="claude-sonnet-4-6",          # configurable via env
        max_tokens=1500,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": "Données de l'examen :\n" + json.dumps(data, ensure_ascii=False)
        }],
        # extra_headers pour la zéro-rétention si applicable
    )
    raw = "".join(b.text for b in message.content if b.type == "text").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    report = json.loads(raw)  # valider les clés attendues avant de stocker
    return report
```

À prévoir côté code : validation du JSON (clés présentes, types corrects), gestion d'erreur si le parsing échoue (relance ou message clair), enregistrement de la **version brouillon** + de la **version du modèle** (traçabilité, cf. `05_CONTRAINTES_SECURITE.md`).

---

## 6. Garde-fous — pourquoi chacun compte

| Garde-fou | Risque évité |
|---|---|
| Utiliser uniquement les données fournies | Hallucination d'un foyer ou d'une mesure inexistante |
| Valeurs reprises telles quelles | Altération d'un chiffre clinique (BSI, activité) |
| Langage prudent imposé | Faux diagnostic présenté comme certain |
| Séparation physiologique / suspect | Prendre reins/vessie (normaux) pour des lésions |
| `alertes` plutôt que trancher | L'IA tranche à la place du médecin |
| Pas de reco thérapeutique | Sortie du périmètre « aide à la décision » |
| Mention « brouillon » ajoutée par l'UI | Un CR IA pris pour un CR validé |

---

## 7. Réutilisation pour les autres examens

Le squelette (rôle, règles absolues, format JSON, garde-fous) est commun. Pour chaque nouvel examen, on remplace :
- le **bloc « connaissances de référence »** (atlas physiologique + logique propre au traceur),
- le **score** attendu (Krenning, Curie, FEVG/SSS, PIOPED…),
- les **exemples**.
→ Un prompt par examen, même structure. Prochain candidat logique : **Octréotide (Krenning)**.
