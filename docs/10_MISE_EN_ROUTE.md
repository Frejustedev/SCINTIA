# 10 — Mise en route (runbook opérationnel)

Guide pas-à-pas pour lancer Scintia et **débloquer** les intégrations réelles
(Claude, GPU/TotalSegmentator, DICOM, production). Les variables citées sont
décrites dans [`.env.example`](../.env.example).

> ⚠️ Rappel : **prototype de recherche**, pas un dispositif médical certifié. Ne
> jamais committer de DICOM, de secret, ni de `.env` (le hook pre-commit les bloque).

---

## 1. Prérequis

- **Docker Desktop** (Postgres + Redis, ou stack complète).
- **Python 3.12** et **Node 20+** (pour lancer hors Docker / développer).
- **Optionnel** : machine **GPU NVIDIA ≥ 8 Go** pour la vraie segmentation.

## 2. Configuration

```bash
bash scripts/init-env.sh     # crée .env avec des secrets locaux aléatoires
```

Vérifiez/ajustez `.env` : `SECRET_KEY` et `IDENTITY_ENCRYPTION_KEY` (forts, gérés
**hors base**), `BACKEND_CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`.

## 3. Démarrage rapide (Docker)

```bash
docker compose up -d postgres redis     # bases
cd backend && alembic upgrade head       # crée le schéma (toutes les migrations)
docker compose up --build                # backend + frontend (ou voir §4 pour le local)
```

- API : `http://localhost:8000/health` → `{"status":"ok"}`
- Frontend : `http://localhost:3000`

## 4. Démarrage local (sans Docker pour l'app)

Avec Postgres + Redis lancés (Docker) et le `.env` chargé :

```bash
# Backend
cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000
# Worker Celery (asynchrone) — Windows : --pool=solo
celery -A app.workers.celery_app:celery_app worker --loglevel=info
# Frontend
cd frontend && npm install && npm run dev
```

## 5. Premier compte

À la première utilisation, l'écran de connexion propose **« créer un
administrateur »** (ou `POST /api/v1/users/bootstrap-admin`). L'admin crée ensuite
les comptes **médecin / physicien / manipulateur** (`POST /api/v1/users`).

| Rôle | Peut |
|---|---|
| `medecin` | tout voir + **valider** le compte-rendu + export PDF ré-identifié |
| `admin` | gérer les comptes, lancer l'analyse, **effacer** un examen |
| `manipulateur` / `physicien` | gèrent **leurs** examens uniquement (RBAC) |

**MFA (optionnel)** : `POST /api/v1/auth/mfa/setup` puis `/mfa/enable` avec un code
TOTP. Une fois activé, la connexion exige le code.

## 6. Activer Claude (brouillon de CR par l'IA)

1. Créez une clé sur la console Anthropic et **activez la zéro-rétention** au niveau
   de l'organisation (réglage du compte, pas du code).
2. Dans `.env` : `ANTHROPIC_API_KEY=sk-ant-…` et `REPORT_BACKEND=claude`.
3. Redémarrez le backend (et le worker). Le contexte envoyé est **anonymisé** (jamais
   d'identifiant patient).

## 7. Activer la vraie segmentation (GPU)

Sur une machine **GPU** : `pip install TotalSegmentator` (+ `SimpleITK`), puis
`.env` : `SEGMENTER_BACKEND=totalsegmentator` (option `SEGMENTER_ROI_SUBSET=`
liste d'organes). Sans GPU/outil, l'adaptateur **échoue franchement** — il ne
fabrique jamais de mesure. Le mode hors-ligne (`stub`) reste disponible pour les tests.

## 8. Importer des DICOM

- **UI** : « Nouvel examen » → choisir le type → déposer un dossier, un `.zip` ou un
  `DICOMDIR`. Les fichiers sont **anonymisés avant tout stockage**, le CT et le SPECT
  sont triés automatiquement.
- **API** : `POST /api/v1/studies` (avec l'identité réelle, chiffrée au repos) puis
  `POST /api/v1/studies/{id}/files`.
- **Toujours des DICOM dé-identifiés.** Lancer l'analyse : `POST /…/analyze`.
- **Visualiseur** : `/studies/{id}/viewer` (coupes + fenêtrage).

## 9. Exports

- **PDF** (ré-identifié, local) : `GET /…/export?format=pdf` (CR **validé** requis).
  Options `?theme=light|dark` ; en-tête d'établissement via `ESTABLISHMENT_NAME` /
  `ESTABLISHMENT_SUBTITLE`.
- **FHIR / DICOM-SR** (pseudonymes, pour RIS/PACS) : `?format=fhir|dicom-sr`.

## 10. Rétention & effacement (RGPD / loi 18-07)

- `PURGE_RAW_DICOM_AFTER_ANALYSIS=true` supprime les DICOM bruts après analyse
  (les résultats dérivés sont conservés).
- **Droit à l'effacement** : `DELETE /api/v1/studies/{id}` (admin/médecin) supprime
  l'examen, ses dérivés, le stockage et l'**identité chiffrée** (si le patient n'a
  plus d'examen). Le **journal d'audit** est conservé (append-only).

## 11. Checklist de mise en PRODUCTION

- [ ] **TLS partout** (reverse-proxy Nginx/Traefik devant l'app) ; `ENABLE_HSTS=true`.
- [ ] **Secrets hors dépôt** (coffre / variables d'environnement du déploiement) ;
      `SECRET_KEY` et `IDENTITY_ENCRYPTION_KEY` gérés **hors base**, rotation prévue.
- [ ] **Chiffrement au repos** (volume Postgres + stockage objet).
- [ ] **Stockage objet** : remplacer le volume local par MinIO/S3 (interface
      `ObjectStorage` déjà en place).
- [ ] `BACKEND_CORS_ORIGINS` limité au domaine réel ; `APP_ENV=production`.
- [ ] **Sauvegardes** base + stockage ; plan de restauration.
- [ ] **Hébergement de données de santé** conforme + **volet réglementaire**
      (statut dispositif médical, RGPD / loi 18-07) — voir [`docs/05`](05_CONTRAINTES_SECURITE.md).
- [ ] Méthodes cliniques **validées et consignées** — voir
      [`docs/09`](09_GABARIT_METHODE_CLINIQUE.md).

## 12. Qualité (développement)

```bash
cd backend && pytest -q && ruff check . && black --check . && mypy app
cd frontend && npm run lint && npm run build
pre-commit install            # active les hooks (bloque DICOM/secrets, formate)
```

La CI (GitHub Actions) rejoue tout cela à chaque push/PR
([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).
