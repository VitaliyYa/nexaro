# Changelog

Все важные изменения в проекте **SmartRent** документируются в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

## [Unreleased]

### Added
- **MQTT Broker (Mosquitto & mosquitto-go-auth):**
  - Конфигурация брокера с поддержкой TLS (порт 8883) и WebSockets (порт 9001).
  - Интеграция с плагином `mosquitto-go-auth` для динамической аутентификации и проверки ACL через HTTP Webhook в Backend API.
  - Полное исключение файлов учетных записей `passwd` и `acl` из репозитория.
  - Docker Compose файл для развертывания `iegomez/mosquitto-go-auth`.
  - Скрипт `generate_dev_certs.sh` для локальной генерации тестовых TLS сертификатов.
  - Утилита `manage_acl.py` и юнит-тесты для локального/офлайн тестирования ACL.
- **База данных Supabase (PostgreSQL):**
  - DDL миграция для таблиц `properties`, `devices`, `device_logs`, `mqtt_credentials`, `property_pins`, `audit_logs`.
  - Включение Row Level Security (RLS) на всех таблицах с проверкой владения (`auth.uid()`).
  - Автоматическая очистка логов устройств старше 90 дней через `pg_cron`.
- **Контракты данных (SSOT):**
  - JSON-схемы для MQTT сообщений (`availability`, `lock_state`, `lock_command`, `relay_state`, `relay_command`, `valve_event`, `climate_state`, `climate_command`).
  - JSON-схемы для API сущностей (`property`, `device`, `pin`, `mqtt_auth`).
