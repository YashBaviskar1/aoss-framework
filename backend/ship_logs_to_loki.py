#!/usr/bin/env python3
"""
Standalone DB → Loki Log Shipper Script

This script:
- Fetches ALL execution logs from the database via API
- Transforms them into Loki's push format
- Ships them to Grafana Loki in batches
- Can be run manually or scheduled via cron

Purpose: Ship historical logs to Loki for observability in Grafana

Usage:
    python ship_logs_to_loki.py
    
    # Or with custom URLs:
    python ship_logs_to_loki.py --backend http://localhost:8000 --loki http://loki_tst:3100

Requirements:
- Backend API must be running
- Loki must be accessible
"""

import requests
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict


class LokiShipper:
    """
    Standalone log shipper that reads from API and pushes to Loki.
    
    DATA FLOW:
    1. GET /api/monitoring/logs → Fetch execution logs from PostgreSQL
    2. Transform each log entry into Loki format
    3. POST /loki/api/v1/push → Ship logs to Loki
    """
    
    def __init__(self, backend_url: str, loki_url: str):
        """
        Initialize the shipper.
        
        Args:
            backend_url: AOSS Backend API URL (e.g., http://localhost:8000)
            loki_url: Grafana Loki URL (e.g., http://localhost:3100 or http://loki_tst:3100)
        """
        self.backend_url = backend_url.rstrip('/')
        self.loki_url = loki_url.rstrip('/')
        self.stats = {
            "fetched": 0,
            "shipped": 0,
            "failed": 0,
            "batches": 0
        }
    
    def fetch_all_logs(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch execution logs from the backend API.
        
        Endpoint: GET /api/monitoring/logs
        Returns: List of log entries with execution details
        
        Each log entry contains:
        - timestamp: ISO 8601 timestamp
        - execution_id: Unique execution UUID
        - server_id, server_tag, server_ip: Server identification
        - agent_type: network/database/security/general
        - command: Executed command
        - status: Success/Failed
        - exit_code: Command exit code
        - stdout, stderr: Command output
        - execution_status: Overall execution status
        """
        print(f"📥 Fetching logs from: {self.backend_url}/api/monitoring/logs")
        
        try:
            response = requests.get(
                f"{self.backend_url}/api/monitoring/logs",
                params={"limit": limit},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error fetching logs: HTTP {response.status_code}")
                return []
            
            data = response.json()
            logs = data.get("logs", [])
            total_executions = data.get("total_executions", 0)
            
            self.stats["fetched"] = len(logs)
            print(f"✅ Fetched {len(logs)} log entries from {total_executions} executions")
            
            return logs
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching logs: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def convert_to_loki_format(self, logs: List[Dict]) -> Dict:
        """
        Transform AOSS logs into Loki's push API format.
        
        Loki Push API Format:
        {
          "streams": [
            {
              "stream": {
                "label1": "value1",
                "label2": "value2"
              },
              "values": [
                ["<nanosecond_timestamp>", "<log_message>"]
              ]
            }
          ]
        }
        
        Labels used:
        - job: "aoss" (constant)
        - server_id: Server UUID
        - server_tag: Human-readable server name
        - agent_type: network/database/security/general
        - status: Success/Failed
        - execution_status: Overall execution status
        
        Message format:
        STEP: 1 | COMMAND: ls -la | EXIT_CODE: 0 | STDOUT: ... | STDERR: ...
        """
        print(f"🔄 Converting {len(logs)} logs to Loki format...")
        
        # Group logs by label set for efficiency
        streams_map = {}
        
        for log in logs:
            # Extract fields from log entry
            timestamp_iso = log.get("timestamp")
            execution_id = log.get("execution_id")
            server_id = log.get("server_id", "unknown")
            server_tag = log.get("server_tag", "unknown")
            agent_type = log.get("agent_type", "general")
            step = log.get("step", 0)
            command = log.get("command", "")
            status = log.get("status", "unknown")
            exit_code = log.get("exit_code")
            stdout = log.get("stdout", "")
            stderr = log.get("stderr", "")
            exec_status = log.get("execution_status", "unknown")
            
            # Create Loki labels
            labels = {
                "job": "aoss",
                "server_id": server_id,
                "server_tag": server_tag,
                "agent_type": agent_type,
                "status": status,
                "execution_status": exec_status
            }
            
            # Create label key for grouping
            label_key = json.dumps(labels, sort_keys=True)
            
            # Build log message
            message_parts = [f"STEP: {step}"]
            if command:
                message_parts.append(f"COMMAND: {command}")
            if exit_code is not None:
                message_parts.append(f"EXIT_CODE: {exit_code}")
            if stdout:
                # Truncate long output
                stdout_short = stdout[:300] + "..." if len(stdout) > 300 else stdout
                message_parts.append(f"STDOUT: {stdout_short}")
            if stderr:
                stderr_short = stderr[:300] + "..." if len(stderr) > 300 else stderr
                message_parts.append(f"STDERR: {stderr_short}")
            
            message = " | ".join(message_parts)
            
            # Convert timestamp to nanoseconds (Loki requirement)
            if timestamp_iso:
                try:
                    # Handle both with and without timezone
                    dt = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
                    timestamp_ns = str(int(dt.timestamp() * 1_000_000_000))
                except Exception:
                    # Fallback to current time if parsing fails
                    timestamp_ns = str(int(time.time() * 1_000_000_000))
            else:
                timestamp_ns = str(int(time.time() * 1_000_000_000))
            
            # Group by labels
            if label_key not in streams_map:
                streams_map[label_key] = {
                    "stream": labels,
                    "values": []
                }
            
            streams_map[label_key]["values"].append([timestamp_ns, message])
        
        # Build final payload
        payload = {
            "streams": list(streams_map.values())
        }
        
        print(f"✅ Created {len(streams_map)} streams for Loki")
        return payload
    
    def push_to_loki(self, payload: Dict) -> bool:
        """
        Push logs to Loki via HTTP POST.
        
        Endpoint: POST /loki/api/v1/push
        Content-Type: application/json
        
        Returns: True if successful, False otherwise
        """
        if not payload.get("streams"):
            print("⚠️  No streams to push")
            return False
        
        stream_count = len(payload["streams"])
        log_count = sum(len(s["values"]) for s in payload["streams"])
        
        print(f"📤 Pushing {log_count} logs ({stream_count} streams) to Loki...")
        print(f"   Target: {self.loki_url}/loki/api/v1/push")
        
        try:
            response = requests.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 204 or response.status_code == 200:
                print(f"✅ Successfully pushed logs to Loki")
                self.stats["shipped"] += log_count
                self.stats["batches"] += 1
                return True
            else:
                print(f"❌ Loki returned error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.stats["failed"] += log_count
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Loki at {self.loki_url}")
            print(f"   Is Loki running? Check: docker ps | grep loki")
            self.stats["failed"] += log_count
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error pushing to Loki: {e}")
            self.stats["failed"] += log_count
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.stats["failed"] += log_count
            return False
    
    def ship_logs(self, batch_size: int = 500):
        """
        Main method: Fetch logs from API and ship to Loki in batches.
        
        Args:
            batch_size: Number of logs to fetch per batch
        """
        print("=" * 60)
        print("🚀 AOSS → Loki Log Shipper")
        print("=" * 60)
        print()
        
        # Fetch logs from backend API
        logs = self.fetch_all_logs(limit=batch_size)
        
        if not logs:
            print("⚠️  No logs found to ship")
            return
        
        print()
        
        # Convert to Loki format
        payload = self.convert_to_loki_format(logs)
        
        print()
        
        # Push to Loki
        success = self.push_to_loki(payload)
        
        print()
        print("=" * 60)
        print("📊 Summary")
        print("=" * 60)
        print(f"Fetched:  {self.stats['fetched']} logs")
        print(f"Shipped:  {self.stats['shipped']} logs")
        print(f"Failed:   {self.stats['failed']} logs")
        print(f"Batches:  {self.stats['batches']}")
        print()
        
        if success:
            print("✅ Logs successfully shipped to Loki!")
            print("   View in Grafana: http://localhost:3001")
            print("   Query: {job=\"aoss\"}")
        else:
            print("❌ Failed to ship logs")


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Ship AOSS execution logs to Grafana Loki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ship logs from local backend to local Loki
  python ship_logs_to_loki.py

  # Ship to Docker Loki container
  python ship_logs_to_loki.py --loki http://loki_tst:3100

  # Custom backend and Loki URLs
  python ship_logs_to_loki.py --backend http://localhost:8000 --loki http://192.168.1.10:3100

  # Ship more logs (default: 500)
  python ship_logs_to_loki.py --batch-size 1000
        """
    )
    
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--loki",
        default="http://localhost:3100",
        help="Loki URL (default: http://localhost:3100, use http://loki_tst:3100 for Docker)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of logs to fetch (default: 500)"
    )
    
    args = parser.parse_args()
    
    # Create and run shipper
    shipper = LokiShipper(
        backend_url=args.backend,
        loki_url=args.loki
    )
    
    shipper.ship_logs(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
