# Changelog

Все важные изменения в проекте **SmartRent** документируются в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

## [Unreleased]

### Added
- **MQTT Broker (Mosquitto):**
  - Конфигурация брокера с поддержкой TLS (порт 8883) и WebSockets (порт 9001).
  - Docker Compose файл для развертывания Mosquitto.
  - Утилита `manage_acl.py` для динамической генерации паролей (`passwd`) и правил разграничения доступа (`acl`) с изоляцией топиков по тенантам (`properties/<property_id>/#`).
  - Скрипт `generate_dev_certs.sh` для локальной генерации тестовых TLS сертификатов.
  - Набор unit-тестов для управления ACL и валидации правил безопасности.
- **База данных Supabase (PostgreSQL):**
  - DDL миграция для таблиц `properties`, `devices`, `device_logs`, `property_pins`, `audit_logs`.
  - Включение Row Level Security (RLS) и настройка политик мультитенантности по владельцу (`auth.uid()`).
  - Автоматическая очистка логов устройств старше 90 дней через `pg_cron`.
- **Контракты данных (SSOT):**
  - JSON-схемы для MQTT сообщений (`availability`, `lock_state`, `lock_command`, `relay_state`, `relay_command`, `valve_event`, `climate_state`, `climate_command`).
  - JSON-схемы для API сущностей (`property`, `device`, `pin`).
