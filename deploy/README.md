# Развёртывание SmartRent на VPS

Инструкция по первоначальной настройке VPS и последующим автоматическим деплоям.

## Архитектура

```
┌──────────────────── VPS (Ubuntu 24.04) ─────────────────────┐
│                                                              │
│  ┌─────────┐    ┌──────────┐    ┌────────────────────────┐  │
│  │ nginx   │    │ backend  │    │      mosquitto         │  │
│  │ :80/443 │──→ │ :8000    │←── │ (go-auth → backend)    │  │
│  │ (proxy) │    │ (FastAPI) │    │ :8883 (MQTTS)          │  │
│  └────┬────┘    └──────────┘    └───────────┬────────────┘  │
│       │                                      │               │
│  ┌────┴────┐                                │               │
│  │frontend │                                │               │
│  │ (SPA)   │                                │               │
│  └─────────┘                                │               │
│                                              │               │
│  ┌──────────┐                               │               │
│  │ certbot  │ (DNS challenge, Cloudflare)    │               │
│  └──────────┘                               │               │
└──────────────────────────────────────────────┼───────────────┘
                                               │
                                    ┌──────────┴──────────┐
                                    │ HAOS (Edge-узел)    │
                                    │ (исходящее MQTTS)   │
                                    └─────────────────────┘
```

## Шаг 0. Первоначальная подготовка VPS (одноразово)

### 0.1. Базовая настройка

```bash
# Файрвол
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8883/tcp
sudo ufw enable

# Swap (обязательно при ≤ 2 GB RAM)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Перелогиниться по SSH
```

### 0.2. Каталог для деплоя

```bash
mkdir -p ~/smartrent/deploy/{nginx,mosquitto,certbot}
```

### 0.3. Первоначальные TLS-сертификаты

Перед первым запуском контейнеров нужно получить сертификаты. Создайте `cloudflare.ini`:

```bash
cat > ~/smartrent/deploy/certbot/cloudflare.ini << 'EOF'
dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN
EOF
chmod 600 ~/smartrent/deploy/certbot/cloudflare.ini
```

Получите сертификаты для обоих доменов:

```bash
docker run --rm \
  -v ~/smartrent/certbot-certs:/etc/letsencrypt \
  -v ~/smartrent/deploy/certbot/cloudflare.ini:/etc/letsencrypt/cloudflare.ini:ro \
  certbot/dns-cloudflare certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 30 \
  -d app.example.com \
  -d mqtt.example.com \
  --agree-tos \
  --email your@email.com \
  --non-interactive
```

**Важно**: замените домены и email на реальные.

### 0.4. SSH-ключ для GitHub Actions

На VPS создайте отдельный SSH-ключ для CD:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy  # Скопируйте в GitHub Secret VPS_SSH_KEY
```

### 0.5. Удаление старого Mosquitto

Если на VPS ещё работает тестовый Mosquitto (`eclipse-mosquitto:2`):

```bash
cd ~/mosquitto  # или где он был развёрнут
docker compose down -v  # -v удалит тома (тестовые данные)
cd ~ && rm -rf ~/mosquitto
```

## Шаг 1. Настройка GitHub Secrets

В репозитории: **Settings → Secrets and variables → Actions → New repository secret**

### Обязательные секреты

| Secret | Описание | Пример |
|---|---|---|
| `VPS_HOST` | IP или домен VPS | `123.45.67.89` |
| `VPS_USER` | SSH-пользователь | `asst` |
| `VPS_SSH_KEY` | Приватный SSH-ключ (ed25519) | содержимое `~/.ssh/github_deploy` |
| `APP_DOMAIN` | Домен для веб-приложения | `app.example.com` |
| `MQTT_CERT_DOMAIN` | Домен для MQTT-брокера | `mqtt.example.com` |
| `MQTT_BROKER_HOST` | Домен MQTT для backend worker | `mqtt.example.com` |
| `MQTT_WORKER_PASSWORD` | Пароль backend_worker | сгенерировать: `openssl rand -base64 32` |
| `SUPABASE_URL` | URL Supabase проекта | `https://xyz.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | Anon Key Supabase | из Supabase Dashboard |
| `SUPABASE_SECRET_KEY` | Service Role Key Supabase | из Supabase Dashboard |
| `SUPABASE_JWKS_URL` | JWKS URL для JWT | `https://xyz.supabase.co/auth/v1/.well-known/jwks.json` |
| `VITE_SUPABASE_URL` | URL Supabase (для frontend) | `https://xyz.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Anon Key (для frontend) | из Supabase Dashboard |
| `PIN_ENCRYPTION_KEY` | Fernet ключ шифрования PIN | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CORS_ORIGINS` | Разрешённые CORS домены | `["https://app.example.com"]` |
| `CLOUDFLARE_API_TOKEN` | API-токен Cloudflare (DNS:Edit) | из Cloudflare Dashboard |

### Создание environment

Также создайте **Environment** `production` в Settings → Environments. Job `deploy` привязан к этому environment, что позволяет добавить protection rules (например, manual approval).

## Шаг 2. Запуск деплоя

После настройки секретов — пуш в `main` автоматически запустит:
1. CI: линтеры и тесты (backend + frontend)
2. Сборка Docker-образов → push в GHCR
3. Деплой: SSH → VPS, генерация `.env`, docker compose pull + up

Мониторинг: **Actions** вкладка в GitHub.

## Шаг 3. Подключение HAOS к продакшен-брокеру

### 3.1. Создание MQTT-учётных данных

В **Supabase Studio** → таблица `mqtt_credentials` → Insert Row:

```json
{
  "username": "haos_property_<uuid>",
  "password_hash": "<PBKDF2-SHA512 hash>",
  "property_id": "<uuid объекта из таблицы properties>",
  "is_active": true
}
```

Для генерации хэша пароля используйте `manage_acl.py`:

```bash
cd edge/mosquitto
python manage_acl.py hash-password "your_secure_password"
```

### 3.2. Настройка MQTT в HAOS

Settings → Devices & Services → MQTT:
- Broker: `mqtt.example.com` (ваш MQTT-домен)
- Port: `8883`
- TLS: включить
- Username: `haos_property_<uuid>` (из шага 3.1)
- Password: пароль (не хэш!)

### 3.3. Проверка

Developer Tools → MQTT → Publish:
- Topic: `properties/<property_id>/relay/test/state`
- Payload: `{"state": "ON"}`

Должно отразиться в логах backend:
```bash
ssh <vps> 'cd ~/smartrent && docker compose -f docker-compose.prod.yml logs backend --tail 20'
```

## Полезные команды диагностики

```bash
# Статус контейнеров
docker compose -f docker-compose.prod.yml ps

# Логи конкретного сервиса
docker compose -f docker-compose.prod.yml logs backend --tail 50 -f
docker compose -f docker-compose.prod.yml logs mosquitto --tail 50 -f
docker compose -f docker-compose.prod.yml logs nginx --tail 50 -f

# Healthcheck
curl -sf https://app.example.com/health | jq

# Перезапуск одного сервиса
docker compose -f docker-compose.prod.yml restart backend

# Полный перезапуск
docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d

# Принудительное обновление сертификатов
docker compose -f docker-compose.prod.yml exec certbot certbot renew --force-renewal

# Проверка MQTT снаружи
mosquitto_sub -h mqtt.example.com -p 8883 --capath /etc/ssl/certs \
  -u "haos_property_xxx" -P "password" -t "properties/xxx/#" -v
```
