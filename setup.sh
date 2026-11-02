#!/usr/bin/env bash
# ==============================================================================
# Setup & Initializer Script untuk Proyek Integrasi WordPress, Hermes, & 9Router
# ==============================================================================

set -e

# Warna untuk output terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================================${NC}"
echo -e "${BLUE}  Setup Integrasi WordPress + Hermes Agent + 9Router + Telegram    ${NC}"
echo -e "${BLUE}===================================================================${NC}"

# 1. Cek ketersediaan Docker dan Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker tidak ditemukan! Silakan install Docker terlebih dahulu.${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR] Docker Compose (v2) tidak ditemukan!${NC}"
    exit 1
fi

# 2. Pastikan file .env ada
if [ ! -f .env ]; then
    echo -e "${YELLOW}[INFO] File .env tidak ditemukan. Membuat dari .env.example...${NC}"
    cp .env.example .env
fi

# Load variabel lingkungan
source .env

WP_PORT=${WP_PORT:-10000}
ROUTER_PORT=${ROUTER_PORT:-11000}
WP_ADMIN_USER=${WP_ADMIN_USER:-admin}
WP_ADMIN_PASSWORD=${WP_ADMIN_PASSWORD:-adminsecretpassword}
WP_ADMIN_EMAIL=${WP_ADMIN_EMAIL:-admin@example.com}
WP_SITE_TITLE=${WP_SITE_TITLE:-"Portal AI Hermes"}

echo -e "${GREEN}[OK] Konfigurasi termuat: WordPress Port ${WP_PORT}, 9Router Port ${ROUTER_PORT}${NC}"

# 3. Buat folder data persisten lokal jika belum ada
mkdir -p data/9router data/mariadb data/wordpress data/hermes hermes/skills/wordpress-manager/scripts
chmod +x hermes/skills/wordpress-manager/scripts/wp_manager.py

# 4. Jalankan Database MariaDB dan WordPress terlebih dahulu
echo -e "\n${BLUE}[1/4] Menjalankan container MariaDB dan WordPress...${NC}"
docker compose up -d db wordpress

echo -e "${YELLOW}Menunggu database dan WordPress siap menerima koneksi (sekitar 10-20 detik)...${NC}"
MAX_RETRIES=30
COUNT=0
IS_READY=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    if docker compose run --rm --no-deps wpcli wp core is-installed --path=/var/www/html 2>/dev/null; then
        echo -e "${GREEN}[OK] WordPress sudah terinstall!${NC}"
        IS_READY=true
        break
    elif docker compose run --rm --no-deps wpcli wp db check --path=/var/www/html 2>/dev/null; then
        echo -e "${GREEN}[OK] Database siap! Memulai instalasi WordPress...${NC}"
        IS_READY=true
        
        # Jalankan instalasi WordPress otomatis
        docker compose run --rm wpcli wp core install \
            --path=/var/www/html \
            --url="http://localhost:${WP_PORT}" \
            --title="${WP_SITE_TITLE}" \
            --admin_user="${WP_ADMIN_USER}" \
            --admin_password="${WP_ADMIN_PASSWORD}" \
            --admin_email="${WP_ADMIN_EMAIL}" \
            --skip-email
        
        echo -e "${GREEN}[OK] WordPress berhasil diinstall otomatis!${NC}"
        break
    fi
    sleep 2
    COUNT=$((COUNT+1))
    echo -n "."
done

if [ "$IS_READY" = false ]; then
    echo -e "\n${YELLOW}[PERINGATAN] WordPress membutuhkan waktu lebih lama untuk start. Melanjutkan langkah berikutnya...${NC}"
fi

# 5. Konfigurasi REST API & Application Password untuk Hermes Agent
echo -e "\n${BLUE}[2/4] Mengonfigurasi REST API & Application Password untuk Hermes Agent...${NC}"

# Aktifkan rewrite structure untuk /wp-json/ permalink
docker compose run --rm wpcli wp rewrite structure '/%postname%/' --quiet 2>/dev/null || true

# Aktifkan mu-plugin agar Application Passwords diizinkan di HTTP localhost
docker compose exec -u 0 wordpress sh -c "mkdir -p /var/www/html/wp-content/mu-plugins && cat << 'EOF' > /var/www/html/wp-content/mu-plugins/enable-app-passwords.php
<?php
add_filter( 'wp_is_application_passwords_available', '__return_true' );
EOF
chown -R www-data:www-data /var/www/html/wp-content/mu-plugins" 2>/dev/null || true

APP_PASS_GEN=$(docker compose run --rm wpcli wp user application-password create "${WP_ADMIN_USER}" "HermesAgentBot" --porcelain 2>/dev/null || true)

if [ -n "$APP_PASS_GEN" ]; then
    echo -e "${GREEN}[OK] Application Password berhasil dibuat: ${APP_PASS_GEN}${NC}"
    # Update ke file .env
    sed -i "s/^WP_APP_PASSWORD=.*/WP_APP_PASSWORD=${APP_PASS_GEN}/" .env
    export WP_APP_PASSWORD="${APP_PASS_GEN}"
else
    echo -e "${YELLOW}[INFO] Gunakan Application Password yang sudah ada di .env atau buat manual di WP Admin jika belum ada.${NC}"
fi

# 6. Jalankan 9Router dan Hermes Agent
echo -e "\n${BLUE}[3/4] Menjalankan container 9Router dan Hermes Agent...${NC}"
docker compose up -d 9router hermes

# 7. Informasi Ringkasan & Petunjuk
echo -e "\n${GREEN}===================================================================${NC}"
echo -e "${GREEN}  SEMUA LAYANAN BERHASIL DIKONFIGURASI DAN DIJALANKAN!             ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo -e "1. ${BLUE}WordPress Website${NC}   : http://localhost:${WP_PORT}"
echo -e "   - WP-Admin Login     : http://localhost:${WP_PORT}/wp-admin"
echo -e "   - Username           : ${WP_ADMIN_USER}"
echo -e "   - Password           : ${WP_ADMIN_PASSWORD}"
echo -e ""
echo -e "2. ${BLUE}9Router Dashboard${NC}   : http://localhost:${ROUTER_PORT}"
echo -e "   - Password Login     : ${ROUTER_PASSWORD:-admin123456}"
echo -e "   - Buka URL ini di browser untuk memasukkan Google Gemini API Key Anda."
echo -e ""
echo -e "3. ${BLUE}Hermes Agent (Telegram)${NC}:"
echo -e "   - Pastikan TELEGRAM_BOT_TOKEN dan TELEGRAM_ALLOWED_USERS sudah diisi di .env"
echo -e "   - Restart hermes jika Anda baru saja mengubah .env: ${YELLOW}docker compose restart hermes${NC}"
echo -e "   - Periksa log Hermes dengan: ${YELLOW}docker compose logs -f hermes${NC}"
echo -e ""
echo -e "4. ${BLUE}Uji Coba Integrasi${NC}   : Jalankan ${YELLOW}python3 test_integration.py${NC}"
echo -e "${GREEN}===================================================================${NC}"
