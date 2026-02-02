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

    def execute_step(self, command):
        if not self.client:
            raise Exception("Client not connected")

        # use get_pty=True to handle sudo if needed (though we rely on valid sudoers usually)
        # and to capture combined output better
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
        
        # Determine success roughly by exit status
        exit_status = stdout.channel.recv_exit_status()
        
        out_str = stdout.read().decode('utf-8', errors='replace')
        err_str = stderr.read().decode('utf-8', errors='replace')
        
        return {
            "command": command,
            "exit_code": exit_status,
            "stdout": out_str,
            "stderr": err_str,
            "status": "Success" if exit_status == 0 else "Failed"
        }

    def close(self):
        if self.client:
            self.client.close()
