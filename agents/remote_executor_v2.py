#!/usr/bin/env python3
"""
remote_executor_v2.py

Simple SSH remote executor with two backends.
V2 Update: Includes ANSI code stripping to clean terminal output.
"""

import os
import sys
import json
import getpass
import shlex
import subprocess
import re  # <-- IMPORTED RE
from typing import Optional, Dict, Any, List

try:
    import paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _HAS_PARAMIKO = False

# -------------------------
# NEW: ANSI Stripping Function
# -------------------------
def clean_ansi_output(text: str) -> str:
    """
    Removes ANSI escape sequences (for colors, progress bars)
    and other common terminal control characters.
    """
    if not text:
        return ""
    # Regex for ANSI escape codes
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    text = ansi_escape.sub('', text)
    
    # Remove other control chars like carriage return
    # This stops lines from overwriting each other in the log
    text = re.sub(r'[\r\b]', '', text)
    
    # Optional: Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

# -------------------------
# Logger
# -------------------------
class Logger:
    def log(self, step, command, return_code, stdout, stderr):
        status = "SUCCESS" if return_code == 0 else "FAILED"
        # Note: stdout/stderr are now pre-cleaned by ParamikoBackend
        log_entry = {
            "step": step, "command": command, "status": status,
            "stdout": stdout.strip(), "stderr": stderr.strip(),
        }
        print("="*70)
        print(f"STEP: {log_entry['step']} | COMMAND: `{log_entry['command']}` | STATUS: {log_entry['status']}")
        
        # Only print if there is content
        if log_entry['stdout']:
            print("\n--- STDOUT ---\n" + log_entry['stdout'])
        if log_entry['stderr']:
            print("\n--- STDERR ---\n" + log_entry['stderr'])
        
        print("="*70 + "\n")
        return log_entry

# -------------------------
# SSH Backend Interfaces
# -------------------------
class ParamikoBackend:
    def __init__(self, host, user, password=None, key_filename=None, port=22, timeout=10):
        if not _HAS_PARAMIKO:
            raise RuntimeError("Paramiko not installed. Use `pip install paramiko`.")
        self.host = host
        self.user = user
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.timeout = timeout
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = dict(hostname=self.host, port=self.port, username=self.user, timeout=self.timeout)
        if self.key_filename:
            connect_kwargs['key_filename'] = self.key_filename
        else:
            connect_kwargs['password'] = self.password
        self.client.connect(**connect_kwargs)

    def execute(self, command, cwd=None, timeout=None):
        safe_cmd = f"cd {shlex.quote(cwd)} && {command}" if cwd else command
        
        stdin, stdout, stderr = self.client.exec_command(safe_cmd, get_pty=True, timeout=timeout)
        
        if command.strip().startswith('sudo') and self.password:
            stdin.write(self.password + '\n')
            stdin.flush()
            
        # Read raw output
        raw_out = stdout.read().decode(errors='replace')
        raw_err = stderr.read().decode(errors='replace')
        exit_status = stdout.channel.recv_exit_status()
        
        # --- NEW: Clean the output before returning ---
        out = clean_ansi_output(raw_out)
        err = clean_ansi_output(raw_err)
        
        return exit_status, out, err

    def close(self):
        if self.client: self.client.close()

class SystemSSHBackend:
    # (Leaving this as-is, as Paramiko is the focus)
    def __init__(self, host, user, password=None, key_filename=None, port=22, ssh_binary="ssh"):
        self.host, self.user, self.key_filename, self.port = host, user, key_filename, port

    def connect(self): pass

    def execute(self, command, cwd=None, timeout=None):
        remote_cmd = f"cd {shlex.quote(cwd)} && {command}" if cwd else command
        ssh_cmd = ["ssh", "-p", str(self.port), f"{self.user}@{self.host}", remote_cmd]
        if self.key_filename: ssh_cmd.insert(1, "-i"); ssh_cmd.insert(2, self.key_filename)
        try:
            proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
            # --- NEW: Clean the output here too ---
            out = clean_ansi_output(proc.stdout)
            err = clean_ansi_output(proc.stderr)
            return proc.returncode, out, err
        except Exception as e:
            return 1, "", f"Exception running ssh: {e}"

    def close(self): pass

# -------------------------
# Remote Plan Runner
# -------------------------
class RemotePlanRunner:
    def __init__(self, backend, env: Dict[str, str] = None):
        self.backend = backend
        self.logger = Logger()
        self.remote_pwd = None
        self.env = env or {}

    def _init_remote_pwd(self):
        code, out, err = self.backend.execute("pwd")
        self.remote_pwd = out.strip() if code == 0 and out.strip() else f"/home/{self.backend.user}"
        print(f"[Remote PWD initialized to] {self.remote_pwd}")

    def _interpolate_env(self, command: str):
        for k, v in (self.env or {}).items():
            command = command.replace(f"{{{k}}}", v).replace(f"{{{{{k}}}}}", v)
        return command

    def _handle_cd(self, command: str):
        if command.strip().startswith("cd "):
            target = command.strip()[3:].strip()
            # Use a test command to resolve the path
            code, out, err = self.backend.execute(f"cd {shlex.quote(target)} && pwd", cwd=self.remote_pwd)
            if code == 0 and out.strip():
                self.remote_pwd = out.strip()
                return True, f"Changed directory to: {self.remote_pwd}", ""
            else:
                return False, "", err or "Failed to resolve CD path."
        return None, None, None

    def run_plan(self, plan: List[Dict[str, Any]]):
        self.backend.connect()
        self._init_remote_pwd()
        history = []
        for step_obj in plan:
            if not isinstance(step_obj, dict): continue # Skip malformed steps
            step, raw_command = step_obj.get("step"), step_obj.get("command")
            if not raw_command: continue

            command = self._interpolate_env(raw_command)
            is_cd, out, err = self._handle_cd(command)
            if is_cd is not None:
                log_entry = self.logger.log(step, raw_command, 0 if is_cd else 1, out, err)
                history.append(log_entry)
                if not is_cd: break
                continue

            code, out, err = self.backend.execute(command, cwd=self.remote_pwd)
            log_entry = self.logger.log(step, raw_command, code, out, err)
            history.append(log_entry)
            if code != 0:
                print(f"Halting execution due to failure at step {step}")
                break
        self.backend.close()
        return history

# -------------------------
# Interactive Credential Helper
# -------------------------
def build_ssh_backend_interactive() -> Any:
    print("Enter SSH connection details for remote server.")
    host = input("Host (host.example.com or 1.2.3.4): ").strip()
    user = input(f"User (default: {getpass.getuser()}): ").strip() or getpass.getuser()
    port = int(input("Port (default 22): ").strip() or 22)
    use_paramiko = _HAS_PARAMIKO and input("Use Paramiko or system ssh? [paramiko/system] (default paramiko): ").strip().lower() != "system"
    keypath = input("Private key path (leave blank for password): ").strip() or None
    password = getpass.getpass("Password (for ssh and sudo): ") if not keypath else None
    
    if use_paramiko:
        return ParamikoBackend(host=host, user=user, password=password, key_filename=keypath, port=port)
    else:
        return SystemSSHBackend(host=host, user=user, key_filename=keypath, port=port)

# -------------------------
# Example Driver
# -------------------------
if __name__ == "__main__":
    backend = build_ssh_backend_interactive()
    print("\nPerforming quick connectivity test...")
    try:
        backend.connect()
        code, out, err = backend.execute('echo "test"')
        if code == 0 and out.strip() == "test":
            print("[CONNECTIVITY TEST] SUCCESS")
        else:
            print(f"[CONNECTIVITY TEST] FAILED\nstdout: {out}\nstderr: {err}")
        backend.close()
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
