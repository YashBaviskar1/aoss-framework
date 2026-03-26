# AOSS Backend Setup — Demo-Ready Guide

The backend is a **FastAPI** application that depends on **PostgreSQL** (user/server data), **Neo4j** (compliance graph), and **Prometheus + Grafana** (monitoring). All infrastructure runs in Docker containers.

## User Review Required

> [!IMPORTANT]
> **Docker Desktop is NOT installed** on this machine. You need to install it first. All DB services run in Docker.

> [!WARNING]
> The [.env](file:///d:/Projects/aoss-framework/backend/.env) file contains a Groq API key. Please verify it is still valid — keys can expire. If the demo needs live LLM features (agent planning/execution), a working key is required.

> [!CAUTION]
> The [requirements.txt](file:///d:/Projects/aoss-framework/backend/requirements.txt) has a typo: `boto3n-dotenv` should be `boto3`. I will fix this.

---

## Proposed Changes

### Fix requirements.txt typo

#### [MODIFY] [requirements.txt](file:///d:/Projects/aoss-framework/backend/requirements.txt)
- Change `boto3n-dotenv` → `boto3` (line 11). `python-dotenv` is already on line 7.

---

### Add Neo4j to docker-compose.yml

#### [MODIFY] [docker-compose.yml](file:///d:/Projects/aoss-framework/backend/docker-compose.yml)
- Add a `neo4j` service with image `neo4j:5`, port `7474` (browser) and `7687` (bolt), password `admin1234` (matching [graph_connector.py](file:///d:/Projects/aoss-framework/backend/compliance/graph_connector.py) defaults), and a persistent volume.
- Add `execution_logs` table support — the init SQL is missing this table but it's defined in [models.py](file:///d:/Projects/aoss-framework/backend/models.py). SQLAlchemy's `create_all` handles it, but we should add it to init SQL for completeness.

---

### Add Neo4j + Groq env vars to .env

#### [MODIFY] [.env](file:///d:/Projects/aoss-framework/backend/.env)
- Add `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` to match defaults in [graph_connector.py](file:///d:/Projects/aoss-framework/backend/compliance/graph_connector.py).

---

### Add missing `server_metadata` column to init SQL

#### [MODIFY] [001_init.sql](file:///d:/Projects/aoss-framework/backend/db/init/001_init.sql)
- Add `server_metadata JSONB DEFAULT '{}'` to the `servers` table (exists in model but missing from SQL).
- Add `execution_logs` table (exists in model but missing from SQL).

---

## Step-by-Step Startup Commands

After Docker Desktop is installed, run these commands in order:

### Step 1: Start all Docker services
```powershell
cd d:\Projects\aoss-framework\backend
docker compose up -d
```

### Step 2: Start monitoring stack
```powershell
cd d:\Projects\aoss-framework\backend\monitering
docker compose up -d
```

### Step 3: Install Python dependencies
```powershell
cd d:\Projects\aoss-framework\backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Start the FastAPI backend
```powershell
cd d:\Projects\aoss-framework\backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Step 5: Seed compliance rules (once backend is running)
```powershell
curl -X POST http://localhost:8000/api/compliance/seed
```

---

## Services & Ports Summary

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| **FastAPI** | 8000 | http://localhost:8000 | — |
| **PostgreSQL** | 5432 | — | `aoss_user` / `aoss_password` |
| **pgAdmin** | 5050 | http://localhost:5050 | `admin@example.com` / `admin` |
| **Neo4j Browser** | 7474 | http://localhost:7474 | `neo4j` / `admin1234` |
| **Prometheus** | 9091 | http://localhost:9091 | — |
| **Grafana** | 3001 | http://localhost:3001 | `admin` / `admin` |
| **Node Exporter** | 9101 | http://localhost:9101/metrics | — |

---

## Verification Plan

### Automated Tests
1. `curl http://localhost:8000/` — should return `{"message": "AOSS Framework Backend API"}`
2. `curl http://localhost:8000/api/compliance/health` — should return `{"status": "connected", "database": "neo4j"}`
3. `curl -X POST http://localhost:8000/api/compliance/seed` — should seed 5 rules
4. `curl http://localhost:8000/api/compliance/rules` — should return seeded rules

### Manual Verification
1. Open http://localhost:5050 → pgAdmin should load
2. Open http://localhost:7474 → Neo4j Browser should load, run `:server status`
3. Open http://localhost:3001 → Grafana should load with the AOSS dashboard
4. Open your frontend (http://localhost:5173) → Should connect to backend without CORS errors
