# E-DÉFENCE — Analyse États Financiers IA

**Plateforme SaaS d'analyse financière et d'audit augmenté par Intelligence Artificielle — V4**

Zone marché : Burkina Faso & Espace UEMOA

---

## Segments de marché

| Segment | Usage |
|---------|-------|
| Cabinets d'Expertise Comptable & Commissariat | Automatisation de la révision, détection anomalies N vs N-1, génération de rapports |
| Administration Fiscale | Détection fraudes fiscales, analyse FEC exhaustive |
| Banques & Établissements de Crédit | Cross-checking bilans, score de risque dynamique |

## Modules IA

- **Ingestion FEC** — Parseur multi-format (encodage, séparateur) conforme SYSCOHADA UEMOA
- **Vérification intrinsèque** — Équilibre Débit = Crédit par écriture
- **Loi de Benford** — Chi-square test sur distribution des premiers chiffres
- **Isolation Forest** — Détection anomalies ML non supervisée (Scikit-learn)
- **Revue analytique N vs N-1** — Variations par compte SYSCOHADA classes 1-9
- **Cycle Ventes/Clients** — Détection anomalies cut-off
- **Cycle Trésorerie** — Flux suspects (week-end, sans libellé, montants ronds)
- **Score de risque 0-100** — VERT / ORANGE / ROUGE
- **Génération rapports** — Word (.docx) + Excel (.xlsx) + synthèse Claude IA

## Stack technique

| Couche | Technologies |
|--------|-------------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy async · Alembic |
| IA / ML | Pandas · NumPy · Scikit-learn · SciPy · Anthropic Claude |
| Frontend | Next.js 14 · Tailwind CSS · Recharts · Zustand |
| Base de données | PostgreSQL 16 (multi-tenant) · Redis 7 |
| Sécurité | JWT · TOTP MFA · AES-256 · RBAC · Logs immuables |
| Infrastructure | Docker · Docker Compose · Nginx TLS |

## Démarrage rapide

```bash
# 1. Variables d'environnement
cp .env.example .env
# Renseigner ANTHROPIC_API_KEY, SECRET_KEY, AES_KEY

# 2. Lancer la stack complète
docker-compose up -d

# 3. Accéder à l'application
# Frontend : http://localhost:3000
# API docs : http://localhost:8000/api/docs
```

## Développement local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Workflow Git

```
feature/* ──PR──► dev ──PR──► main
```

- `main` — production, protégée (PR + 1 approbation, enforce_admins)
- `dev` — intégration, protégée (PR + 1 approbation)
- `feature/frontend-neya` — UI Next.js (MoussaNEYA)
- `feature/security-zombre` — Sécurité & DevOps (burkinabe)

## Équipe

| Rôle | Responsabilité |
|------|---------------|
| Manager / Chef de Projet | Gouvernance, backlog, validation métier |
| Expert Full Stack | Architecture FastAPI, pipeline IA, prompts Claude |
| Expert Cybersécurité | JWT/MFA, AES-256, OWASP, audit sécurité |
| Stagiaire Full Stack (MoussaNEYA) | UI Next.js, tableaux de bord, exports |
| Stagiaire Cyber & Dev (burkinabe) | Auth, anonymisation NLP, logs, SAST |

---

*E-DÉFENCE SaaS — RCCM N°BFOUA2020B1917, IFU N°00133508R — © 2026 Tous droits réservés*
