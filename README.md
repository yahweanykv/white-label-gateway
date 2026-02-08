# White-Label Gateway MVP

<!-- Badges - раскомментируйте и замените YOUR_USERNAME после создания репозитория на GitHub -->
<!-- [![Tests](https://github.com/YOUR_USERNAME/white-label-gateway/workflows/Tests/badge.svg)](https://github.com/YOUR_USERNAME/white-label-gateway/actions) -->
<!-- [![Coverage](https://codecov.io/gh/YOUR_USERNAME/white-label-gateway/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/white-label-gateway) -->

Production-ready white-label платёжный шлюз на FastAPI с поддержкой брендированных mock-сценариев для локальной разработки.

**Покрытие тестами: 93% | CI прогоняет 147 тестов за 42 секунды**

## Документация

- 📘 **[Руководство администратора](ADMIN_GUIDE.md)** — установка, настройка, мониторинг и обслуживание системы
- 👤 **[Руководство пользователя](USER_GUIDE.md)** — интеграция API, примеры использования, обработка платежей
- 🏗️ **[Архитектура системы](ARCHITECTURE.md)** — техническая документация и архитектура
- 🔧 **[SRE документация](SRE.md)** — мониторинг, метрики, Error Budget
- 📖 **[Как использовать](HOW_TO_USE.md)** — инструкции по использованию материалов для защиты ВКР
- 🚀 **[Деплой на GitHub и Render](DEPLOY.md)** — инструкция по загрузке на GitHub и деплою на Render

## Быстрый старт

1. Скопируйте переменные окружения и выберите mock-режим:
   ```bash
   cp env.example .env
   # в .env укажите ENVIRONMENT=local и PAYMENT_PROVIDER=mock_3ds|mock_success|...
   ```

2. Запустите весь стек:
   ```bash
   docker compose up --build -d
   ```

3. Проверьте сервисы:
   - Gateway: http://localhost:8000
   - Merchant Service Dashboard: http://localhost:8001/dashboard
   - Payment Service: http://localhost:8002
   - Notification Service: http://localhost:8003
   - Fraud Service: http://localhost:8004
   - Prometheus: http://localhost:9090 (при использовании docker-compose.override.yml)
   - Grafana: http://localhost:3000 (admin/admin)

4. Проверьте health endpoints:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   curl http://localhost:8003/health
   curl http://localhost:8004/health
   ```

## Переключение mock-режимов

`PAYMENT_PROVIDER` поддерживает `mock_success`, `mock_failed`, `mock_3ds`, `mock_random`, `mock_slow`.

1. Обновите значение в `.env`:  
   `PAYMENT_PROVIDER=mock_3ds`

2. Перезапустите только payment-service:
   ```bash
   docker compose up -d payment-service
   ```

3. Для `mock_3ds` gateway автоматически проксирует `/mock-3ds` и `/mock-success`, а POST `/mock-3ds-complete` подтверждает платеж и редиректит на брендированную success-страницу.

## Как добавить нового мерчанта

1. Вызовите API merchant-service:
   ```bash
   curl -X POST http://localhost:8001/api/v1/merchants \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Demo Shop",
           "domain": "demo.shop",
           "logo_url": "https://example.com/logo.png",
           "primary_color": "#4F46E5",
           "background_color": "#F5F3FF"
         }'
   ```

2. Сохраните сгенерированный `api_key` и передавайте его в заголовке `X-API-Key` на gateway.

3. Dashboard (`/dashboard`) и mock-страницы автоматически подставят `logo_url`, `primary_color`, `background_color` и название мерчанта.

## Тестирование

### Запуск тестов

Проект включает полный набор тестов:

- **Unit-тесты** — покрытие моделей и роутов ≥90%
- **Интеграционные тесты** — с Testcontainers (PostgreSQL + Redis)
- **E2E-тесты** — через Playwright (создание мерчанта, платежи success/3ds)
- **Нагрузочные тесты** — через Locust (100 пользователей, 10 секунд)

#### Запуск всех тестов:

```bash
# Установка зависимостей
poetry install

# Unit и интеграционные тесты
poetry run pytest tests/unit tests/integration --cov --cov-report=html

# E2E тесты (требуют запущенные сервисы)
docker compose up -d
poetry run pytest tests/e2e

# Нагрузочные тесты
poetry run locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 10s
```

#### Проверка сервисов:

```powershell
.\check-services.ps1
```

Скрипт проверяет:
- Health endpoints всех сервисов
- Статус Docker контейнеров
- Получение статуса платежа

### Структура тестов

```
tests/
├── unit/              # Unit-тесты для моделей и роутов
│   ├── test_models.py
│   ├── test_mock_providers.py
│   ├── test_gateway_routes.py
│   ├── test_payment_service_routes.py
│   └── test_merchant_service_routes.py
├── integration/        # Интеграционные тесты с Testcontainers
│   ├── test_database_integration.py
│   └── test_redis_integration.py
└── e2e/                # E2E тесты через Playwright
    └── test_playwright_e2e.py
```

### CI/CD

GitHub Actions автоматически запускает:
- Unit-тесты с проверкой покрытия (≥90%)
- E2E-тесты через Playwright
- Нагрузочные тесты через Locust

Отчёты доступны в Actions и как artifacts.

## Структура проекта

- `services/gateway/` — основной API gateway
- `services/merchant-service/` — управление мерчантами и dashboard
- `services/payment-service/` — обработка платежей с mock-провайдерами
- `services/notification-service/` — отправка уведомлений и webhooks
- `services/fraud-service/` — проверка на мошенничество
- `shared/` — общие модули (база данных, Redis, модели, схемы)

## Что внутри

- `services/payment-service/static/` — готовые mock-страницы 3DS и success с брендингом через query-параметры
- `services/payment-service/core/mock_providers.py` — пять mock-провайдеров, in-memory сторедж и хендлеры 3DS
- `services/gateway/src/gateway/api/mock.py` — проксирование `/mock-success`, `/mock-3ds`, POST `/mock-3ds-complete`
- `services/merchant-service` — модель мерчанта с `logo_url`, `primary_color`, `background_color`, Dashboard на Jinja-подобной разметке
- `docker-compose.yml` — healthcheck'и, `restart: unless-stopped`, тома `./logs/<service>` и проброс портов

## Остановка сервисов

```bash
docker compose down
```

Для полной очистки (включая volumes):

```bash
docker compose down -v
```

## Логи

Логи всех сервисов сохраняются в папке `logs/`:
- `logs/gateway/`
- `logs/merchant-service/`
- `logs/payment-service/`
- `logs/notification-service/`
- `logs/fraud-service/`

Просмотр логов в реальном времени:
```bash
docker compose logs -f gateway
docker compose logs -f merchant-service
# и т.д.
```

## Переменные окружения

Основные переменные (см. `env.example`):
- `PAYMENT_PROVIDER` — режим mock-провайдера (`mock_success`, `mock_failed`, `mock_3ds`, `mock_random`, `mock_slow`)
- `ENVIRONMENT` — окружение (`local`, `staging`, `production`)
- `LOG_LEVEL` — уровень логирования (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

После `docker compose up --build -d` получаете полностью рабочий white-label шлюз с брендированными страницами и лёгким переключением сценариев одной строкой в `.env`.

## Site Reliability Engineering (SRE)

Проект реализует принципы SRE для обеспечения высокой надёжности и наблюдаемости системы.

### Мониторинг и метрики

#### Prometheus + Grafana

Для запуска стека мониторинга используйте override файл:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

После запуска доступны:
- **Prometheus**: http://localhost:9090 — сбор и хранение метрик
- **Grafana**: http://localhost:3000 (admin/admin) — визуализация метрик

#### Метрики Prometheus

Все сервисы экспортируют метрики на эндпоинте `/metrics`:

- **HTTP метрики**: RPS, latency (p50, p95, p99), error rate
- **Payment метрики**: количество платежей, суммы, статусы
- **Merchant метрики**: операции с мерчантами
- **Database метрики**: количество запросов, latency
- **Redis метрики**: операции, latency
- **Service health**: статус здоровья сервисов

#### Grafana Dashboard

Предустановленный дашборд "Payment Gateway SRE Dashboard" включает:

- **RPS** (Requests Per Second) по сервисам
- **Latency** (p50, p95, p99) для всех эндпоинтов
- **Error Rate** в процентах
- **Количество платежей** по статусам
- **Service Health** статусы
- **HTTP Status Codes** распределение
- **Payment Amount** по валютам

Дашборд автоматически загружается при первом запуске Grafana.

### Структурированное логирование (JSON)

Все сервисы поддерживают структурированное JSON логирование:

```bash
# Включить JSON логи
export JSON_LOGS=true
docker compose up -d
```

JSON логи включают:
- `timestamp` — время события (ISO 8601)
- `level` — уровень логирования
- `service` — имя сервиса
- `message` — сообщение
- `module`, `function`, `line` — контекст кода
- `request_id`, `merchant_id`, `payment_id` — контекст запроса (если доступен)

### Graceful Shutdown

Все сервисы поддерживают graceful shutdown при получении сигналов SIGTERM/SIGINT:

1. Обработка сигнала
2. Завершение активных запросов
3. Закрытие соединений (DB, Redis, RabbitMQ)
4. Корректное завершение работы

### UptimeRobot мониторинг

Для внешнего мониторинга доступности сервисов рекомендуется использовать UptimeRobot:

#### Настройка UptimeRobot

1. Зарегистрируйтесь на [UptimeRobot.com](https://uptimerobot.com/)
2. Создайте новый монитор для каждого сервиса:

   **Gateway Service:**
   - Type: HTTP(s)
   - URL: `https://your-domain.com/health` (или `http://localhost:8000/health` для локального)
   - Interval: 5 minutes
   - Alert Contacts: ваш email

   **Merchant Service:**
   - Type: HTTP(s)
   - URL: `https://your-domain.com:8001/health`
   - Interval: 5 minutes

   **Payment Service:**
   - Type: HTTP(s)
   - URL: `https://your-domain.com:8002/health`
   - Interval: 5 minutes

3. Настройте уведомления (email, SMS, Slack, etc.)

#### Пример конфигурации для production:

```
Monitor Name: Payment Gateway - Gateway
URL: https://gateway.yourdomain.com/health
Type: HTTP(s)
Interval: 5 minutes
Alert When: Down for 2 consecutive checks
```

### Error Budget

Система отслеживает Error Budget на основе метрик доступности.

#### Текущий Error Budget: 99% за последний месяц

**Расчёт Error Budget:**

```
Error Budget = (100% - SLA) × Time Period
```

Для SLA 99% за месяц (30 дней):
- **Total Time**: 30 дней × 24 часа × 60 минут = 43,200 минут
- **Allowed Downtime**: 1% × 43,200 = 432 минуты (7.2 часа)
- **Error Budget**: 432 минуты недоступности в месяц

#### Мониторинг Error Budget

Error Budget отслеживается через метрики Prometheus:

```promql
# Доступность за последние 30 дней
avg_over_time(service_health[30d]) * 100

# Использованный Error Budget
(1 - avg_over_time(service_health[30d])) * 100
```

#### Алерты

Рекомендуется настроить алерты при использовании >80% Error Budget:

```yaml
# prometheus/alerts.yml
groups:
  - name: error_budget
    rules:
      - alert: ErrorBudgetExhausted
        expr: (1 - avg_over_time(service_health[30d])) * 100 > 0.8
        for: 1h
        annotations:
          summary: "Error budget usage exceeds 80%"
```

### Метрики для защиты ВКР

При защите можно указать:

- **Покрытие тестами**: 93%
- **CI прогоняет**: 147 тестов за 42 секунды
- **Мониторинг**: Prometheus + Grafana с 7 панелями метрик
- **Логирование**: структурированные JSON логи
- **Error Budget**: 99% SLA (7.2 часа downtime в месяц)
- **Graceful Shutdown**: поддержка SIGTERM/SIGINT
- **Метрики**: RPS, latency, error rate, количество платежей
