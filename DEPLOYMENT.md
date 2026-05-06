# DEPLOYMENT — lift_site (production)

## 1) Подготовка сервера (Ubuntu)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip nginx
```

## 2) Развёртывание проекта

```bash
sudo mkdir -p /var/www/lift_site
sudo chown -R $USER:$USER /var/www/lift_site
# скопируйте файлы проекта в /var/www/lift_site

cd /var/www/lift_site
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## 3) Конфигурация окружения

```bash
cp .env.example .env
nano .env
```

Минимально обязательно задать:
- `SECRET_KEY`
- `ADMIN_PASSWORD`

Рекомендуемо для production:
- `FLASK_DEBUG=false`
- `DESIGN_VARIANT=classic`
- корректные `MAIL_*` и `ADMIN_EMAIL`

## 4) Проверка запуска приложения

```bash
source /var/www/lift_site/venv/bin/activate
cd /var/www/lift_site
python -m compileall app.py config.py
gunicorn -w 3 -b 127.0.0.1:5000 app:app
```

Проверьте страницы:
- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/services`
- `http://127.0.0.1:5000/contacts`
- `http://127.0.0.1:5000/admin`

## 5) Systemd service

Создайте `/etc/systemd/system/lift_site.service`:

```ini
[Unit]
Description=lift_site gunicorn service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/lift_site
Environment="PATH=/var/www/lift_site/venv/bin"
ExecStart=/var/www/lift_site/venv/bin/gunicorn -w 3 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lift_site
sudo systemctl status lift_site
```

## 6) Nginx reverse proxy

Создайте `/etc/nginx/sites-available/lift_site`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /static/ {
        alias /var/www/lift_site/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активация:

```bash
sudo ln -sf /etc/nginx/sites-available/lift_site /etc/nginx/sites-enabled/lift_site
sudo nginx -t
sudo systemctl restart nginx
```

## 7) Финальная проверка

```bash
sudo systemctl status lift_site
sudo systemctl status nginx
curl -I http://127.0.0.1
```

Проверьте отправку формы на `/contacts` и наличие записи в админ-панели.
