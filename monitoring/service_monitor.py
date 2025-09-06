# monitoring/service_monitor.py
import json
import shutil
import subprocess
import platform


def _run(cmd: list[str]):
    """Run a shell command and return result."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _systemctl_exists() -> bool:
    """Check if systemctl is available in this environment."""
    return shutil.which("systemctl") is not None


def list_services() -> list[dict]:
    """List services and their states (Linux/WSL only)."""
    svcs = []

    # If running on Windows, skip
    if platform.system().lower() == "windows":
        return [{"note": "Service monitoring not supported on Windows. Run inside Linux/WSL."}]

    if _systemctl_exists():
        # Try JSON output (newer systemd versions support this)
        res = _run([
            "systemctl", "list-units",
            "--type=service", "--all", "--no-pager",
            "--no-legend", "--plain", "--output=json"
        ])
        if res.returncode == 0 and res.stdout.strip().startswith("["):
            try:
                for s in json.loads(res.stdout):
                    svcs.append({
                        "name": s.get("unit", ""),
                        "load": s.get("load", ""),
                        "active": s.get("active", ""),
                        "sub": s.get("sub", ""),
                        "description": s.get("description", "")
                    })
                return svcs
            except Exception:
                pass

        # Fallback: parse plain-text output
        res = _run([
            "systemctl", "list-units",
            "--type=service", "--all", "--no-pager", "--no-legend", "--plain"
        ])
        for line in res.stdout.splitlines():
            parts = line.split(None, 4)  # UNIT LOAD ACTIVE SUB DESCRIPTION
            if len(parts) >= 5:
                unit, load, active, sub, desc = parts
                svcs.append({
                    "name": unit,
                    "load": load,
                    "active": active,
                    "sub": sub,
                    "description": desc
                })

    else:
        # Fallback for WSL without systemd: sysvinit service list
        res = _run(["service", "--status-all"])
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            status = "unknown"
            if "[ + ]" in line:
                status = "running"
            elif "[ - ]" in line:
                status = "stopped"
            name = line.split("]")[-1].strip()
            svcs.append({
                "name": name,
                "load": "unknown",
                "active": status,
                "sub": status,
                "description": ""
            })

    return svcs


if __name__ == "__main__":
    services = list_services()
    print(json.dumps(services, indent=2))
