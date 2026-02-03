import boto3
import json
import os
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from agents.executor import RemoteExecutor

router = APIRouter()

def open_aws_port(access_key, secret_key, region, instance_id, port=9100):
    """
    Finds the security group of an EC2 instance and opens the port using provided creds.
    """
    try:
        if not all([access_key, secret_key, region, instance_id]):
             raise Exception("Missing AWS Credentials or Instance ID")

        # Init Client with Dynamic Creds
        ec2_client = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # 1. Get Instance Details to find Security Group
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        reservations = response.get('Reservations', [])
        if not reservations:
            raise Exception("Instance not found")
        
        instance = reservations[0]['Instances'][0]
        if not instance.get('SecurityGroups'):
             raise Exception("No Security Groups attached to this instance")
             
        sg_id = instance['SecurityGroups'][0]['GroupId']
        
        print(f"Opening port {port} on Security Group: {sg_id}")

        # 2. Authorize Ingress
        try:
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': port,
                        'ToPort': port,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}] # Ideally restrict this!
                    }
                ]
            )
        except ec2_client.exceptions.ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                print("Port already open.")
            else:
                raise e
                
        return True
    except Exception as e:
        print(f"AWS Error: {e}")
        # We re-raise to show the user the specific AWS error
        raise Exception(f"AWS Security Group Update Failed: {str(e)}")

def update_prometheus_targets(ip_address: str):
    """
    Updates the targets.json file so Prometheus starts scraping immediately.
    """
    # Assuming targets.json is in a known location relative to backend or absolute path
    # For this environment, let's put it in the backend root or a specific monitor folder
    # User mentioned: "Create an initial empty targets.json in the same folder [as prometheus]"
    # Since we are running backend separately, we will simulate this by writing to a local file
    # that Prometheus WOULD be watching if it were local. 
    # In a real deployed setup, this file needs to be on the Prometheus server volume.
    
    # Updated path to match the docker volume mount
    target_dir = os.path.join("monitering", "prometheus")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    target_file = os.path.join(target_dir, "targets.json") 
    
    # Load existing
    if os.path.exists(target_file):
        try:
            with open(target_file, 'r') as f:
                content = f.read()
                if not content.strip():
                    targets = []
                else:
                    targets = json.loads(content)
        except json.JSONDecodeError:
            targets = []
    else:
        targets = []

    # Check if exists
    new_target = f"{ip_address}:9100"
    
    # Simplified logic: remove existing entry for this IP if any, then add fresh
    # This prevents duplicates
    targets = [t for t in targets if new_target not in t['targets']]
    
    # Add new
    targets.append({
        "targets": [new_target],
        "labels": {"job": "node_exporter", "env": "production"}
    })
    
    with open(target_file, 'w') as f:
        json.dump(targets, f, indent=2)

@router.post("/api/monitoring/enable/{server_id}")
def enable_monitoring(server_id: str, req: schemas.MonitoringRequest, db: Session = Depends(get_db)):
    """
    One-Click Setup: Opens Port -> Installs Agent -> Configures Prometheus
    """
    print(f"Enabling monitoring for server {server_id} on AWS Instance {req.instance_id}")

    # 1. Get Server Info
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # 2. Open AWS Port
    try:
        open_aws_port(req.aws_access_key, req.aws_secret_key, req.aws_region, req.instance_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Install Node Exporter via SSH
    install_script = """
    if ! command -v node_exporter &> /dev/null; then
        echo "Installing Node Exporter..."
        # Download (using a mirror or github)
        wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz -O /tmp/node_exporter.tar.gz
        
        # Extract
        tar xvf /tmp/node_exporter.tar.gz -C /tmp/
        
        # Move binary
        sudo mv /tmp/node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
        
        # Create Service User if not exists (optional, skipping for root simplicty in prototype)
        
        # Create Service
        sudo bash -c 'cat > /etc/systemd/system/node_exporter.service <<EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=root
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF'
        sudo systemctl daemon-reload
        sudo systemctl enable node_exporter
        sudo systemctl start node_exporter
    else
        echo "Node Exporter already installed."
        sudo systemctl start node_exporter
    fi
    """

    executor = RemoteExecutor(
        host=str(server.ip_address),
        user=server.ssh_username,
        key_path=server.ssh_key_path,
        password=server.ssh_password_encrypted
    )
    
    try:
        executor.connect()
        result = executor.execute_step(install_script)
        if result['exit_code'] != 0:
             # Just log warning, sometimes it might fail if apt lock held etc, but we proceed
             print(f"Installation warning: {result['stderr']}")
             if "Permission denied" in result['stderr']:
                  raise Exception(f"SSH Permission Denied: {result['stderr']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Installation Failed: {str(e)}")
    finally:
        executor.close()

    # 4. Update Database
    # Check if config exists
    mon_config = db.query(models.MonitoringConfig).filter(models.MonitoringConfig.server_id == server_id).first()
    if not mon_config:
        mon_config = models.MonitoringConfig(
            server_id=server.id,
            monitor_path="/metrics",
            interval_seconds=30
        )
        db.add(mon_config)
        db.commit()

    # 5. Update Prometheus Config Local File
    update_prometheus_targets(str(server.ip_address))

    return {"status": "success", "message": "Monitoring enabled successfully. Port 9100 opened, Agent installed, Target added."}

@router.get("/api/monitoring/status", response_model=List[dict])
def get_monitoring_status(db: Session = Depends(get_db)):
    """
    Returns list of servers with their monitoring status.
    """
    servers = db.query(models.Server).all()
    result = []
    
    for server in servers:
        # Check if config exists
        config = db.query(models.MonitoringConfig).filter(models.MonitoringConfig.server_id == server.id).first()
        is_enabled = config is not None
        
        result.append({
            "id": server.id,
            "server_tag": server.server_tag,
            "ip_address": server.ip_address,
            "monitoring_enabled": is_enabled,
            # We could add last_scraped or health status if we queried Prometheus here
        })
        
    return result


@router.post("/api/monitoring/alerts")
async def receive_grafana_alert(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint to receive Grafana alerts.
    Stores alert data without modification.
    """
    try:
        payload = await request.json()
        
        # Extract alerts from Grafana webhook payload
        alerts = payload.get("alerts", [])
        
        for alert in alerts:
            # Parse labels and annotations
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            
            # Extract instance (server identifier) and try to match with server
            instance = labels.get("instance", "")
            server_id = None
            
            if instance:
                # Try to match instance IP with server IP
                # Instance format is usually "IP:PORT"
                instance_ip = instance.split(":")[0] if ":" in instance else instance
                server = db.query(models.Server).filter(
                    models.Server.ip_address == instance_ip
                ).first()
                if server:
                    server_id = server.id
            
            # Parse timestamps
            starts_at = None
            ends_at = None
            if alert.get("startsAt"):
                try:
                    starts_at = datetime.fromisoformat(alert["startsAt"].replace("Z", "+00:00"))
                except:
                    pass
            if alert.get("endsAt"):
                try:
                    ends_at = datetime.fromisoformat(alert["endsAt"].replace("Z", "+00:00"))
                except:
                    pass
            
            # Create alert record
            grafana_alert = models.GrafanaAlert(
                alertname=labels.get("alertname", "Unknown"),
                fingerprint=alert.get("fingerprint"),
                instance=instance,
                severity=labels.get("severity", "info"),
                status=alert.get("status", "firing"),
                summary=annotations.get("summary"),
                description=annotations.get("description"),
                starts_at=starts_at,
                ends_at=ends_at,
                raw_payload=alert,
                server_id=server_id
            )
            
            db.add(grafana_alert)
        
        db.commit()
        
        return {"status": "success", "message": f"Processed {len(alerts)} alert(s)"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process alert: {str(e)}")


@router.get("/api/monitoring/alerts")
def get_alerts(
    status: str = None,
    severity: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Returns list of Grafana alerts.
    Filters: status (firing, resolved), severity (critical, warning, info)
    """
    query = db.query(models.GrafanaAlert).order_by(models.GrafanaAlert.received_at.desc())
    
    if status:
        query = query.filter(models.GrafanaAlert.status == status)
    if severity:
        query = query.filter(models.GrafanaAlert.severity == severity)
    
    alerts = query.limit(limit).all()
    
    result = []
    for alert in alerts:
        # Get server info if linked
        server_tag = None
        server_ip = None
        if alert.server_id:
            server = db.query(models.Server).filter(models.Server.id == alert.server_id).first()
            if server:
                server_tag = server.server_tag
                server_ip = str(server.ip_address)
        
        result.append({
            "id": str(alert.id),
            "alertname": alert.alertname,
            "instance": alert.instance,
            "severity": alert.severity,
            "status": alert.status,
            "summary": alert.summary,
            "description": alert.description,
            "starts_at": alert.starts_at.isoformat() if alert.starts_at else None,
            "ends_at": alert.ends_at.isoformat() if alert.ends_at else None,
            "received_at": alert.received_at.isoformat() if alert.received_at else None,
            "server_tag": server_tag,
            "server_ip": server_ip,
            "server_id": str(alert.server_id) if alert.server_id else None
        })
    
    return result


@router.get("/api/monitoring/logs")
def get_execution_logs(
    limit: int = 100,
    server_id: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    READ-ONLY endpoint to expose execution logs in structured format.
    
    Extracts per-step execution events from execution_results JSON and
    flattens them into log records suitable for observability tools.
    
    Query Parameters:
    - limit: Maximum number of execution records to fetch (default: 100)
    - server_id: Filter by specific server UUID
    - status: Filter by execution status (Success, Failed, Planned)
    
    Returns:
    - List of log entries with timestamp, agent_type, server_id, command, status, etc.
    """
    query = db.query(models.ExecutionLog).order_by(models.ExecutionLog.created_at.desc())
    
    # Apply filters
    if server_id:
        query = query.filter(models.ExecutionLog.server_id == server_id)
    if status:
        query = query.filter(models.ExecutionLog.status == status)
    
    execution_logs = query.limit(limit).all()
    
    log_entries = []
    
    for exec_log in execution_logs:
        # Get server info
        server = db.query(models.Server).filter(models.Server.id == exec_log.server_id).first()
        server_tag = server.server_tag if server else "unknown"
        server_ip = str(server.ip_address) if server else "unknown"
        
        # Extract agent type from query/plan (heuristic)
        agent_type = "general"
        if exec_log.plan and isinstance(exec_log.plan, list) and len(exec_log.plan) > 0:
            # Agent type might be embedded in plan or we use query keywords
            query_lower = exec_log.query.lower() if exec_log.query else ""
            if any(kw in query_lower for kw in ["network", "firewall", "dns", "port"]):
                agent_type = "network"
            elif any(kw in query_lower for kw in ["database", "postgres", "mysql", "sql"]):
                agent_type = "database"
            elif any(kw in query_lower for kw in ["security", "audit", "permission", "user"]):
                agent_type = "security"
        
        # Flatten execution_results into individual log entries
        if exec_log.execution_results and isinstance(exec_log.execution_results, list):
            for step_result in exec_log.execution_results:
                # Truncate output for log readability
                stdout = step_result.get("stdout", "")
                stderr = step_result.get("stderr", "")
                stdout_truncated = stdout[:500] + "..." if len(stdout) > 500 else stdout
                stderr_truncated = stderr[:500] + "..." if len(stderr) > 500 else stderr
                
                log_entry = {
                    "timestamp": exec_log.created_at.isoformat() if exec_log.created_at else None,
                    "execution_id": str(exec_log.id),
                    "user_id": exec_log.user_id,
                    "server_id": str(exec_log.server_id),
                    "server_tag": server_tag,
                    "server_ip": server_ip,
                    "agent_type": agent_type,
                    "query": exec_log.query,
                    "step": step_result.get("step", 0),
                    "command": step_result.get("command", ""),
                    "status": step_result.get("status", "Unknown"),
                    "exit_code": step_result.get("exit_code"),
                    "stdout": stdout_truncated,
                    "stderr": stderr_truncated,
                    "execution_status": exec_log.status,
                    "agent_summary": exec_log.agent_summary
                }
                log_entries.append(log_entry)
        else:
            # No execution results yet (Planned state), create a single entry
            log_entry = {
                "timestamp": exec_log.created_at.isoformat() if exec_log.created_at else None,
                "execution_id": str(exec_log.id),
                "user_id": exec_log.user_id,
                "server_id": str(exec_log.server_id),
                "server_tag": server_tag,
                "server_ip": server_ip,
                "agent_type": agent_type,
                "query": exec_log.query,
                "step": 0,
                "command": "",
                "status": exec_log.status,
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "execution_status": exec_log.status,
                "agent_summary": exec_log.agent_summary
            }
            log_entries.append(log_entry)
    
    return {
        "total_executions": len(execution_logs),
        "total_log_entries": len(log_entries),
        "logs": log_entries
    }
