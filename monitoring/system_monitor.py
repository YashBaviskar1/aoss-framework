# monitoring/system_monitor.py
import os
import time
import platform
import psutil


def _load_avg():
    """Get system load average (Linux only)."""
    try:
        a1, a5, a15 = os.getloadavg()
        return {"1m": a1, "5m": a5, "15m": a15}
    except Exception:
        # Windows/WSL fallback
        return {"1m": None, "5m": None, "15m": None}


def _uptime_sec():
    """Get uptime in seconds (Linux only)."""
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception:
        return None


def collect_system_stats(top_n: int = 5) -> dict:
    """Collect system metrics similar to htop style."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disks
    disks = []
    for p in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(p.mountpoint)
            disks.append({
                "device": p.device,
                "mount": p.mountpoint,
                "fstype": p.fstype,
                "total": u.total,
                "used": u.used,
                "free": u.free,
                "percent": u.percent
            })
        except Exception:
            continue

    # Network
    net = psutil.net_io_counters(pernic=True)

    # Top processes (sorted by CPU%)
    top_procs = []
    for proc in sorted(
        psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']),
        key=lambda x: (x.info.get('cpu_percent') or 0),
        reverse=True
    )[:top_n]:
        info = proc.info
        top_procs.append({
            "pid": info.get("pid"),
            "name": info.get("name") or "unknown",         # <-- Windows-safe
            "username": info.get("username") or "unknown", # <-- Windows-safe
            "cpu_percent": info.get("cpu_percent", 0.0),
            "memory_percent": info.get("memory_percent", 0.0),
        })

    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "uptime_seconds": _uptime_sec(),
        "load": _load_avg(),
        "cpu_percent": cpu,
        "memory": {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent
        },
        "disks": disks,
        "network": {
            nic: {
                "bytes_sent": c.bytes_sent,
                "bytes_recv": c.bytes_recv,
                "packets_sent": c.packets_sent,
                "packets_recv": c.packets_recv,
                "errin": c.errin,
                "errout": c.errout
            } for nic, c in net.items()
        },
        "top_processes": top_procs,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import json
    stats = collect_system_stats()
    print(json.dumps(stats, indent=2, default=str))
