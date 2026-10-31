# Сервис трансфера

REST-сервис на FastAPI для расчёта стоимости трансфера и получения данных о бронировании. Асинхронное общение и функционал бронирования и отмены пока не реализованы.

## Запуск через Docker Compose

```powershell
docker compose up --build
```

API будет доступно по адресу <http://localhost:8000>, автоматическая документация - <http://localhost:8000/docs>. PostgreSQL доступен на порту `5432`.

При первом запуске пустой базы создаются таблицы и демонстрационные данные: область вокруг центра Москвы радиусом 100 км, тарифы `Premium` и `VIP` и цены для них. 
SQL-скрипты из `db/init` выполняются только при первом создании тома базы данных. При последующих запусках данные сохраняются.

Для пременения init данных повторно использовать:

```powershell
docker compose exec -T postgres sh -c "psql -U transfer -d transfer -f /docker-entrypoint-initdb.d/001_schema.sql && psql -U transfer -d transfer -f /docker-entrypoint-initdb.d/002_seed.sql"
```

Переменные подключения и валюта задаются в `.env`; пример настроек - в `.env.example`.