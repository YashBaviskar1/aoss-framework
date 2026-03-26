import paramiko
import time
import io

class RemoteExecutor:
    def __init__(self, host, user, key_path=None, password=None):
        self.host = host
        self.user = user
        self.key_path = key_path
        self.password = password
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connect_kwargs = {
            "hostname": self.host,
            "username": self.user,
            "timeout": 10
        }
        
        if self.key_path:
            connect_kwargs["key_filename"] = self.key_path
        if self.password:
            connect_kwargs["password"] = self.password
            
        self.client.connect(**connect_kwargs)

    def execute_step(self, command, timeout=30):
        if not self.client:
            raise Exception("Client not connected")

        MAX_OUTPUT = 180  # Truncate output to prevent memory bloat

        try:
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True, timeout=timeout)
            
            # Set channel timeout so reads don't block forever
            stdout.channel.settimeout(timeout)
            
            exit_status = stdout.channel.recv_exit_status()
            
            out_str = stdout.read().decode('utf-8', errors='replace')
            err_str = stderr.read().decode('utf-8', errors='replace')
            
            # Truncate if too large
            if len(out_str) > MAX_OUTPUT:
                out_str = out_str[:MAX_OUTPUT] + "\n... (output truncated)"
            if len(err_str) > MAX_OUTPUT:
                err_str = err_str[:MAX_OUTPUT] + "\n... (output truncated)"
            
            return {
                "command": command,
                "exit_code": exit_status,
                "stdout": out_str,
                "stderr": err_str,
                "status": "Success" if exit_status == 0 else "Failed"
            }
        except Exception as e:
            return {
                "command": command,
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Command timed out or failed: {str(e)}",
                "status": "Failed"
            }

    def close(self):
        if self.client:
            self.client.close()
