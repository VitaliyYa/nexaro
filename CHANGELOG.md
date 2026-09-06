# Changelog

Все важные изменения в проекте **SmartRent** документируются в этом файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

## [Unreleased]

### Added
- **Frontend SPA & PWA (Vue 3, Vite, Tailwind CSS, TypeScript):**
  - Инициализация веб-приложения с Pinia и Vue Router 4.
  - Автоматическая кодогенерация TypeScript интерфейсов из каталога SSOT JSON-схем через `json-schema-to-typescript`.
  - Интеграция с `@supabase/supabase-js` для аутентификации и сессий пользователей.
  - Синхронизация состояний IoT-устройств в реальном времени через **Supabase Realtime** (`postgres_changes` на таблице `devices`) с паттерном *Fetch-then-Subscribe*.
  - Реализация строгого UI-паттерна **`optimistic: false`**: тумблеры и кнопки переходят в `pending/loading` состояние и переключаются только после подтверждения физическим устройством в Realtime (с 10-секундным таймаутом и Toast-уведомлением).
  - Карточки устройств: смарт-замки TTLock (статусы Locked/Unlocked, создание гостевых PIN-кодов с датами начала/окончания и бессрочных PIN-кодов для владельцев/персонала, статусные бейджи), реле освещения (Включено/Выключено), краны перекрытия воды (Открыт/Перекрыт), кондиционеры.
  - Раздел "Журнал событий и аудит": постраничная загрузка единой хроники событий из `device_logs` (телеметрия IoT) и `audit_logs` (команды управления, PIN-коды, безопасность) через REST API `/api/v1/properties/{property_id}/logs`.
  - Мультиязычность (`vue-i18n`) с поддержкой русского (`ru`), английского (`en`) и готовностью к грузинскому (`ka`) и ивриту (`he` с поддержкой `dir="rtl"`).
  - Консоль Супер-Администратора (`/admin`): системный мониторинг, моментальное создание тестовых пользователей без обязательного подтверждения email и генерация тестовых квартир с 4 IoT-устройствами.
  - Поддержка PWA (`vite-plugin-pwa`, Service Worker, веб-манифест, адаптивность для мобильных экранов).
  - Скрипт эмулятора Edge-узла (`scripts/dev_edge_emulator.py`) для сквозного локального тестирования отклика устройств.
  - Юнит-тесты на Vitest для компонентов и Pinia сторов, интеграция в CI пайплайн GitHub Actions.
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
- **Backend API & Worker (Python 3.14 + FastAPI):**
  - Инициализация и конфигурация проекта с использованием менеджера пакетов `uv`.
  - Автоматическая кодогенерация моделей Pydantic v2 из SSOT JSON-схем через `datamodel-code-generator`.
  - Настройка непрерывной интеграции (CI) в GitHub Actions (линтер Ruff и тесты Pytest).
  - Аутентификация через Supabase JWT (поддержка JWKS и симметричных ключей) с пробросом токенов в БД для строгого соблюдения RLS-политик.
  - Изолированный доступ по ключу `service_role` только для фонового воркера и вебхуков Mosquitto.
  - Реализация динамических HTTP Webhook эндпоинтов для `mosquitto-go-auth` (`/auth/mqtt/user`, `/auth/mqtt/superuser`, `/auth/mqtt/acl`) с валидацией прав на топики `properties/<property_id>/...`.
  - Управление объектами (`/properties`) и IoT-устройствами (`/properties/{property_id}/devices`).
  - Управление PIN-кодами смарт-замков (`/properties/{property_id}/locks/{device_id}/pins`) с шифрованием AES (Fernet) at rest, запретом логирования и аудитом в `audit_logs`.
  - Эндпоинты истории телеметрии (`device_logs`) и аудита (`audit_logs`).
  - Фоновый MQTT Worker (`paho-mqtt`) для сбора телеметрии из топиков `state`, `event`, `availability` с валидацией схем и сохранением в БД.
  - Эндпоинт отправки команд устройствам (`/properties/{property_id}/devices/{device_id}/command`) с QoS 1 и `retain: false`.
  - 100% покрытие юнит-тестами (26 тестов в Pytest).

### Changed & Security
- **Унификация переменных окружения (.env):**
  - Удален избыточный дубликат `edge/mosquitto/.env`. Теперь все сервисы (Backend, Mosquitto Docker Compose) используют единый конфигурационный файл `/.env` в корне монорепозитория.
  - Контейнер Mosquitto в `docker-compose.yml` получает учетные данные воркера напрямую через `env_file: ../../.env` без дублирования в блоке `environment`.
- **Устранение захардкоженных секретов и ключей:**
  - Очищены значения по умолчанию для `MQTT_WORKER_PASSWORD` и `PIN_ENCRYPTION_KEY` в `backend/src/config.py`.
  - Удален захардкоженный дефолтный пароль `secret_backend_worker_pass` из `edge/mosquitto/docker-compose.yml`.
  - Добавлена строгая валидация наличия `PIN_ENCRYPTION_KEY` в `pin_crypto.py`.
  - Устранена передача статических паролей и ключей в `backend/tests/conftest.py`, `test_mqtt_auth.py` и `test_auth_jwt.py`; тесты теперь динамически подтягивают актуальные настройки.
  - Добавлена поддержка настройки учетных данных тестового пользователя через `TEST_USER_PASSWORD` / `TEST_USER_EMAIL` в `backend/scripts/get_token.py` и шаблонах `.env.example`.

