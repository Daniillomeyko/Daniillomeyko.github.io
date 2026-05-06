# Инструкция по деплою lift_site

## Домен и сервер
- **Домен:** etazhi-lifts.online
- **IP:** 193.233.20.17
- **Пользователь SSH:** root

## Пароли и учётные данные
- **Пароль админки:** `Gsm&G0zMhtj*y#1o0XV3`
- **SECRET_KEY:** сгенерировать новый или оставить текущий (не для production)

## Шаги деплоя

### 1. Подключение к серверу
```bash
ssh root@193.233.20.17
```

### 2. Загрузка проекта на сервер
Вариант A - через scp/sftp:
```bash
# С локальной машины
scp -r lift_site/ root@193.233.20.17:/root/
```

Вариант B - через Git (если есть репозиторий):
```bash
# На сервере
cd /root
git clone <your-repo-url> lift_site
```

### 3. Запуск скрипта деплоя
```bash
cd /root/lift_site
chmod +x deploy.sh
./deploy.sh
```

### 4. Проверка
- Сайт: https://etazhi-lifts.online
- Админка: https://etazhi-lifts.online/admin
- Тест входа с паролем: `Gsm&G0zMhtj*y#1o0XV3`

## Управление после деплоя

```bash
# Статус приложения
systemctl status lift_site

# Перезапуск приложения
systemctl restart lift_site

# Просмотр логов
journalctl -u lift_site -f

# Статус Nginx
systemctl status nginx

# Перезапуск Nginx
systemctl reload nginx

# Проверка SSL
certbot certificates
certbot renew --dry-run
```

## Настройки .env для production
```env
SECRET_KEY=<сильный-случайный-ключ>
ADMIN_PASSWORD=Gsm&G0zMhtj*y#1o0XV3
DESIGN_VARIANT=classic
FLASK_DEBUG=false
```

## Важные замечания
1. Сменить SECRET_KEY на случайный в production
2. Сохранить пароль админки в безопасном месте
3. Настроить автоматическое обновление SSL сертификатов
4. Настроить резервное копирование
