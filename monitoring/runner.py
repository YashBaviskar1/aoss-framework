# monitoring/runner.py
import os
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database.log import logger, update_system_metrics, evaluate_alerts, emit_alerts
from monitoring import system_monitor, service_monitor

# Optional: JSON lines & Prometheus textfile for legacy/Promtail ingestion
LOG_FILE = "monitoring_logs.jsonl"
PROM_METRICS_FILE = "monitoring_metrics.prom"

def log_to_file(data: dict, file_path: str = LOG_FILE):
    """Append a JSON entry to the log file."""
    with open(file_path, "a") as f:
        f.write(json.dumps(data, default=str) + "\n")

def write_prometheus_metrics(system_data: dict, services_data: list[dict], file_path: str = PROM_METRICS_FILE):
    """Write metrics in Prometheus text format (legacy/optional)."""
    lines = []

    # System metrics
    lines.append(f'system_cpu_percent {system_data.get("cpu_percent", 0)}')
    lines.append(f'system_memory_percent {system_data.get("memory", {}).get("percent", 0)}')

    # Max disk usage across all disks
    disk_percent = max([d.get("percent", 0) for d in system_data.get("disks", [])], default=0)
    lines.append(f'system_disk_percent {disk_percent}')

    # Services
    for svc in services_data:
        status = 1 if str(svc.get("active", "")).lower() == "running" else 0
        name = svc.get("name", "unknown").replace(".", "_").replace("-", "_")
        lines.append(f'service_status{{name="{name}"}} {status}')

    with open(file_path, "w") as f:
        f.write("\n".join(lines) + "\n")

async def monitor_loop():
    interval = int(os.environ.get("MONITOR_INTERVAL", 60))  # seconds
    while True:
        db: Session = SessionLocal()
        try:
            # Collect system + service metrics
            system_data = system_monitor.collect_system_stats(top_n=10)
            services_data = service_monitor.list_services()

            # Update Prometheus metrics
            update_system_metrics(system_data, services_data)

            # Log structured snapshot
            logger.log(
                agent_role="monitor",
                status="success",
                message="system snapshot",
                payload={"system": system_data, "services": services_data},
                rag_context_ids=[],
                db=db
            )

            # Evaluate alerts
            alerts = evaluate_alerts(system_data, services_data)
            emit_alerts(alerts, db=db)

            # Compute disk usage for console output
            disk_percent = max([d.get("percent", 0) for d in system_data.get("disks", [])], default=0)
            mem_percent = system_data.get("memory", {}).get("percent", 0)

            # Console output
            print(f"[{datetime.utcnow().isoformat()}] Metrics logged: "
                  f"CPU={system_data.get('cpu_percent',0)}%, "
                  f"Memory={mem_percent}%, "
                  f"Disk={disk_percent}%")

            # Optional: log to JSON/Prometheus textfile
            log_to_file({
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_data,
                "services": services_data
            })
            write_prometheus_metrics(system_data, services_data)

        except Exception as e:
            logger.log(
                agent_role="monitor",
                status="error",
                message=f"monitor loop error: {e}",
                payload={},
                rag_context_ids=[],
                db=db
            )
        finally:
            db.close()

        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_loop())
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
