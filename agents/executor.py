import os
import json
import subprocess
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class Logger:
    """Logs command execution, returning a structured dictionary for history."""
    def log(self, step, command, return_code, stdout, stderr):
        status = "SUCCESS" if return_code == 0 else "FAILED"
        log_entry = {
            "step": step, "command": command, "status": status,
            "stdout": stdout.strip(), "stderr": stderr.strip()
        }
        print("="*70)
        print(f"STEP: {log_entry['step']} | COMMAND: `{log_entry['command']}` | STATUS: {log_entry['status']}")
        if log_entry['stdout']: print("\n--- STDOUT ---\n" + log_entry['stdout'])
        if log_entry['stderr']: print("\n--- STDERR ---\n" + log_entry['stderr'])
        print("="*70 + "\n")
        return log_entry

class ExecutorAgent:
    """Executes a plan locally or remotely, using RAG for task decomposition."""
    def __init__(self, plan_json, llm, retriever, remote_runner=None):
        self.plan = plan_json.get('plan', [])
        self.execution_state = plan_json.get('env', {})
        self.retriever = retriever
        self.logger = Logger()
        self.llm = llm
        self.history = []
        self.remote_runner = remote_runner

        decomposer_system_prompt = """
        You are an expert SRE who translates a high-level goal into a sequence of executable shell commands.
        Based on the execution history, documentation, and environment, provide ONLY the shell commands to achieve the task.
        **EXECUTION HISTORY:**
        {history}
        **RELEVANT DOCUMENTATION:**
        {context}
        **CURRENT ENVIRONMENT:**
        {env}
        **HIGH-LEVEL TASK:**
        {task}
        **SHELL COMMANDS:**
        """
        self.decomposer_prompt = ChatPromptTemplate.from_template(decomposer_system_prompt)
        self.decomposer_chain = self.decomposer_prompt | self.llm | StrOutputParser()

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs) if docs else "No relevant documentation found."
    
    def _format_history(self):
        return json.dumps(self.history, indent=2) if self.history else "No commands have been executed yet."

    def _is_complex_step(self, command):
        complex_keywords = ["configure", "set up", "verify", "create a file", "ensure", "deploy"]
        return any(keyword in command.lower() for keyword in complex_keywords)

    def _decompose_task(self, task):
        print(f"--- Decomposing complex task: '{task}' ---")
        task_context = self._format_docs(self.retriever.invoke(task))
        env_str = json.dumps(self.execution_state, indent=2)
        history_str = self._format_history()
        sub_commands_str = self.decomposer_chain.invoke({
            "task": task, "context": task_context, "env": env_str, "history": history_str
        })
        return [cmd.strip() for cmd in sub_commands_str.split('\n') if cmd.strip()]

    def _execute_local_command(self, command, step_id):
        """Executes a command on the local machine."""
        for key, value in self.execution_state.items():
            command = command.replace(f"{{{key}}}", value).replace(f"'{key}'", value)
        
        try:
            working_dir = self.execution_state.get('PWD', os.getcwd())
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=False, cwd=working_dir)
            
            if command.strip().startswith("cd "):
                new_dir = command.strip().split(" ", 1)[1]
                # A simple way to handle local directory changes
                if os.path.isdir(new_dir): self.execution_state['PWD'] = os.path.abspath(new_dir)

            log_entry = self.logger.log(step_id, command, process.returncode, process.stdout, process.stderr)
            self.history.append(log_entry)
            return log_entry['status'] == 'SUCCESS'
        
        except Exception as e:
            log_entry = self.logger.log(step_id, command, 1, "", f"Executor failed with Python exception: {e}")
            self.history.append(log_entry)
            return False

    def execute_plan(self):
        """
        Orchestrates plan execution. Delegates to the RemotePlanRunner if one is provided,
        otherwise executes the plan locally.
        """
        if self.remote_runner:
            # --- REMOTE EXECUTION ---
            print("\n" + "*"*20 + " EXECUTING PLAN REMOTELY " + "*"*20)
            # The RemotePlanRunner handles the entire loop, logging, and connection.
            self.history = self.remote_runner.run_plan(self.plan)
        else:
            # --- LOCAL EXECUTION ---
            print("\n" + "*"*20 + " EXECUTING PLAN LOCALLY " + "*"*20)
            self.execution_state['PWD'] = os.getcwd()

            for step_obj in self.plan:
                if not isinstance(step_obj, dict): continue
                command, step_id = step_obj.get('command'), str(step_obj.get('step'))
                if not command: continue

                if not self._is_complex_step(command):
                    if not self._execute_local_command(command, step_id):
                        print(f"Execution halted due to failure at step {step_id}.")
                        break
                else:
                    sub_commands = self._decompose_task(command)
                    halt = False
                    for i, sub_cmd in enumerate(sub_commands, 1):
                        if not self._execute_local_command(sub_cmd, f"{step_id}.{i}"):
                            print(f"Execution halted at sub-step {step_id}.{i}.")
                            halt = True
                            break
                    if halt: break
        
        print("*"*20 + " PLAN EXECUTION COMPLETE " + "*"*20)

