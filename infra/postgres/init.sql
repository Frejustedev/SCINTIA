-- Scintia — Postgres init (Phase 0).
-- The schema (15 tables, docs/04_MODELE_DONNEES.md) is created via SQLAlchemy /
-- migrations from Phase 1. This file only runs on first container start and is
-- intentionally a no-op for now.
SELECT 'scintia: database initialized' AS note;
