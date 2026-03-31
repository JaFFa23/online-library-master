# Online Library1

**Client–server system:** FastAPI API + PostgreSQL + Telegram Bot (aiogram 3)

## Official run mode (this repository)

* **Docker:** API + DB + pgAdmin + DB_test + Telegram Bot

---

## Table of contents

* [Requirements](#requirements)
* [Project structure](#project-structure)
* [Quick start](#quick-start)
* [Migrations (Alembic)](#migrations-alembic)
* [Run API locally from PyCharm (optional)](#run-api-locally-from-pycharm-optional)
* [Create user and make admin (CLI)](#create-user-and-make-admin-cli)
* [Run tests (pytest)](#run-tests-pytest)
* [Check export.csv](#check-exportcsv)
* [Run Telegram Bot](#run-telegram-bot)
* [Troubleshooting](#troubleshooting)

---

## Requirements

* Docker Desktop
* Python **3.11** (local debug/CLI/pytest)

---

## Project structure

```text
backend/         FastAPI app + Alembic migrations
bot/             aiogram 3 bot
infra/           docker-compose files
```

---

## Quick start

### 1) Start the Docker stack (DB + API + pgAdmin + DB_test + Bot)

From repository root:

```powershell
cd A:\online-library
docker compose -f .\infra\docker-compose.stack.yml up -d --build
```

### 2) Check services

* API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* pgAdmin: [http://127.0.0.1:5050](http://127.0.0.1:5050)

Logs:

```powershell
docker compose -f .\infra\docker-compose.stack.yml logs -f api
docker compose -f .\infra\docker-compose.stack.yml logs -f bot
```

Stop:

```powershell
docker compose -f .\infra\docker-compose.stack.yml down
```

---

## Migrations (Alembic)

Apply migrations in Docker:

```powershell
docker compose -f .\infra\docker-compose.stack.yml exec api alembic upgrade head
```

Create migration (autogenerate):

```powershell
docker compose -f .\infra\docker-compose.stack.yml exec api alembic revision --autogenerate -m "my_migration"
```

---

## Run API locally from PyCharm (optional)

Use this when you need debugging in PyCharm, while DB stays in Docker.

### Option A (recommended): stop API container and run local API on port 8000

```powershell
cd A:\online-library
docker compose -f .\infra\docker-compose.stack.yml stop api
```

Local API must connect to DB via `127.0.0.1:5432`, so in your local env:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/online_library
```

---

## Create user and make admin (CLI)

### Create user (official way)

* Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) → `POST /api/v1/auth/register`

### Make user admin (CLI)

CLI module: `python -m app.cli`

In Docker:

```powershell
docker compose -f .\infra\docker-compose.stack.yml exec api `
  python -m app.cli set-role --email admin@example.com --role admin
```

Local:

```powershell
cd A:\online-library\backend\src
python -m app.cli set-role --email admin@example.com --role admin
```

---

## Run tests (pytest)

Test DB (`db_test`) is available on **localhost:5433**.

Ensure it is running:

```powershell
cd A:\online-library
docker compose -f .\infra\docker-compose.stack.yml up -d db_test
```

Run tests locally:

```powershell
cd A:\online-library\backend
pytest -q
```

Optional override (if supported in your tests):

```powershell
$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/online_library_test"
pytest -q
```

---

## Check export.csv

Admin-only endpoint:  
`GET /api/v1/admin/books/export.csv`

Steps:

1. Register user
2. Make user admin (CLI)
3. Login → get JWT token
4. Download CSV:

```powershell
curl.exe -L -o books.csv `
  -H "Authorization: Bearer <JWT_TOKEN>" `
  "http://127.0.0.1:8000/api/v1/admin/books/export.csv"
```

Check:

```powershell
type .\books.csv
```

---

## Run Telegram Bot

### Docker (official mode)

1. Fill `bot/.env`:

```env
BOT_TOKEN=PASTE_YOUR_TOKEN_HERE
```

2. Restart bot:

```powershell
cd A:\online-library
docker compose -f .\infra\docker-compose.stack.yml restart bot
docker compose -f .\infra\docker-compose.stack.yml logs -f bot
```

Note: inside Docker bot uses internal API base URL configured in compose (`http://api:8000/api/v1`).

---

## Troubleshooting

### Alembic / migrations

Apply manually:

```powershell
docker compose -f .\infra\docker-compose.stack.yml exec api alembic upgrade head
```

### Port already in use (8000 / 5432 / 5050 / 5433)

Check who uses a port:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Env / pydantic-settings validation errors

* verify variable names in `.env`
* recommended: `extra="ignore"` in Settings models
* remember: Docker DB host is `db`, local host is `127.0.0.1`

### Docker build error: “parent snapshot … does not exist”

Clear build cache and rebuild:

```powershell
docker buildx prune -a -f
docker builder prune -a -f
docker compose -f .\infra\docker-compose.stack.yml build --no-cache
```

---

## Recommended PyCharm Run Configurations

1. **Docker Compose: Up (stack)**

* Compose file: `infra/docker-compose.stack.yml`
* Command: `up -d --build`

2. **Docker Compose: Down (stack)**

* Compose file: `infra/docker-compose.stack.yml`
* Command: `down`

3. **API (local) — Uvicorn**

* Module: `uvicorn`
* Params: `app.main:app --reload --host 127.0.0.1 --port 8000`
* Working dir: `backend/src`
* Env file: `backend/.env` (or `.env.local`)

4. **Alembic upgrade head (local)**

* Module: `alembic`
* Params: `upgrade head`
* Working dir: `backend`
* Env file: `backend/.env`

5. **CLI set-role admin (local)**

* Module: `app.cli`
* Params: `set-role --email admin@example.com --role admin`
* Working dir: `backend/src`
* Env file: `backend/.env`

6. **Pytest (backend)**

* Target: `backend`
* Args: `-q`
* Optional env: `TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/online_library_test`

7. **Bot (local, optional)**

* Module: `bot_app`
* Working dir: `bot/src`
* Env file: `bot/.env`
