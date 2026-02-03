# AOSS → Loki Log Shipper

This directory contains the log shipping infrastructure for sending AOSS execution logs to Grafana Loki.

## 🎯 Overview

The log shipper reads execution logs from the PostgreSQL database via the API and pushes them to Grafana Loki for observability in Grafana.

**Data Flow:**
```
PostgreSQL (execution_logs table)
    ↓
GET /api/monitoring/logs  (read-only API)
    ↓
Log Transformation (to Loki format)
    ↓
POST /loki/api/v1/push  (Loki HTTP API)
    ↓
Grafana Dashboards
```

## 📦 Components

### 1. `log_shipper.py` - Background Service
Automatic background service that ships logs continuously.

**Features:**
- Polls `/api/monitoring/logs` every 30 seconds
- Tracks processed logs to prevent duplicates
- Fails silently if Loki is unavailable
- Auto-starts with FastAPI application

**Usage:**
Already integrated into `main.py` - starts automatically when backend starts.

### 2. `ship_logs_to_loki.py` - Standalone Script ⭐
**Run this script to ship all historical logs immediately.**

**Features:**
- Ships ALL execution logs in one run
- Useful for:
  - Initial setup (backfill historical data)
  - After Loki restarts
  - Manual log shipping
  - Troubleshooting

**Usage:**
```bash
# Basic usage (local development)
python ship_logs_to_loki.py

# For Docker Loki container
python ship_logs_to_loki.py --loki http://loki_tst:3100

# Custom configuration
python ship_logs_to_loki.py \
  --backend http://localhost:8000 \
  --loki http://localhost:3100 \
  --batch-size 1000

# Help
python ship_logs_to_loki.py --help
```

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
LOKI_URL=http://localhost:3100
BACKEND_URL=http://localhost:8000
```

### Loki Endpoints
- **Local development:** `http://localhost:3100`
- **Docker container:** `http://loki_tst:3100`
- **Remote:** `http://<server-ip>:3100`

## 📊 Log Format

### Loki Labels
Each log entry includes these labels for filtering:
```
job="aoss"                    # Constant identifier
server_id="<uuid>"           # Server UUID
server_tag="prod-web-01"     # Human-readable server name
agent_type="network"         # network/database/security/general
status="Success"             # Step status
execution_status="Success"   # Overall execution status
```

### Log Message Format
```
STEP: 1 | COMMAND: systemctl status nginx | EXIT_CODE: 0 | STDOUT: Active: active (running) | STDERR: 
```

## 🔍 Querying Logs in Grafana

Access Grafana at: `http://localhost:3001`

### Example LogQL Queries
```logql
# All AOSS logs
{job="aoss"}

# Logs for specific server
{job="aoss", server_tag="prod-web-01"}

# Failed executions only
{job="aoss", status="Failed"}

# Network agent logs
{job="aoss", agent_type="network"}

# Search for specific command
{job="aoss"} |= "nginx"

# Failed commands with error output
{job="aoss", status="Failed"} |= "STDERR"
```

## 🚀 Quick Start

### First Time Setup
1. **Start Loki:**
   ```bash
   cd backend/monitering
   docker-compose up -d loki_tst
   ```

2. **Verify Loki is running:**
   ```bash
   curl http://localhost:3100/ready
   ```

3. **Ship historical logs:**
   ```bash
   cd backend
   python ship_logs_to_loki.py
   ```

4. **Start backend (auto-ships new logs):**
   ```bash
   uvicorn main:app --reload
   ```

5. **View logs in Grafana:**
   - Open: http://localhost:3001
   - Login: admin/admin
   - Explore → Loki → Query: `{job="aoss"}`

### Daily Operation
Once set up, logs are automatically shipped as executions happen. The background service runs continuously.

### Manual Log Shipping
Run anytime to ship all logs:
```bash
python ship_logs_to_loki.py
```

## 🔒 Key Features

✅ **Read-Only:** Never modifies execution_logs table  
✅ **Non-Blocking:** Background thread doesn't block requests  
✅ **Deduplication:** Tracks processed logs to prevent duplicates  
✅ **Fail-Safe:** Silently handles Loki unavailability  
✅ **Production-Ready:** Thread-safe with proper locking  
✅ **Docker-Friendly:** Works with containerized Loki  

## 📝 Notes

- Logs are fetched via the existing `/api/monitoring/logs` endpoint
- No new database queries or schema changes required
- Works with existing execution_logs table structure
- Timestamps converted to nanoseconds (Loki requirement)
- Output truncated to 300 chars for readability
- Memory-efficient deduplication (max 10k entries)

## 🐛 Troubleshooting

### No logs in Grafana
```bash
# 1. Check if logs were shipped
python ship_logs_to_loki.py

# 2. Verify Loki has logs
curl "http://localhost:3100/loki/api/v1/labels"

# 3. Check backend API
curl http://localhost:8000/api/monitoring/logs
```

### Loki connection errors
```bash
# Check Loki is running
docker ps | grep loki

# Check Loki logs
docker logs loki_tst

# Restart Loki
docker-compose restart loki_tst
```

### Duplicate logs
The shipper tracks processed logs in memory. If you restart the backend, it will re-ship logs. This is safe - Loki handles duplicates gracefully.

## 🎯 Architecture Decisions

1. **Why API instead of direct DB access?**
   - Respects separation of concerns
   - No direct DB dependencies
   - Works with any backend implementation
   - Can ship from remote backends

2. **Why separate standalone script?**
   - Backfill historical logs without restarting backend
   - Manual troubleshooting
   - Scheduled batch jobs via cron
   - Works even if backend is down

3. **Why in-memory deduplication?**
   - No DB writes (read-only requirement)
   - Fast and simple
   - Acceptable for restarts (Loki handles duplicates)
