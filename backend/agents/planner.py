import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys
# Ensure backend module is found if running from sub-dir, although generic import usually works if path set
sys.path.append("..") 
from compliance.compliance_service import ComplianceService

class PlannerAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in env")

        # --- AGENT PERSONAS (The "Smart" Part) ---
        self.prompts = {
            "general": """
                You are an expert SRE and System Administrator. 
                Convert the request into a general system execution plan.
                Focus on standard Linux utilities and safe operations.
            """,
            "network": """
                You are a Senior Network Engineer Agent.
                Focus specifically on networking, firewalls, DNS, and connectivity.
                Prefer tools like `ip`, `netstat`, `ss`, `dig`, `ufw`, `iptables`, and `curl`.
                If debugging, always check connectivity first.
            """,
            "database": """
                You are a Database Administrator (DBA) Agent.
                Focus on data integrity, backups, and safe SQL execution.
                If the user asks to touch a DB, ensure services are running first.
                Assume standard paths for PostgreSQL/MySQL unless specified.
            """,
            "security": """
                You are a SecOps Specialist.
                Focus on hardening, auditing, and permission checks.
                Prioritize checking logs (`/var/log/auth.log`), file permissions, and active users.
            """
        }

        self.base_instruction = """
        **Output Format:**
        Provide ONLY a JSON object. No markdown, no explanations.
        
        The JSON must have this structure:

        {{
          "plan": [
            {{
              "step": 1,
              "command": "sudo apt update",
              "description": "Update package lists"
            }}
          ]
        }}

        **Rules:**
        1. Target system: Ubuntu/Debian.
        2. Use `-y` for apt/dnf.
        3. Break complex tasks into steps.
        4. Use `sudo` if required.
        
        **User Query:**
        {query}
        """

    def generate_plan(self, query: str, model: str = "llama-3.3-70b-versatile", agent_type: str = "general", server_context: dict = {}):
        try:
            print(f"Planning | Model: {model} | Agent: {agent_type}")
            
            # 1. Select the Persona
            persona_intro = self.prompts.get(agent_type, self.prompts["general"])
            
            # 1.5 Fetch Compliance Context
            compliance_rules = ComplianceService.get_compliance_context()
            
            # 1.6 Environment Context (The "Shared Memory")
            env_context_str = ""
            if server_context:
                env_context_str = f"""
                **Known Environment State (Use this to avoid re-work):**
                - Installed Packages: {server_context.get('installed', [])}
                - Key Directories: {server_context.get('paths', {})}
                - Active Repos: {server_context.get('repos', [])}
                - Opened Ports: {server_context.get('ports', [])}
                - Last Working Directory: {server_context.get('cwd', '/root')}
                """

            # Use placeholders {{var}} so LangChain treats them as variables to be filled by invoke
            full_system_prompt = f"{persona_intro}\n\n{{compliance_rules}}\n\n{{env_context}}\n\n{self.base_instruction}"

            # 2. Instantiate LLM dynamically based on user choice
            llm = ChatGroq(
                model=model,
                api_key=self.api_key,
                temperature=0.1
            )

            # 3. Build Chain
            prompt_template = ChatPromptTemplate.from_messages([("system", full_system_prompt)])
            chain = prompt_template | llm | StrOutputParser()

            # 4. Invoke with ALL variables
            # DEBUG LOGS
            print(f"DEBUG: Compliance Type: {type(compliance_rules)}")
            # print(f"DEBUG: Full Prompt Template: {full_system_prompt}") 
            
            result_str = chain.invoke({
                "query": query,
                "compliance_rules": str(compliance_rules), # Ensure string
                "env_context": env_context_str
            })
            
            print(f"DEBUG: Raw Planner Output: '{result_str}'")
            
            if not result_str:
                return {"error": "LLM returned empty response"}

            # 5. Parse JSON
            clean_str = result_str.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            elif clean_str.startswith("```"):
                clean_str = clean_str[3:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            
            clean_str = clean_str.strip()
            return json.loads(clean_str)

        except Exception as e:
            print(f"Planning Error: {e}")
            return {"error": str(e)}

    # ... generate_fix ...

    def update_knowledge_base(self, current_context: dict, execution_logs: list, model: str):
        """
        Analyzes execution results to update the persistent server state.
        """
        updater_system_prompt = """
        You are a Knowledge Base Manager.
        Analyze the executed commands and their results.
        Update the JSON environment state.

        Input JSON State:
        {current_state}

        Execution Logs:
        {logs}

        Tasks:
        1. Add newly installed packages to 'installed'.
        2. Update 'paths' if a directory was created or we cd'ed into it.
        3. Add new repos to 'repos' (name and path).
        4. Add opened ports to 'ports'.
        5. Update 'cwd' if changed.

        Output:
        ONLY the updated JSON object.
        """

        try:
            print(f"🧠 Updating Knowledge Base | Model: {model}")
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", updater_system_prompt),
                ("user", "Update the state based on these logs.")
            ])
            
            llm = ChatGroq(model=model, api_key=self.api_key, temperature=0.1)
            chain = prompt_template | llm | StrOutputParser()
            
            updated_state_str = chain.invoke({
                "current_state": json.dumps(current_context or {}, indent=2),
                "logs": json.dumps(execution_logs, indent=2)
            })
            
            # Clean JSON
            import re
            json_match = re.search(r"\{.*\}", updated_state_str, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return current_context

        except Exception as e:
            print(f"Knowledge Update Error: {e}")
            return current_context

    def generate_fix(self, original_query: str, failed_command: str, error_output: str, model: str):
        """
        Analyzes a failure and generates a remediation plan.
        """
        recovery_system_prompt = """
        You are a Self-Healing SRE Agent. A command failed during execution.
        Your goal is to provide a JSON plan to FIX the error and complete the objective.
        
        Analyze the error:
        1. If 'command not found': Suggest installing the package OR using a standard alternative (e.g., 'ss' instead of 'netstat').
        2. If 'permission denied': Suggest chmod or sudo (if safe).
        3. If 'lock file': Suggest waiting or removing lock (carefully).
        4. If 'already exists' (for git clone, mkdir, etc.): Suggest removing the existing target (`rm -rf`) OR skipping the creation step.
        5. If 'port in use': Suggest finding the PID and killing it, or using a different port.

        CRITICAL: Do NOT just repeat the same command that failed. You must change the state of the system (e.g. install something, delete something) before retrying.
        
        Return a JSON object with a "plan" list containing the fix steps AND the retry step.
        """
        
        # Context for the LLM
        user_input = f"""
        **Original Goal:** {original_query}
        **Failed Command:** {failed_command}
        **Error Output:** {error_output}
        
        Provide the fix steps.
        """

        try:
            print(f"🏥 Healing | Model: {model}")
            
            # Specific Output Format for Fixes (No "{query}" placeholder to avoid confusion)
            fix_output_format = """
            **Output Format:**
            Provide ONLY a JSON object.
            
            The JSON must have this structure:
            {{
              "plan": [
                {{
                  "step": 1,
                  "command": "rm -rf Streamlit-App",
                  "description": "Remove existing directory to allow fresh clone"
                }},
                {{
                  "step": 2,
                  "command": "git clone ...",
                  "description": "Retry cloning"
                }}
              ]
            }}
            
            **Rules:**
            1. ONLY provide steps to fix the error and the retry step.
            2. Do NOT re-plan successful steps (e.g. do not apt update again if it worked).
            3. If a file/folder exists and causes error, DELETE it or MOVE it.
            """
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", recovery_system_prompt + "\n\n" + fix_output_format),
                ("user", user_input)
            ])
            
            # No "query" variable needed for this specific template setup since we removed the placeholder
            # But LangChain might complain if we pass variables not in template, or vice versa? 
            # We are constructing template strings directly.
            
            llm = ChatGroq(model=model, api_key=self.api_key, temperature=0.1)
            chain = prompt_template | llm | StrOutputParser()
            
            # invoke with empty dict if no variables, or just pass original_query if we want to log it
            result_str = chain.invoke({}) 
            print(f"DEBUG: Healing Output: {result_str}")
            
            # Robust JSON extraction
            import re
            json_match = re.search(r"\{.*\}", result_str, re.DOTALL)
            if json_match:
                clean_str = json_match.group(0)
                return json.loads(clean_str)
            else:
                 # Fallback/Empty
                return {"plan": []}

        except Exception as e:
            print(f"Recovery Planning Error: {e}")
            return {"plan": []}

    def summarize_execution(self, query: str, results: list, model: str):
        """
        Summarizes the execution results in natural language.
        """
        summary_system_prompt = """
        You are an SRE Assistant. 
        Analyze the command execution logs and their output. 
        Provide a concise, human-readable summary of what was found or achieved.
        Explain the technical output in simple terms (e.g., "The web server (nginx) is running on port 80").
        
        Format:
        Markdown. Keep it brief. 
        """
        
        
        # Serialize results 
        results_str = json.dumps(results, indent=2)
        
        try:
            print(f"📝 Summarizing | Model: {model}")
            
            # Use placeholders for LangChain to safely insert the content
            user_template = """
            **Original Query:** {original_query}
            **Execution Logs:**
            {execution_logs}
            
            **Summary:**
            """
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", summary_system_prompt),
                ("user", user_template)
            ])
            
            llm = ChatGroq(model=model, api_key=self.api_key, temperature=0.1)
            chain = prompt_template | llm | StrOutputParser()
            
            # Pass the data as variables so brackets in JSON aren't interpreted as templates
            summary = chain.invoke({
                "original_query": query, 
                "execution_logs": results_str
            })
            return summary.strip()

        except Exception as e:
            print(f"Summarization Error: {e}")
            return "Could not generate summary."
