# Database

The app runs on **PostgreSQL** (SQLite has been removed). Persistence is plain
SQLAlchemy + `Base.metadata.create_all()`, and LangGraph pause/resume state is
persisted with the **PostgresSaver** checkpointer.

## Connection
Set via `DB_URL` (env / `config/.env.dev`):
```
# Docker Compose (backend → postgres service)
DB_URL=postgresql+psycopg2://aipp:aipp@postgres:5432/aipp

# Local (non-Docker) run
DB_URL=postgresql+psycopg2://aipp:aipp@localhost:5432/aipp
```
The default in `core/config.py` points at `localhost:5432`. **PostgreSQL must be
running** before the backend starts — on boot it runs `create_tables()` (schema
+ idempotent migrations + admin seed) and the pipeline opens a PostgresSaver.

## Required packages (in requirements.txt)
```
psycopg2-binary                 # PostgreSQL driver
langgraph-checkpoint-postgres   # PostgresSaver (pause/resume on Postgres)
```

## Run Postgres

### Option A — Docker Compose (recommended)
`docker-compose.yml` includes a `postgres:16` service (db `aipp`, user/pass
`aipp`/`aipp`) with a healthcheck; the backend waits for it to be healthy.
```
docker compose up -d postgres backend frontend
```

### Option B — Local dev without Docker (pgserver)
A user-space PostgreSQL, no admin/Docker:
```
pip install pgserver
python -c "import pgserver,pathlib;s=pgserver.get_server(str(pathlib.Path.home()/'aipp_pgdata'));print(s.get_uri())"
# set DB_URL to the printed host:port, e.g.:
#   DB_URL=postgresql+psycopg2://postgres@127.0.0.1:<port>/postgres
```

### Option C — Native PostgreSQL
Install PostgreSQL 16, create the db/role:
```
createdb aipp && psql -c "CREATE USER aipp WITH PASSWORD 'aipp'; GRANT ALL ON DATABASE aipp TO aipp;"
```

## How it works
- `core/database.py` builds a PostgreSQL engine with `pool_pre_ping=True`.
- `create_tables()` builds the full schema (19 tables) via `create_all()`, then
  runs idempotent column/table migrations (one statement per transaction, so an
  expected "already exists" doesn't abort the batch), then seeds the admin user.
- `graph/pipeline.py` `_build_checkpointer()` uses **PostgresSaver** (falls back
  to in-memory only if `langgraph-checkpoint-postgres` is missing — scans run
  but pause/resume won't survive a restart).
- Guardian pre-flight runs a real `SELECT 1` connectivity check.

## Notes
- Unit tests (`backend/test_*.py`) use a throwaway in-memory SQLite engine via
  Python's stdlib `sqlite3` purely for fast, isolated fixtures — this does not
  affect the application database, which is PostgreSQL only.
- Concurrency: PostgreSQL supports concurrent multi-user scans / horizontal
  scaling (the previous SQLite single-writer limitation is gone).
