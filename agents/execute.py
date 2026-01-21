import subprocess
import json
import sys

def run_commands(commands):
    results = []

    for cmd in commands:
        print(f"\n$ {cmd}")  # Show command being executed (like a terminal)
        try:
            # Run command in WSL shell and stream output directly
            process = subprocess.Popen(
                ["wsl", "bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_lines = []
            stderr_lines = []

            # Stream output line by line to console (real-time)
            for line in process.stdout:
                print(line, end="")   # Print live to WSL terminal
                stdout_lines.append(line)

            for line in process.stderr:
                print(line, end="", file=sys.stderr)
                stderr_lines.append(line)

            process.wait()

            results.append({
                "command": cmd,
                "status": "✅ Success" if process.returncode == 0 else "❌ Failed",
                "stdout": "".join(stdout_lines),
                "stderr": "".join(stderr_lines)
            })

        except Exception as e:
            results.append({
                "command": cmd,
                "status": "❌ Error",
                "stdout": "",
                "stderr": str(e)
            })

    return results


if __name__ == "__main__":
    # Example: You can pass JSON with commands list
    commands = [
        "ls -la",
        "pwd",
        "echo 'Hello from WSL!'"
    ]

    results = run_commands(commands)

    # Also return JSON (for agents)
    print("\n\n--- JSON OUTPUT ---")
    print(json.dumps({"plan": commands, "results": results}, indent=2))
