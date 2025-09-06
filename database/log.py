import json
import time
import uuid
import logging
from typing import Dict, List, Optional
# from database.models import LogEntry
# from database.session import SessionLocal
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, Gauge

from .models import LogEntry
from .session import SessionLocal
 #promotheus metrics
TASKS_TOTAL = Counter('aoss_tasks_total', 'Total tasks', ['status','agent'])
ERRORS_TOTAL = Counter('aoss_errors_total', 'Total errors', ['error_type'])
RAG_QUERIES_TOTAL = Counter('aoss_rag_queries_total', 'RAG queries', ['db'])
TASK_DURATION = Histogram('aoss_task_duration_seconds', 'Task durations (s)', ['agent'])
ACTIVE_TASKS = Gauge('aoss_active_tasks', 'Currently active tasks')

# --- Monitoring metrics ---
CPU_USAGE = Gauge('aoss_cpu_usage_percent', 'CPU usage percent')
MEM_USAGE = Gauge('aoss_memory_usage_percent', 'Memory usage percent')
LOAD_AVG = Gauge('aoss_load_average', 'System load average', ['window'])
DISK_USAGE = Gauge('aoss_disk_usage_percent', 'Disk usage %', ['mount'])
NET_BYTES = Gauge('aoss_network_bytes_total', 'Network bytes', ['nic','direction'])
SERVICE_UP = Gauge('aoss_service_up', 'Service up (1=up,0=down)', ['service'])

ALERTS_TOTAL = Counter('aoss_alerts_total', 'Total alerts', ['type','severity'])


class StructuredLogger:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('aoss.observability')

    def log(
        self,
        agent_role: str,
        status: str,
        message: str,
        payload: Dict,
        rag_context_ids: List[str],
        task_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        step_id: str = "step-1",
        duration_ms: int = 100,
        db: Optional[Session] = None
    ) -> LogEntry:
        """Create & save a structured log entry. If `db` is provided, use it instead of opening SessionLocal."""
        created_local = False
        if db is None:
            db = SessionLocal()
            created_local = True

    # ) -> Dict:
    #     """Generate and store a structured log entry in database."""
    #     db = SessionLocal()
        try:
            log_entry = LogEntry(
                trace_id=trace_id or str(uuid.uuid4()),
                task_id=task_id or str(uuid.uuid4()),
                step_id=step_id,
                agent_role=agent_role,
                status=status,
                duration_ms=duration_ms,
                message=message,
                payload=payload,
                rag_context_ids=rag_context_ids
            )
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

             # Prometheus updates
            TASKS_TOTAL.labels(status=status, agent=agent_role).inc()
            if status.lower() != "success":
                ERRORS_TOTAL.labels(error_type=status).inc()
            TASK_DURATION.labels(agent=agent_role).observe(duration_ms / 1000.0)
            
            # Also log to console
            log_data = {
                "timestamp": log_entry.timestamp.isoformat(),
                "trace_id": log_entry.trace_id,
                "task_id": log_entry.task_id,
                "step_id": log_entry.step_id,
                "agent_role": log_entry.agent_role,
                "status": log_entry.status,
                "duration_ms": log_entry.duration_ms,
                "message": log_entry.message,
                "payload": log_entry.payload,
                "rag_context_ids": log_entry.rag_context_ids
            }
            self.logger.info(json.dumps(log_data,default=str))
            
            return log_entry
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to save log: {str(e)}")
            raise
        finally:
            if created_local:
                db.close()

logger = StructuredLogger()

# --- Metrics updater ---
def update_system_metrics(stats: Dict, services: List[Dict]):
    CPU_USAGE.set(stats.get("cpu_percent", 0))
    mem = stats.get("memory", {})
    if mem:
        MEM_USAGE.set(mem.get("percent", 0))
    load = stats.get("load", {})
    for w in ("1m","5m","15m"):
        v = load.get(w)
        if v is not None:
            LOAD_AVG.labels(window=w).set(v)
    for d in stats.get("disks", []):
        DISK_USAGE.labels(mount=d["mount"]).set(d.get("percent",0))
    for nic, c in (stats.get("network") or {}).items():
        NET_BYTES.labels(nic=nic, direction="sent").set(c.get("bytes_sent",0))
        NET_BYTES.labels(nic=nic, direction="recv").set(c.get("bytes_recv",0))
    for s in services:
        up = 1 if str(s.get("active","")).lower() == "running" else 0
        SERVICE_UP.labels(service=s.get("name","")).set(up)

# --- Alert evaluation ---
import os

def evaluate_alerts(stats: Dict, services: List[Dict]) -> List[Dict]:
    alerts=[]
    cpu_high = float(os.getenv("AOSS_CPU_HIGH","85"))
    mem_high = float(os.getenv("AOSS_MEM_HIGH","85"))
    disk_high = float(os.getenv("AOSS_DISK_HIGH","90"))
    must_run = [s.strip() for s in os.getenv("AOSS_MUST_RUN","").split(",") if s.strip()]

    if stats.get("cpu_percent",0) >= cpu_high:
        alerts.append({"type":"cpu","severity":"warning","message":f"CPU {stats['cpu_percent']}% >= {cpu_high}%"})

    mem_pct = (stats.get("memory") or {}).get("percent")
    if mem_pct is not None and mem_pct >= mem_high:
        alerts.append({"type":"memory","severity":"warning","message":f"Memory {mem_pct}% >= {mem_high}%"})

    for d in stats.get("disks",[]):
        if d.get("percent",0) >= disk_high:
            alerts.append({"type":"disk","severity":"warning","message":f"Disk {d['mount']} {d['percent']}% >= {disk_high}%"})

    by_name = {s['name']: s for s in services}
    for name in must_run:
        s = by_name.get(name)
        if not s or str(s.get("active","")).lower() != "running":
            alerts.append({"type":"service","severity":"critical","message":f"Service {name} not running"})

    return alerts

def emit_alerts(alerts: List[Dict], db: Optional[Session] = None):
    for a in alerts:
        ALERTS_TOTAL.labels(type=a["type"], severity=a["severity"]).inc()
        logger.log(
            agent_role="monitor",
            status="ALERT",
            message=a["message"],
            payload=a,
            rag_context_ids=[],
            db=db
        )
