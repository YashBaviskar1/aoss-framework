"""
Lightweight Log Shipper for AOSS Execution Logs

This component:
- Periodically fetches execution logs from /api/monitoring/logs
- Transforms them into Grafana Loki format
- Ships logs to Loki via HTTP API
- Tracks processed logs to prevent duplicates
- Fails silently if Loki is unreachable

CRITICAL: This is a READ-ONLY observer. It does NOT modify execution behavior.
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Set, List, Dict
from threading import Thread, Lock
import logging

# Suppress verbose logging from this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class LokiLogShipper:
    """
    Background service that ships AOSS execution logs to Grafana Loki.
    """
    
    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        loki_url: str = "http://localhost:3100",
        poll_interval: int = 30,
        batch_size: int = 100
    ):
        self.backend_url = backend_url.rstrip('/')
        self.loki_url = loki_url.rstrip('/')
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        
        # Track processed execution_ids to prevent duplicates
        self.processed_executions: Set[str] = set()
        self.lock = Lock()
        
        # Thread control
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background log shipping thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._shipping_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the background log shipping thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _shipping_loop(self):
        """Main loop that periodically fetches and ships logs."""
        while self.running:
            try:
                self._fetch_and_ship_logs()
            except Exception:
                # Fail silently - don't crash the shipper
                pass
            
            # Sleep for poll interval
            time.sleep(self.poll_interval)
    
    def _fetch_and_ship_logs(self):
        """Fetch logs from backend API and ship to Loki."""
        try:
            # Fetch logs from the monitoring API
            response = requests.get(
                f"{self.backend_url}/api/monitoring/logs",
                params={"limit": self.batch_size},
                timeout=5
            )
            
            if response.status_code != 200:
                return
            
            data = response.json()
            logs = data.get("logs", [])
            
            if not logs:
                return
            
            # Filter out already processed logs
            new_logs = self._filter_processed_logs(logs)
            
            if not new_logs:
                return
            
            # Convert to Loki format and ship
            loki_payload = self._convert_to_loki_format(new_logs)
            self._push_to_loki(loki_payload)
            
            # Mark logs as processed
            self._mark_processed(new_logs)
            
        except requests.exceptions.RequestException:
            # Fail silently if backend is unreachable
            pass
        except Exception:
            # Fail silently on any error
            pass
    
    def _filter_processed_logs(self, logs: List[Dict]) -> List[Dict]:
        """Filter out logs that have already been processed."""
        with self.lock:
            new_logs = []
            for log in logs:
                exec_id = log.get("execution_id")
                step = log.get("step", 0)
                # Create unique key for each step in each execution
                log_key = f"{exec_id}:{step}"
                
                if log_key not in self.processed_executions:
                    new_logs.append(log)
            
            return new_logs
    
    def _mark_processed(self, logs: List[Dict]):
        """Mark logs as processed to prevent duplicates."""
        with self.lock:
            for log in logs:
                exec_id = log.get("execution_id")
                step = log.get("step", 0)
                log_key = f"{exec_id}:{step}"
                self.processed_executions.add(log_key)
            
            # Prevent memory growth - keep only last 10000 entries
            if len(self.processed_executions) > 10000:
                # Remove oldest half
                to_remove = list(self.processed_executions)[:5000]
                for key in to_remove:
                    self.processed_executions.discard(key)
    
    def _convert_to_loki_format(self, logs: List[Dict]) -> Dict:
        """
        Convert AOSS logs to Loki push API format.
        
        Loki format:
        {
          "streams": [
            {
              "stream": {
                "label1": "value1",
                "label2": "value2"
              },
              "values": [
                ["<unix_epoch_nanoseconds>", "<log_line>"]
              ]
            }
          ]
        }
        """
        # Group logs by label set for efficiency
        streams_map = {}
        
        for log in logs:
            # Create label set
            labels = {
                "job": "aoss",
                "server_id": log.get("server_id", "unknown"),
                "server_tag": log.get("server_tag", "unknown"),
                "agent_type": log.get("agent_type", "general"),
                "status": log.get("status", "unknown"),
                "execution_status": log.get("execution_status", "unknown")
            }
            
            # Create label key for grouping
            label_key = json.dumps(labels, sort_keys=True)
            
            # Create log message
            command = log.get("command", "")
            stdout = log.get("stdout", "")
            stderr = log.get("stderr", "")
            exit_code = log.get("exit_code")
            
            # Format message
            message_parts = []
            if command:
                message_parts.append(f"COMMAND: {command}")
            if exit_code is not None:
                message_parts.append(f"EXIT_CODE: {exit_code}")
            if stdout:
                message_parts.append(f"STDOUT: {stdout}")
            if stderr:
                message_parts.append(f"STDERR: {stderr}")
            
            message = " | ".join(message_parts) if message_parts else "No output"
            
            # Convert timestamp to nanoseconds
            timestamp_iso = log.get("timestamp")
            if timestamp_iso:
                try:
                    dt = datetime.fromisoformat(timestamp_iso.replace('Z', '+00:00'))
                    timestamp_ns = str(int(dt.timestamp() * 1_000_000_000))
                except Exception:
                    timestamp_ns = str(int(time.time() * 1_000_000_000))
            else:
                timestamp_ns = str(int(time.time() * 1_000_000_000))
            
            # Add to stream
            if label_key not in streams_map:
                streams_map[label_key] = {
                    "stream": labels,
                    "values": []
                }
            
            streams_map[label_key]["values"].append([timestamp_ns, message])
        
        # Convert to Loki payload
        payload = {
            "streams": list(streams_map.values())
        }
        
        return payload
    
    def _push_to_loki(self, payload: Dict):
        """Push logs to Loki via HTTP API."""
        try:
            response = requests.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Silently ignore if Loki is unreachable or returns error
            # No need to log or raise exceptions
            
        except requests.exceptions.RequestException:
            # Fail silently if Loki is unreachable
            pass
        except Exception:
            # Fail silently on any error
            pass


# Global instance
_shipper_instance = None


def start_log_shipper(
    backend_url: str = None,
    loki_url: str = None,
    poll_interval: int = 30
):
    """
    Start the global log shipper instance.
    
    Args:
        backend_url: Backend API URL (default: http://localhost:8000)
        loki_url: Loki URL (default: http://localhost:3100)
        poll_interval: Polling interval in seconds (default: 30)
    """
    global _shipper_instance
    
    if _shipper_instance is not None:
        return
    
    # Use environment variables or defaults
    backend_url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8000")
    loki_url = loki_url or os.getenv("LOKI_URL", "http://localhost:3100")
    
    _shipper_instance = LokiLogShipper(
        backend_url=backend_url,
        loki_url=loki_url,
        poll_interval=poll_interval
    )
    
    _shipper_instance.start()


def stop_log_shipper():
    """Stop the global log shipper instance."""
    global _shipper_instance
    
    if _shipper_instance is not None:
        _shipper_instance.stop()
        _shipper_instance = None
