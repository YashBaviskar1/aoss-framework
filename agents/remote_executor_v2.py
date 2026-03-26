#!/usr/bin/env python3
"""
remote_executor_v2.py

SSH remote executor with two backends.
V3 Fix: Added per-command timeout to prevent hangs on slow apt/systemd
        operations when using get_pty=True. Uses channel-level select()
        so stdout.read() never blocks indefinitely.
"""

import os
import sys
import json
import getpass
import shlex
import select
import subprocess
import re
import time
from typing import Optional, Dict, Any, List

try:
    import paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _HAS_PARAMIKO = False

# ---------------------------------------------------------------------------
# ANSI / control-character stripping
# ---------------------------------------------------------------------------
def clean_ansi_output(text: str) -> str:
    if not text:
        return ""
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    text = ansi_escape.sub('', text)
    text = re.sub(r'[\r\b]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
class Logger:
    def log(self, step, command, return_code, stdout, stderr):
        status = "SUCCESS" if return_code == 0 else "FAILED"
        log_entry = {
            "step": step, "command": command, "status": status,
            "stdout": stdout.strip(), "stderr": stderr.strip(),
        }
        print("=" * 70)
        print(f"STEP: {log_entry['step']} | COMMAND: `{log_entry['command']}` | STATUS: {log_entry['status']}")
        if log_entry['stdout']:
            print("\n--- STDOUT ---\n" + log_entry['stdout'])
        if log_entry['stderr']:
            print("\n--- STDERR ---\n" + log_entry['stderr'])
        print("=" * 70 + "\n")
        return log_entry


# ---------------------------------------------------------------------------
# Paramiko backend  — KEY CHANGE: channel-level read with timeout
# ---------------------------------------------------------------------------
class ParamikoBackend:
    """
    Executes commands over SSH via Paramiko.

    `default_timeout` (seconds) is applied to every command unless the caller
    passes an explicit `timeout` kwarg.  Set it high enough for slow apt
    operations (120 s is usually fine) but low enough to catch true hangs.
    """

    DEFAULT_TIMEOUT = 240   # seconds — override per-command when needed

    def __init__(self, host, user, password=None, key_filename=None,
                 port=22, connect_timeout=10, default_timeout=None):
        if not _HAS_PARAMIKO:
            raise RuntimeError("Paramiko not installed.  pip install paramiko")
        self.host            = host
        self.user            = user
        self.password        = password
        self.key_filename    = key_filename
        self.port            = port
        self.connect_timeout = connect_timeout
        self.default_timeout = default_timeout if default_timeout is not None \
                               else self.DEFAULT_TIMEOUT
        self.client          = None

    # ── connection ──────────────────────────────────────────────────────────
    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kw = dict(hostname=self.host, port=self.port, username=self.user,
                  timeout=self.connect_timeout)
        if self.key_filename:
            kw['key_filename'] = self.key_filename
        else:
            kw['password'] = self.password
        self.client.connect(**kw)

    # ── core execute  — uses select() so we never hang forever ──────────────
    def execute(self, command: str, cwd: str = None, timeout: int = None) -> tuple:
        """
        Returns (exit_code, stdout_str, stderr_str).

        `timeout` overrides the instance default for this single call.
        Raises TimeoutError (caught by RemotePlanRunner) if the command
        does not finish within the allowed window.
        """
        cmd_timeout = timeout if timeout is not None else self.default_timeout
        safe_cmd    = f"cd {shlex.quote(cwd)} && {command}" if cwd else command

        # Open a fresh channel for every command so PTY state never leaks
        transport = self.client.get_transport()
        channel   = transport.open_session()
        channel.get_pty()                    # needed for sudo password injection
        channel.set_combine_stderr(False)    # keep stderr separate
        channel.exec_command(safe_cmd)

        # Inject sudo password if needed
        if command.strip().startswith('sudo') and self.password:
            time.sleep(0.3)                  # tiny pause so the prompt arrives
            channel.sendall(self.password + '\n')

        # ── non-blocking drain loop ──────────────────────────────────────────
        stdout_chunks = []
        stderr_chunks = []
        deadline      = time.time() + cmd_timeout

        while True:
            # select() tells us when data is available (avoids blocking read)
            ready = select.select([channel], [], [], 1.0)

            if ready[0]:
                # recv_ready / recv_stderr_ready before reading avoids empty-read hangs
                if channel.recv_ready():
                    chunk = channel.recv(4096)
                    if chunk:
                        stdout_chunks.append(chunk)
                if channel.recv_stderr_ready():
                    chunk = channel.recv_stderr(4096)
                    if chunk:
                        stderr_chunks.append(chunk)

            if channel.exit_status_ready():
                # Drain any remaining buffered data
                while channel.recv_ready():
                    stdout_chunks.append(channel.recv(4096))
                while channel.recv_stderr_ready():
                    stderr_chunks.append(channel.recv_stderr(4096))
                break

            if time.time() > deadline:
                channel.close()
                raise TimeoutError(
                    f"Command timed out after {cmd_timeout}s: {command[:80]}"
                )

        exit_code = channel.recv_exit_status()
        channel.close()

        raw_out = b"".join(stdout_chunks).decode(errors='replace')
        raw_err = b"".join(stderr_chunks).decode(errors='replace')
        return exit_code, clean_ansi_output(raw_out), clean_ansi_output(raw_err)

    def close(self):
        if self.client:
            self.client.close()


# ---------------------------------------------------------------------------
# System SSH fallback backend (unchanged)
# ---------------------------------------------------------------------------
class SystemSSHBackend:
    def __init__(self, host, user, password=None, key_filename=None,
                 port=22, ssh_binary="ssh"):
        self.host          = host
        self.user          = user
        self.key_filename  = key_filename
        self.port          = port

    def connect(self): pass

    def execute(self, command, cwd=None, timeout=None):
        remote_cmd = f"cd {shlex.quote(cwd)} && {command}" if cwd else command
        ssh_cmd    = ["ssh", "-p", str(self.port), f"{self.user}@{self.host}", remote_cmd]
        if self.key_filename:
            ssh_cmd.insert(1, "-i")
            ssh_cmd.insert(2, self.key_filename)
        try:
            proc = subprocess.run(ssh_cmd, capture_output=True, text=True,
                                  timeout=timeout or 120)
            return proc.returncode, clean_ansi_output(proc.stdout), \
                   clean_ansi_output(proc.stderr)
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"System SSH timed out: {command[:80]}")
        except Exception as e:
            return 1, "", f"Exception running ssh: {e}"

    def close(self): pass


# ---------------------------------------------------------------------------
# Remote Plan Runner
# ---------------------------------------------------------------------------
class RemotePlanRunner:
    """
    Executes a structured plan (list of {step, command} dicts) on the remote
    host.  Each command respects the per-backend default_timeout; individual
    steps can pass an explicit timeout via step_obj['timeout'].
    """

    def __init__(self, backend: ParamikoBackend, env: Dict[str, str] = None):
        self.backend    = backend
        self.logger     = Logger()
        self.remote_pwd = None
        self.env        = env or {}

    def _init_remote_pwd(self):
        code, out, _ = self.backend.execute("pwd", timeout=10)
        self.remote_pwd = out.strip() if code == 0 and out.strip() \
                          else f"/home/{self.backend.user}"
        print(f"[Remote PWD initialized to] {self.remote_pwd}")

    def _interpolate_env(self, command: str) -> str:
        for k, v in self.env.items():
            command = command.replace(f"{{{k}}}", v).replace(f"{{{{{k}}}}}", v)
        return command

    def _handle_cd(self, command: str):
        if command.strip().startswith("cd "):
            target = command.strip()[3:].strip()
            code, out, err = self.backend.execute(
                f"cd {shlex.quote(target)} && pwd",
                cwd=self.remote_pwd, timeout=10
            )
            if code == 0 and out.strip():
                self.remote_pwd = out.strip()
                return True, f"Changed directory to: {self.remote_pwd}", ""
            return False, "", err or "Failed to resolve CD path."
        return None, None, None

    def run_plan(self, plan: List[Dict[str, Any]]) -> List[Dict]:
        print("*" * 60)
        print("EXECUTING PLAN REMOTELY")
        print("*" * 60)
        self.backend.connect()
        self._init_remote_pwd()
        history = []

        for step_obj in plan:
            if not isinstance(step_obj, dict):
                continue
            step        = step_obj.get("step")
            raw_command = step_obj.get("command")
            if not raw_command:
                continue

            # Per-step timeout override (optional field in plan JSON)
            step_timeout = step_obj.get("timeout", None)
            command      = self._interpolate_env(raw_command)

            # Handle cd specially (no real execution needed)
            is_cd, out, err = self._handle_cd(command)
            if is_cd is not None:
                log_entry = self.logger.log(step, raw_command,
                                            0 if is_cd else 1, out, err)
                history.append(log_entry)
                if not is_cd:
                    break
                continue

            # Normal command execution with timeout guard
            try:
                code, out, err = self.backend.execute(
                    command, cwd=self.remote_pwd, timeout=step_timeout
                )
            except TimeoutError as te:
                print(f"\n[TIMEOUT] Step {step} exceeded time limit: {te}")
                log_entry = self.logger.log(step, raw_command, 1,
                                            "", f"TIMEOUT: {te}")
                log_entry["status"] = "TIMEOUT"
                history.append(log_entry)
                break

            log_entry = self.logger.log(step, raw_command, code, out, err)
            history.append(log_entry)

            if code != 0:
                print(f"Halting execution: failure at step {step}")
                break

        self.backend.close()
        return history


# ---------------------------------------------------------------------------
# Interactive helper (unchanged)
# ---------------------------------------------------------------------------
def build_ssh_backend_interactive() -> Any:
    print("Enter SSH connection details for remote server.")
    host     = input("Host: ").strip()
    user     = input(f"User (default: {getpass.getuser()}): ").strip() or getpass.getuser()
    port     = int(input("Port (default 22): ").strip() or 22)
    use_par  = _HAS_PARAMIKO and \
               input("Use Paramiko or system ssh? [paramiko/system] (default paramiko): "
                     ).strip().lower() != "system"
    keypath  = input("Private key path (blank = password): ").strip() or None
    password = getpass.getpass("Password: ") if not keypath else None

    if use_par:
        return ParamikoBackend(host=host, user=user, password=password,
                               key_filename=keypath, port=port)
    return SystemSSHBackend(host=host, user=user, key_filename=keypath, port=port)


# ---------------------------------------------------------------------------
# Quick connectivity test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    backend = build_ssh_backend_interactive()
    print("\nPerforming connectivity test...")
    try:
        backend.connect()
        code, out, err = backend.execute('echo "test"', timeout=10)
        if code == 0 and "test" in out:
            print("[CONNECTIVITY TEST] SUCCESS")
        else:
            print(f"[CONNECTIVITY TEST] FAILED\nstdout: {out}\nstderr: {err}")
        backend.close()
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)