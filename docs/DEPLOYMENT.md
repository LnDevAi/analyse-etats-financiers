# Guide de déploiement — E-DÉFENCE V4

## Architecture de production

```
Internet
    │ HTTPS :443
    ▼
Nginx (reverse proxy + TLS Let's Encrypt)
    ├── /          → Next.js :3000
    └── /api/      → FastAPI :8000

FastAPI :8000
    ├── PostgreSQL :5432 (volume persistant)
    └── Redis :6379 (volume persistant)
```

---

## Docker Compose (production)

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: analyse_financiere
      POSTGRES_USER: edefence
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U edefence"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    restart: always
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - uploads:/var/edefence/uploads
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: https://api.edefence.tech/api/v1
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  uploads:
```

---

## Configuration Nginx

### `/etc/nginx/sites-available/edefence`

```nginx
# Frontend
server {
    listen 443 ssl http2;
    server_name app.edefence.tech;

    ssl_certificate     /etc/letsencrypt/live/edefence.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/edefence.tech/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API Backend
server {
    listen 443 ssl http2;
    server_name api.edefence.tech;

    ssl_certificate     /etc/letsencrypt/live/edefence.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/edefence.tech/privkey.pem;

    client_max_body_size 55M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name app.edefence.tech api.edefence.tech;
    return 301 https://$host$request_uri;
}
```

---

## Certificat TLS (Let's Encrypt)

```bash
# Installation Certbot
apt install certbot python3-certbot-nginx -y

# Génération certificat wildcard
certbot certonly --nginx -d edefence.tech -d app.edefence.tech -d api.edefence.tech

# Renouvellement automatique (cron)
echo "0 3 * * * certbot renew --quiet && nginx -s reload" | crontab -
```

---

## Variables d'environnement de production (`.env`)

```env
# Sécurité
SECRET_KEY=<64 chars hex — python -c "import secrets; print(secrets.token_hex(32))">
AES_KEY=<32 chars — python -c "import secrets; print(secrets.token_urlsafe(24)[:32])">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false

# Base de données
DATABASE_URL=postgresql+asyncpg://edefence:${DB_PASSWORD}@db:5432/analyse_financiere
DATABASE_SYNC_URL=postgresql://edefence:${DB_PASSWORD}@db:5432/analyse_financiere
DB_PASSWORD=<mot de passe fort>

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=<mot de passe fort>

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@edefence.tech
SMTP_PASSWORD=<app password Gmail>
SMTP_FROM_EMAIL=noreply@edefence.tech
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=true
FRONTEND_URL=https://app.edefence.tech

# CinetPay
CINETPAY_API_KEY=<clé production CinetPay>
CINETPAY_SITE_ID=<site ID production>
BACKEND_URL=https://api.edefence.tech

# Upload
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=/var/edefence/uploads

# CORS
ALLOWED_ORIGINS=["https://app.edefence.tech"]
```

---

## Procédure de déploiement initial

```bash
# 1. Cloner et configurer
git clone https://github.com/LnDevAi/analyse-etats-financiers.git /opt/edefence
cd /opt/edefence
cp .env.example .env
nano .env    # renseigner toutes les valeurs

# 2. Build et lancement
docker-compose -f docker-compose.yml up -d --build

# 3. Migrations
docker-compose exec backend alembic upgrade head

# 4. Seeder plans
docker-compose exec backend python -m app.services.seed_plans

# 5. Nginx
cp nginx.conf /etc/nginx/sites-available/edefence
ln -s /etc/nginx/sites-available/edefence /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 6. TLS
certbot --nginx -d app.edefence.tech -d api.edefence.tech
```

---

## Mise à jour (rolling update)

```bash
cd /opt/edefence
git pull origin main

# Rebuild uniquement les services modifiés
docker-compose up -d --build backend frontend

# Appliquer nouvelles migrations si nécessaire
docker-compose exec backend alembic upgrade head

# Vérifier les logs
docker-compose logs -f backend --tail=50
```

---

## Sauvegarde PostgreSQL

```bash
# Sauvegarde quotidienne
docker-compose exec db pg_dump -U edefence analyse_financiere | gzip > \
    /backups/edefence_$(date +%Y%m%d).sql.gz

# Restauration
gunzip -c /backups/edefence_20260527.sql.gz | \
    docker-compose exec -T db psql -U edefence analyse_financiere
```

Automatiser avec cron :
```bash
0 2 * * * cd /opt/edefence && docker-compose exec -T db \
  pg_dump -U edefence analyse_financiere | gzip > \
  /backups/edefence_$(date +\%Y\%m\%d).sql.gz
```

---

## Monitoring

### Health checks

```bash
# API
curl https://api.edefence.tech/api/health

# Base de données (depuis le conteneur)
docker-compose exec db pg_isready -U edefence

# Redis
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# Tous les services
docker-compose logs -f

# Backend uniquement
docker-compose logs -f backend --tail=100

# Erreurs uniquement
docker-compose logs backend | grep -i error
```

---

## Sécurité en production

- [ ] `DEBUG=false` dans `.env`
- [ ] `ALLOWED_ORIGINS` restreint au domaine de production
- [ ] Firewall : ports 80 et 443 uniquement ouverts publiquement
- [ ] PostgreSQL et Redis non exposés publiquement (ports internes Docker uniquement)
- [ ] Sauvegardes chiffrées et stockées hors site
- [ ] Rotation des secrets tous les 90 jours
- [ ] Certificat TLS valide et renouvellement automatique activé
