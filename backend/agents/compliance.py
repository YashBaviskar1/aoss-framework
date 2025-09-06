import yaml
import os

class ComplianceChecker:
    def __init__(self, policy_path: str):
        with open(policy_path, "r") as f:
            self.rules = yaml.safe_load(f)

    def check_command(self, command: str):
        # If command starts with any forbidden keyword → block
        for bad in self.rules.get("forbidden", []):
            if bad in command:
                return {"command": command, "status": "❌ Blocked", "reason": f"Forbidden by rule: {bad}"}

        # If command starts with an allowed keyword → allow
        for good in self.rules.get("allowed", []):
            if command.strip().startswith(good):
                return {"command": command, "status": "✅ Allowed"}

        # Default → unknown → block
        return {"command": command, "status": "⚠️ Unknown", "reason": "Not in allowed list"}
