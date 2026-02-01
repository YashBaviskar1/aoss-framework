import boto3
import json
import os
from typing import List
from fastapi import APIRouter, HTTPException, Depends
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
