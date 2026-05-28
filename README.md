# E-DÉFENCE — Analyse États Financiers IA

> **Plateforme SaaS d'audit financier augmenté par Intelligence Artificielle — V4**  
> Zone marché : Burkina Faso & Espace UEMOA · SYSCOHADA

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/Licence-Propriétaire-red)](SECURITY.md)

---

## Table des matières

1. [Présentation](#présentation)
2. [Modules](#modules)
3. [Architecture](#architecture)
4. [Démarrage rapide](#démarrage-rapide)
5. [Documentation](#documentation)
6. [Équipe](#équipe)

---

## Présentation

E-DÉFENCE est une plateforme SaaS multi-tenant dédiée à l'analyse automatisée des états financiers des organisations opérant sous le référentiel **SYSCOHADA UEMOA**. Elle combine des algorithmes statistiques, du machine learning et l'IA générative (Claude Anthropic) pour produire des rapports d'audit structurés.

### Segments de marché

| Segment | Cas d'usage |
|---------|-------------|
| Cabinets d'expertise comptable | Révision automatisée, détection anomalies N vs N-1, rapports clients |
| Administration fiscale | Détection fraudes FEC, analyse exhaustive des écritures |
| Banques & établissements de crédit | Cross-checking bilans emprunteurs, scoring risque |
| Collectivités & ONG | Analyse AG, exécution budgétaire, passation des marchés |

---

## Modules

### Analyse du FEC (Fichier des Écritures Comptables)

| Module | Description | Poids risque |
|--------|-------------|-------------|
| **Vérification intrinsèque** | Équilibre Débit = Crédit par écriture, écritures déséquilibrées | 20% |
| **Cohérence SYSCOHADA** | Soldes normaux classes 1-9, résultat net Cl.7-Cl.6 vs compte 13x, équilibre Actif/Passif, doublons | 20% |
| **Loi de Benford** | Chi-square sur distribution des premiers chiffres significatifs | 17% |
| **Isolation Forest ML** | Détection non supervisée d'écritures anormales (montant, date, compte) | 15% |
| **Revue analytique N vs N-1** | Variations par compte SYSCOHADA, seuil de déviation configurable | 12% |
| **Cycle Ventes/Clients** | Anomalies cut-off, concentrations de débit par période | 8% |
| **Cycle Trésorerie** | Flux week-end, sans libellé, montants ronds répétés | 8% |

**Score global 0–100** · Niveaux de risque : 🟢 VERT · 🟠 ORANGE · 🔴 ROUGE

### Cohérence & Réconciliation

- **Réconciliation Balance Générale ↔ FEC** — comparaison solde débit/crédit par compte, détection inversions et écarts
- **Cross-checking multi-entités** — comparaison de FEC entre plusieurs entités d'un même groupe

### Analyse AG (Assemblée Générale)

Comparaison automatique entre le FEC et les documents soumis en AG :

| Document | Comparaison réalisée |
|----------|---------------------|
| Rapport d'exécution budgétaire | Budget prévu vs réalisé doc vs réalisé FEC par classe SYSCOHADA |
| Bilan social | Masse salariale document vs comptes 66x FEC |
| Plan de passation des marchés | Montants marchés vs paiements 40x FEC |
| Rapport d'activités | Montants du rapport corrélés aux écritures FEC |

### CRM & Facturation

- **CRM** — pipeline commercial 6 stades, fiche client, contacts, journal d'activités
- **Abonnements** — plans Starter / Pro / Enterprise, périodes d'essai, upgrade/downgrade
- **Facturation** — génération PDF (TVA 18% UEMOA, mentions légales), numérotation séquentielle
- **Paiements** — Orange Money · Wave · Moov Money · Carte bancaire via **CinetPay**

---

## Architecture

```
analyse-etats-financiers/
├── backend/                    # FastAPI · Python 3.12
│   ├── app/
│   │   ├── api/v1/             # Endpoints REST
│   │   ├── models/             # SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic validation
│   │   ├── services/           # Logique métier & IA
│   │   ├── middleware/         # Auth JWT, RBAC, audit logs
│   │   └── core/              # Config, BDD, Redis, sécurité
│   ├── alembic/               # Migrations BDD
│   └── tests/                 # Tests unitaires pytest
│
├── frontend/                   # Next.js 14 · TypeScript
│   ├── app/                   # Pages (App Router)
│   ├── components/            # Composants réutilisables
│   └── lib/                   # API client, store Zustand
│
└── docs/                      # Documentation technique
```

### Stack technique

| Couche | Technologies |
|--------|-------------|
| Backend | Python 3.12 · FastAPI 0.115 · SQLAlchemy 2.0 async · Alembic |
| IA / ML | Pandas · NumPy · Scikit-learn · SciPy · Anthropic Claude Sonnet |
| Frontend | Next.js 14 · Tailwind CSS · Recharts · Zustand · Axios |
| Base de données | PostgreSQL 16 (multi-tenant par `tenant_id`) · Redis 7 |
| Sécurité | JWT RS256 · TOTP MFA · AES-256-GCM · RBAC · Logs immuables |
| Paiements | CinetPay (Orange Money, Wave, Moov, Carte) |
| PDF | ReportLab (factures) · python-docx · openpyxl |
| Infrastructure | Docker · Docker Compose · Nginx TLS |

---

## Démarrage rapide

### Prérequis

- Docker & Docker Compose v2
- Python 3.12+ (développement local uniquement)
- Node.js 20+ (développement local uniquement)

### Avec Docker (recommandé)

```bash
# 1. Cloner le dépôt
git clone https://github.com/LnDevAi/analyse-etats-financiers.git
cd analyse-etats-financiers

# 2. Variables d'environnement
cp .env.example .env
# Éditer .env — voir docs/INSTALLATION.md

# 3. Lancer la stack
docker-compose up -d

# 4. Appliquer les migrations
docker-compose exec backend alembic upgrade head

# 5. Initialiser les plans d'abonnement
docker-compose exec backend python -m app.services.seed_plans

# Accès
# Frontend   → http://localhost:3000
# API        → http://localhost:8000
# Swagger    → http://localhost:8000/api/docs
# ReDoc      → http://localhost:8000/api/redoc
```

### Développement local

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest tests/ -v --tb=short
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](docs/INSTALLATION.md) | Variables d'environnement, base de données, Redis |
| [Architecture](docs/ARCHITECTURE.md) | Multi-tenancy, sécurité, flux de données |
| [Modules IA](docs/MODULES.md) | Détail de chaque algorithme d'analyse |
| [API Reference](docs/API.md) | Tous les endpoints REST avec exemples |
| [CRM & Paiements](docs/CRM_BILLING.md) | Guide CRM, abonnements, intégration CinetPay |
| [Déploiement](docs/DEPLOYMENT.md) | Docker, Nginx, SSL, variables de production |

L'interface Swagger interactive est disponible à `/api/docs` sur toute instance déployée.

---

## Équipe

| Rôle | Responsabilité |
|------|---------------|
| Chef de Projet / Architecte | Gouvernance, backlog, architecture, pipeline IA |
| Expert Cybersécurité | JWT/MFA, AES-256, OWASP, audit sécurité |
| Développeur Full Stack (MoussaNEYA) | UI Next.js, tableaux de bord, Recharts |
| Développeur Cyber & Dev (burkinabe) | Auth, anonymisation NLP, logs immuables |

---

## Sécurité

Voir [SECURITY.md](SECURITY.md) pour signaler une vulnérabilité.

---

*E-DÉFENCE SaaS · RCCM N°BFOUA2020B1917 · IFU N°00133508R · © 2026 Tous droits réservés*
