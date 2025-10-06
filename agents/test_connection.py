#!/usr/bin/env python3
"""
test.py
Simple SSH connectivity tester using paramiko (preferred) or system ssh.
Prompts user for credentials, attempts to connect, and verifies via 'echo test'.
"""

import getpass
import shlex
import subprocess
import sys

try:
    import paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _HAS_PARAMIKO = False


class ParamikoBackend:
    def __init__(self, host, user, password=None, key_filename=None, port=22, timeout=10):
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
        connect_kwargs = dict(hostname=self.host, username=self.user, port=self.port, timeout=self.timeout)
        if self.key_filename:
            connect_kwargs['key_filename'] = self.key_filename
        elif self.password:
            connect_kwargs['password'] = self.password
        self.client.connect(**connect_kwargs)

    def execute(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        out, err = stdout.read().decode(), stderr.read().decode()
        code = stdout.channel.recv_exit_status()
        return code, out.strip(), err.strip()

    def close(self):
        if self.client:
            self.client.close()


class SystemSSHBackend:
    def __init__(self, host, user, key_filename=None, port=22):
        self.host = host
        self.user = user
        self.key_filename = key_filename
        self.port = port

    def connect(self):
        # just a check if host reachable via ssh
        cmd = ["ssh", "-p", str(self.port), f"{self.user}@{self.host}", "echo connected"]
        if self.key_filename:
            cmd.insert(1, "-i")
            cmd.insert(2, self.key_filename)
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    def execute(self, command):
        cmd = ["ssh", "-p", str(self.port), f"{self.user}@{self.host}", command]
        if self.key_filename:
            cmd.insert(1, "-i")
            cmd.insert(2, self.key_filename)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def close(self):
        pass


def build_backend():
    print("=== SSH Connection Test ===")
    host = input("Host (e.g. 1.2.3.4): ").strip()
    user = input("User (default: current): ").strip() or getpass.getuser()
    port = int(input("Port (default 22): ").strip() or 22)

    if _HAS_PARAMIKO:
        choice = input("Use Paramiko or system ssh? [paramiko/system] (default: paramiko): ").strip().lower()
        use_paramiko = choice != "system"
    else:
        print("Paramiko not installed — using system ssh.")
        use_paramiko = False

    keypath = input("Private key path (leave blank for password): ").strip() or None
    password = None
    if not keypath:
        password = getpass.getpass("Password (leave blank if using ssh-agent): ")

    if use_paramiko:
        return ParamikoBackend(host, user, password=password, key_filename=keypath, port=port)
    else:
        return SystemSSHBackend(host, user, key_filename=keypath, port=port)


def main():
    backend = build_backend()

    print("\nConnecting...")
    try:
        backend.connect()
        print("[+] Connection established.")
    except Exception as e:
        print(f"[x] Connection failed: {e}")
        sys.exit(1)

    print("Running echo test...")
    try:
        code, out, err = backend.execute('echo "test"')
        if code == 0 and out.strip() == "test":
            print("[✓] Connectivity test successful.")
        else:
            print("[x] Connectivity test failed.")
            print("stdout:", out)
            print("stderr:", err)
    except Exception as e:
        print(f"[x] Failed to execute test command: {e}")

    backend.close()


if __name__ == "__main__":
    main()
