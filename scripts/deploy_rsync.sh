#!/usr/bin/env bash
# Выгрузка кода на сервер без перезаписи .env, паролей и почты.
# chmod +x scripts/deploy_rsync.sh
#
# Вариант 1 — отдельно логин и хост (без «собаки» в DEPLOY_HOST):
#   export DEPLOY_HOST="etazhi-lifts.online"
#   export DEPLOY_USER="deploy"
#
# Вариант 2 — одной строкой (тогда DEPLOY_USER не нужен):
#   export DEPLOY_SSH="deploy@etazhi-lifts.online"
#
# Не подставляйте в DEPLOY_HOST: https://, порты :22, пробелы, перевод строки после копирования.

set -euo pipefail

trim() { printf '%s' "$1" | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="$(trim "${DEPLOY_REMOTE:-/var/www/etazhi-lifts}")"

if [[ -n "${DEPLOY_SSH:-}" ]]; then
  SSH_TARGET="$(trim "$DEPLOY_SSH")"
else
  HOST="$(trim "${DEPLOY_HOST:?Задайте DEPLOY_HOST (только домен или IP, без user@) или полностью DEPLOY_SSH=user@host})")"
  USER="${DEPLOY_USER:-deploy}"
  USER="$(trim "$USER")"
  if [[ "$HOST" == *"@"* ]]; then
    echo "Ошибка: в DEPLOY_HOST не должно быть «user@». Укажите только домен или IP." >&2
    echo "Пример: export DEPLOY_HOST=\"123.45.67.89\"" >&2
    echo "Или:    export DEPLOY_SSH=\"мойлогин@123.45.67.89\"" >&2
    exit 1
  fi
  SSH_TARGET="${USER}@${HOST}"
fi

if [[ "$SSH_TARGET" != *"@"* ]]; then
  echo "Ошибка: адрес SSH должен быть вида user@host. Сейчас: $SSH_TARGET" >&2
  exit 1
fi

echo "→ Локально: $ROOT"
echo "→ Куда:    ${SSH_TARGET}:${REMOTE}/"
echo "→ Не копируем: .env, базы, instance, .venv, логи"
echo "→ Опционально: статические видео можно не копировать при DEPLOY_SKIP_VIDEOS=true"
echo ""

EXTRA_EXCLUDES=()
if [[ "${DEPLOY_SKIP_VIDEOS:-false}" == "true" ]]; then
  EXTRA_EXCLUDES+=(--exclude 'static/videos/')
fi

rsync -avz -e ssh \
  --exclude '.env' \
  --exclude '.env.save' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.git/' \
  --exclude '.pytest_cache/' \
  --exclude '*.db' \
  --exclude 'instance/' \
  --exclude 'etazhi.log' \
  --exclude '*.log' \
  "${EXTRA_EXCLUDES[@]}" \
  "$ROOT/" \
  "${SSH_TARGET}:${REMOTE}/"

echo ""
echo "Готово. На сервере (при необходимости):"
echo "  ssh ${SSH_TARGET} 'cd ${REMOTE} && .venv/bin/pip install -r requirements.txt && sudo systemctl restart etazhi'"
