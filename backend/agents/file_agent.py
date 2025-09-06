# backend/agents/file_agent.py
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from .compliance import ComplianceChecker
from .knowledge_base import KnowledgeBase

class FileAgent:
    def __init__(self, policy_file="backend/policies/file_agent.yaml"):
        # ✅ Use Ollama (make sure you have the model pulled, e.g. `ollama pull llama3.1:8b`)
        self.llm = ChatOllama(
            model="llama3.1:8b",   # or whichever you’ve pulled locally
            temperature=0,
        )

        self.compliance = ComplianceChecker(policy_file)
        self.kb = KnowledgeBase()

        self.prompt = PromptTemplate.from_template("""
        You are a File Management Agent. Convert the user query into safe Linux commands.
        Only use simple file operations (ls, pwd, cat, head, tail).
        Respond in JSON strictly.

        Example:
        Input: "show files"
        Output: {{ "Commands": ["ls -la"] }}

        Input:
        {{Question: {question}}}
        """)

    def plan(self, query: str):
        response = self.llm.invoke(self.prompt.format(question=query))

        try:
            commands = eval(response.content)["Commands"]
        except Exception:
            return {
                "error": "Invalid LLM response",
                "raw": response.content
            }

        # Compliance check
        compliance_results = [self.compliance.check_command(cmd) for cmd in commands]

        safe_commands = [r["command"] for r in compliance_results if r["status"] == "✅ Allowed"]

        return {
            "user_query": query,
            "llm_plan": commands,
            "compliance_results": compliance_results,
            "final_plan": safe_commands
        }
