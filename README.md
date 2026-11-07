# Сервис трансфера

Сервис трансферов на FastAPI. REST API рассчитывает стоимость и показывает бронирования; фоновый Kafka worker принимает команды на бронирование и отмену и публикует результаты.

## Kafka

Worker по умолчанию включен. Перед запуском укажите в `.env` адрес внешнего Kafka кластера в `KAFKA_BOOTSTRAP_SERVERS` (например, `broker.example.com:9092`). Для кластера с SASL задайте `KAFKA_SECURITY_PROTOCOL=SASL_SSL`, `KAFKA_SASL_MECHANISM`, `KAFKA_SASL_USERNAME` и `KAFKA_SASL_PASSWORD`. Названия топиков и consumer group также настраиваются через `.env`; полный список есть в `.env.example`. Если Kafka пока недоступна, задайте `KAFKA_ENABLED=false`.

Входящие топики `transfer.booking` и `transfer.booking.cancel`; исходящие `transfer.booking-status` и `transfer.cancellation-result`. Успешное бронирование сразу получает статус `CONFIRMED`. Повтор команды с тем же `compositeBookingId` не создаёт новое бронирование. Некорректные сообщения журналируются и подтверждаются, ошибки обработки/публикации оставляются Kafka для повторной доставки.

## Запуск через Docker Compose

```powershell
docker compose up --build
```

API будет доступно по адресу <http://localhost:8000>, автоматическая документация - <http://localhost:8000/docs>. PostgreSQL доступен на порту `5432`.

При первом запуске пустой базы создаются таблицы и демонстрационные данные: зоны покрытия вокруг 8 городов (Москва, Санкт-Петербург, Сочи, Казань, Новосибирск, Калининград, Екатеринбург), тарифы `Economy` и `Business` и цены для них. 
SQL-скрипты из `db/init` выполняются только при первом создании тома базы данных. При последующих запусках данные сохраняются.

Для пременения init данных повторно использовать:

```powershell
docker compose exec -T postgres sh -c "psql -U transfer -d transfer -f /docker-entrypoint-initdb.d/001_schema.sql && psql -U transfer -d transfer -f /docker-entrypoint-initdb.d/002_seed.sql"
```

Переменные подключения к БД, Kafka и валюта задаются в `.env`; пример настроек - в `.env.example`.

Пакеты `app.api`, `app.core`, `app.db`, `app.messaging` и `app.services` разделяют HTTP-схемы, конфигурацию, доступ к данным, Kafka и бизнес-логику.
