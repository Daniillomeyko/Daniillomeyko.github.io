#!/usr/bin/env bash
set -euo pipefail

SERVER_HOST="${SERVER_HOST:-193.233.20.17}"
SERVER_USER="${SERVER_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/var/www/etazhi-lifts}"
SSH_TARGET="${SERVER_USER}@${SERVER_HOST}"

echo "==> Sync project to ${SSH_TARGET}:${REMOTE_DIR}"
rsync -avz --delete \
  --exclude ".venv" \
  --exclude "venv" \
  --exclude "__pycache__" \
  --exclude ".git" \
  ./ "${SSH_TARGET}:${REMOTE_DIR}/"

echo "==> Run remote setup/restart"
ssh "${SSH_TARGET}" "bash -s" <<'EOF'
set -euo pipefail
cd /var/www/etazhi-lifts

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

chown -R www-data:www-data /var/www/etazhi-lifts
chmod -R u+rwX /var/www/etazhi-lifts

cp /var/www/etazhi-lifts/deploy/systemd/etazhi.service /etc/systemd/system/etazhi.service
systemctl daemon-reload
systemctl enable etazhi
systemctl restart etazhi

cp /var/www/etazhi-lifts/deploy/nginx/etazhi-lifts.online.conf /etc/nginx/sites-available/etazhi-lifts.online
ln -sf /etc/nginx/sites-available/etazhi-lifts.online /etc/nginx/sites-enabled/etazhi-lifts.online
rm -f /etc/nginx/sites-enabled/lift_site
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Service status"
systemctl status etazhi --no-pager | sed -n '1,20p'
echo "==> Quick HTTP checks"
curl -I https://etazhi-lifts.online/ || true
curl -I https://etazhi-lifts.online/news || true
curl -I https://etazhi-lifts.online/robots.txt || true
curl -I https://etazhi-lifts.online/sitemap.xml || true
EOF

echo "==> Done"
