#!/bin/bash
# ============================================================
# deploy.sh — Installation initiale E-DÉFENCE sur Ubuntu 22.04
# Usage : bash deploy.sh
# Prérequis : Ubuntu 22.04 LTS, accès root, domaines DNS pointés
# ============================================================
set -e

APP_DIR="/opt/edefence"
REPO="https://github.com/LnDevAi/analyse-etats-financiers.git"

echo "======================================================"
echo " E-DÉFENCE V4 — Déploiement initial"
echo "======================================================"

# ── 1. Dépendances système ──────────────────────────────────
echo "[1/7] Installation Docker, Nginx, Certbot..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    docker.io docker-compose-v2 \
    nginx certbot python3-certbot-nginx \
    git curl

systemctl enable --now docker nginx

# ── 2. Cloner le repo ──────────────────────────────────────
echo "[2/7] Clonage du repo..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull origin main
else
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# ── 3. Fichier .env ────────────────────────────────────────
echo "[3/7] Configuration .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo "⚠️  IMPORTANT : Éditez $APP_DIR/.env avant de continuer."
    echo "   Renseignez SECRET_KEY, DB_PASSWORD, REDIS_PASSWORD,"
    echo "   ANTHROPIC_API_KEY, SMTP_*, CINETPAY_*."
    echo ""
    echo "   nano $APP_DIR/.env"
    echo ""
    read -p "Appuyez sur Entrée une fois le .env configuré..."
fi

# ── 4. Nginx + TLS ─────────────────────────────────────────
echo "[4/7] Configuration Nginx..."
cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/edefence
ln -sf /etc/nginx/sites-available/edefence /etc/nginx/sites-enabled/edefence
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "[4b/7] Certificat TLS Let's Encrypt..."
certbot --nginx \
    -d app.edefence.tech \
    -d api.edefence.tech \
    --non-interactive --agree-tos -m admin@edefence.tech

# Renouvellement automatique
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && nginx -s reload") | crontab -

# ── 5. Build et lancement ──────────────────────────────────
echo "[5/7] Build Docker Compose..."
cd "$APP_DIR"
docker compose -f docker-compose.prod.yml up -d --build

# ── 6. Migrations et seed ──────────────────────────────────
echo "[6/7] Migrations Alembic..."
sleep 10  # attendre que PostgreSQL soit prêt
docker compose -f docker-compose.prod.yml exec backend \
    alembic upgrade head

echo "[6b/7] Seed des plans d'abonnement..."
docker compose -f docker-compose.prod.yml exec backend \
    python -m app.services.seed_plans || true

# ── 7. Vérification ────────────────────────────────────────
echo "[7/7] Vérification..."
sleep 5
curl -sf https://api.edefence.tech/api/health && \
    echo "✅ API en ligne" || echo "⚠️  API non disponible (vérifiez les logs)"

echo ""
echo "======================================================"
echo " Déploiement terminé !"
echo " Frontend : https://app.edefence.tech"
echo " API      : https://api.edefence.tech/api/docs"
echo " Logs     : docker compose -f /opt/edefence/docker-compose.prod.yml logs -f"
echo "======================================================"
