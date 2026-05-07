# Docker (Local Demo)

This repo supports a **Docker-only** local demo using Docker Compose.

## Prerequisites

- Docker Desktop installed and running

## Run

From the repo root:

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/docs`

## Stop

```bash
docker compose down
```

## Reset local data (uploads + SQLite DB)

The backend stores SQLite + uploads in a named Docker volume (`backend_data`).

```bash
docker compose down -v
```

## Notes

- The frontend runs the Vite dev server inside the container and proxies `/api/*` to the backend service.
- ML dependencies (PyTorch/Transformers) are **optional** for Docker builds. By default, the backend image installs a fast “base” set of deps and the app falls back to heuristic analysis.

## Optional: build with ML dependencies

If you want the backend container to include PyTorch/Transformers:

```bash
docker compose build --build-arg INSTALL_ML=1 backend
docker compose up
```

