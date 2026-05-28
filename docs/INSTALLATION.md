# Guide d'installation — E-DÉFENCE V4

## Prérequis système

| Composant | Version minimale |
|-----------|-----------------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Python | 3.12+ (dev local) |
| Node.js | 20 LTS (dev local) |
| PostgreSQL | 16 (géré par Docker) |
| Redis | 7 (géré par Docker) |

---

## Variables d'environnement

Copier `.env.example` → `.env` et renseigner toutes les valeurs.

### Sécurité (obligatoire)

```env
SECRET_KEY=<chaîne aléatoire 64 caractères hex>
AES_KEY=<chaîne aléatoire exactement 32 caractères>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Générer des clés sécurisées :
```bash
python -c "import secrets; print(secrets.token_hex(32))"  # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(24)[:32])"  # AES_KEY
```

### Base de données

```env
DATABASE_URL=postgresql+asyncpg://edefence:motdepasse@localhost:5432/analyse_financiere
DATABASE_SYNC_URL=postgresql://edefence:motdepasse@localhost:5432/analyse_financiere
```

### Redis

```env
REDIS_URL=redis://localhost:6379/0
```

Avec authentification Redis :
```env
REDIS_URL=redis://:motdepasse@localhost:6379/0
```

### Anthropic (IA)

```env
ANTHROPIC_API_KEY=sk-ant-...
```

Obtenir une clé sur [console.anthropic.com](https://console.anthropic.com).

### Email / SMTP

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@edefence.tech
SMTP_PASSWORD=motdepasse_application
SMTP_FROM_EMAIL=noreply@edefence.tech
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=true
FRONTEND_URL=https://app.edefence.tech
RESET_TOKEN_EXPIRE_MINUTES=30
```

### CinetPay (paiements)

```env
CINETPAY_API_KEY=<clé CinetPay>
CINETPAY_SITE_ID=<site ID CinetPay>
BACKEND_URL=https://api.edefence.tech
```

Compte CinetPay : [cinetpay.com](https://cinetpay.com)  
Mode sandbox disponible pour les tests.

### Upload de fichiers

```env
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=/var/edefence/uploads
```

### CORS

```env
ALLOWED_ORIGINS=["https://app.edefence.tech","http://localhost:3000"]
```

---

## Installation avec Docker

### 1. Cloner et configurer

```bash
git clone https://github.com/LnDevAi/analyse-etats-financiers.git
cd analyse-etats-financiers
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 2. Lancer les conteneurs

```bash
docker-compose up -d
```

Services démarrés :
- `db` — PostgreSQL 16 sur le port 5432
- `redis` — Redis 7 sur le port 6379
- `backend` — FastAPI sur le port 8000
- `frontend` — Next.js sur le port 3000

### 3. Appliquer les migrations

```bash
docker-compose exec backend alembic upgrade head
```

Les 5 migrations sont appliquées dans l'ordre :
1. `001` — Tables de base (tenants, users, documents, analyses, anomalies, audit_logs)
2. `002` — Colonnes cohérence SYSCOHADA et balance générale
3. `003` — Table ag_analyses
4. `004` — Tables CRM (crm_clients, crm_contacts, activity_logs)
5. `005` — Tables billing (subscription_plans, subscriptions, invoices, payments)

### 4. Initialiser les plans d'abonnement

```bash
docker-compose exec backend python -m app.services.seed_plans
```

Crée les 3 plans : Starter (25 000 FCFA), Pro (75 000 FCFA), Enterprise (sur devis).

### 5. Créer le premier compte administrateur

```bash
docker-compose exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import hash_password
import uuid

async def create_admin():
    async with AsyncSessionLocal() as db:
        tenant = Tenant(name='E-DÉFENCE', slug='edefence')
        db.add(tenant)
        await db.flush()
        user = User(
            email='admin@edefence.tech',
            full_name='Administrateur',
            hashed_password=hash_password('MotDePasse123!'),
            role=UserRole.ASSOCIE,
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f'Admin créé : admin@edefence.tech')

asyncio.run(create_admin())
"
```

---

## Installation locale (développement)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

pip install -r requirements.txt
cp ../.env.example .env          # ou utiliser le .env racine

alembic upgrade head
python -m app.services.seed_plans

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Variables d'environnement Next.js
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

npm run dev
```

### Lancer les tests

```bash
cd backend
pytest tests/ -v

# Tests par module
pytest tests/test_crm.py -v
pytest tests/test_billing.py -v
pytest tests/test_coherence_checker.py -v
pytest tests/test_balance_reconciliation.py -v
pytest tests/test_cycle_audit.py -v
pytest tests/test_analytical_review.py -v
pytest tests/test_ag_document_analyzer.py -v
```

---

## Vérification de l'installation

```bash
# API health check
curl http://localhost:8000/api/health

# Swagger UI
open http://localhost:8000/api/docs

# Frontend
open http://localhost:3000
```

Réponse attendue du health check :
```json
{"status": "ok", "version": "4.0.0"}
```
