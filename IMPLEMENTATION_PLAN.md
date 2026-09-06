# План внедрения (Implementation Plan)

Проект разбит на стадии (Stages) для поэтапного запуска B2B SaaS платформы SmartRent.

## Стадия 1: Инфраструктура и Базовый Сетап
- [x] Настройка центрального VPS и развертывание MQTT брокера Mosquitto (в Docker, порт 8883, TLS Let's Encrypt).
- [x] Настройка генерации `passwd` и `acl` файлов для обеспечения мультитенантности.
- [x] Инициализация проекта Supabase (PostgreSQL, GoTrue).
- [x] Создание базовых таблиц БД (объекты, пользователи, логи устройств) и настройка RLS-политик.
- [x] Настройка очистки старых логов через `pg_cron` (90 дней).

## Стадия 2: Backend (Python + FastAPI)
- [x] Инициализация структуры проекта через `uv`.
- [x] Настройка CI/CD (GitHub Actions) для проверки кода (Ruff/Pytest).
- [x] Разработка HTTP API для авторизации (интеграция с Supabase) и управления объектами.
- [x] Разработка MQTT-клиента (Worker), слушающего телеметрию из топиков `properties/+/+/+/state` и пишущего историю в БД.
- [x] Реализация бизнес-логики: API-эндпоинт для отправки команд в MQTT-брокер.


## Стадия 4: Frontend (Vue 3 + Vite + Tailwind + PWA)
*(Примечание: выполнена до Стадии 3 по согласованию с пользователем для сквозной валидации UI/UX)*
- [x] Инициализация SPA приложения (Vue 3, TypeScript, Pinia, Vue Router 4).
- [x] Автоматическая кодогенерация типов из SSOT JSON-схем (`npm run codegen:types` via `json-schema-to-typescript`).
- [x] Интеграция с `@supabase/supabase-js` для аутентификации пользователей и управления сессиями.
- [x] Реализация транспорта обновлений: **Supabase Realtime** с паттерном *Fetch-then-Subscribe* (ADR 5).
- [x] Разработка UI компонентов управления устройствами (замок TTLock, реле освещения, кран протечки, кондиционер) с реализацией паттерна `optimistic: false` и таймаутом ожидания ответа (10с).
- [x] Модуль мультиязычности (`vue-i18n`) с поддержкой EN, RU и подготовкой для RTL языков (HE).
- [x] Панель Супер-Администратора (`/admin`): системный мониторинг, создание тестовых пользователей в 1 клик и автоматическое сидирование объектов с IoT-устройствами.
- [x] Поддержка PWA (`vite-plugin-pwa`, веб-манифест, Service Worker, адаптивный mobile-first дизайн).
- [x] Разработка скрипта эмулятора Edge-узла (`scripts/dev_edge_emulator.py`) для локального тестирования.
- [x] 100% покрытие frontend юнит-тестами (Vitest), линтинг ESLint 9 и сборка Vite.

## Стадия 3: Edge Node (Home Assistant OS)
- [ ] Создание эталонного `configuration.yaml` с подключением к удаленному MQTT.
- [ ] Разработка HA Automations (мостов) для смарт-замков TTLock.
- [ ] Разработка HA Automations для датчиков протечки и приводов перекрытия воды (с приоритетом на локальное выполнение).
- [ ] Разработка HA Automations для управления AC (кондиционерами).

## Стадия 5: Тестирование и Запуск
- [ ] Проведение E2E тестов.
- [x] Контейнеризация Backend: `backend/Dockerfile` (multi-stage, uv, python:3.14-slim, непривилегированный пользователь, healthcheck).
- [x] Контейнеризация Frontend: `frontend/Dockerfile` (multi-stage, node:24-alpine build с codegen → nginx:1-alpine с SPA-роутингом).
- [x] Продакшен-оркестрация: `docker-compose.prod.yml` (backend, mosquitto go-auth, frontend, nginx reverse-proxy, certbot DNS-challenge).
- [x] Продакшен-конфигурации: `deploy/nginx/nginx.conf` (HTTPS, SPA + /api/ reverse proxy), `deploy/mosquitto/mosquitto.prod.conf` (вебхуки → backend:8000 по Docker DNS).
- [x] CI/CD Pipeline: расширение GitHub Actions — сборка Docker-образов → GHCR, автоматический деплой на VPS по SSH после пуша в `main`.
- [x] Документация деплоя: `deploy/README.md` (первоначальная настройка VPS, GitHub Secrets, подключение HAOS, диагностика).
- [ ] Первоначальная настройка VPS: файрвол, swap, Docker, SSH-ключ для CD, сертификаты Let's Encrypt (ручной шаг).
- [ ] Настройка GitHub Secrets и первый запуск CD-пайплайна.
- [ ] Создание MQTT-учётных данных для HAOS в таблице `mqtt_credentials` (Supabase Studio).
- [ ] Переподключение HAOS к продакшен-брокеру (mosquitto-go-auth) и проверка сквозного пути: UI → API → MQTT → HAOS → state → UI.
- [ ] Альфа-тестирование системы с реальным пользователем.
