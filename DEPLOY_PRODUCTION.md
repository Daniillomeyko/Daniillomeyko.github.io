# Прод-развертывание `etazhi-lifts.online` (Ubuntu + Nginx + Gunicorn + systemd)

## 1) Подготовка сервера

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx rsync
```

## 2) Создать директорию проекта

```bash
mkdir -p /var/www/etazhi-lifts
chown -R www-data:www-data /var/www/etazhi-lifts
```

## 3) Загрузить проект на сервер

Запускать на вашем локальном компьютере из папки проекта:

```bash
rsync -avz --delete \
  --exclude ".venv" \
  --exclude "venv" \
  --exclude "__pycache__" \
  --exclude ".git" \
  ./ root@193.233.20.17:/var/www/etazhi-lifts/
```

## 4) Настроить Python-окружение

```bash
cd /var/www/etazhi-lifts
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5) Настроить `.env`

```bash
cd /var/www/etazhi-lifts
cp .env.example .env
nano .env
```

Минимально важно:
- `SECRET_KEY` (новый длинный случайный ключ)
- `ADMIN_PASSWORD` (новый пароль админки)
- `YANDEX_METRIKA_ID` (ваш ID счетчика)
- `FLASK_DEBUG=false`

## 6) Подключить systemd сервис

```bash
cp deploy/systemd/etazhi.service /etc/systemd/system/etazhi.service
systemctl daemon-reload
systemctl enable etazhi
systemctl restart etazhi
systemctl status etazhi --no-pager
```

## 7) Подключить Nginx

```bash
cp deploy/nginx/etazhi-lifts.online.conf /etc/nginx/sites-available/etazhi-lifts.online
ln -sf /etc/nginx/sites-available/etazhi-lifts.online /etc/nginx/sites-enabled/etazhi-lifts.online
nginx -t
systemctl restart nginx
```

## 8) Включить HTTPS (Let's Encrypt)

```bash
certbot --nginx -d etazhi-lifts.online -d www.etazhi-lifts.online
```

## 9) Проверка после запуска

```bash
curl -I https://etazhi-lifts.online
curl -I https://etazhi-lifts.online/robots.txt
curl -I https://etazhi-lifts.online/sitemap.xml
curl -I https://etazhi-lifts.online/news
```

Ожидаемо:
- `200` на главной, `robots.txt`, `sitemap.xml`, `/news`
- Админка открывается на `/admin`

## 10) Если на сервере уже есть старый сайт

После успешной проверки нового:
- отключить старый systemd-сервис;
- удалить старый nginx-конфиг из `sites-enabled`;
- перезапустить nginx.

Пример:

```bash
systemctl stop OLD_SERVICE_NAME
systemctl disable OLD_SERVICE_NAME
rm -f /etc/nginx/sites-enabled/OLD_SITE_CONF
nginx -t && systemctl reload nginx
```

## Безопасность (обязательно)

- Сменить все пароли, которые уже где-либо публиковались.
- Отключить SSH-вход по паролю после настройки ключей.
- Оставить доступ в админку только по сильному паролю.

