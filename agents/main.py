from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Load API key
load_dotenv()

app = FastAPI(title="Multi-Agent Execution API")

# Init LLM (Groq)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("API_KEY")
)

# Prompt template
template = """
You are an execuation agent of a Multi Agent System which handles the terminal of a server and has access to it's terminal, 
you will respond in JSON format only.

You are given a Task, and to execuate that tasks all the terminal commands and make sure to add -y flag when needed 

Example of the input and the output you have to provide :
Input : 
{{
Question : "update system"
}}

Your Output : 
{{
Commands = ['sudo apt update', 'sudo apt upgrade']
}}


Question Query :
{{
Question : {question}
}}


"""

prompt = PromptTemplate.from_template(template)


# Request schema
class Query(BaseModel):
    question: str
    execute: bool = False  # whether to actually run in WSL


# Run commands inside WSL
import subprocess

def run_commands(commands):
    results = []
    for cmd in commands:
        print(f"\n💻 Running: {cmd}")  # Show in your FastAPI console
        result = subprocess.run(
            ["wsl", "bash", "-c", f"cd /home/ygb && {cmd}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Mirror output live to your console
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
        
        status = "✅ Success" if result.returncode == 0 else "❌ Failed"
        results.append({
            "command": cmd,
            "status": status,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        })
    return results

    results = []
    for cmd in commands:
        result = subprocess.run(
            ["wsl", "bash", "-c", f"cd /home/ygb && {cmd}"],  # force working dir
            capture_output=True,
            text=True
        )
        status = "✅ Success" if result.returncode == 0 else "❌ Failed"
        results.append({
            "command": cmd,
            "status": status,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        })
    return results


@app.post("/agent")
def agent(query: Query):
    # Ask LLM to convert query -> commands
    response = llm.invoke(prompt.format(question=query.question))

    try:
        # Parse JSON from LLM response
        commands = eval(response.content)["Commands"]
        print(commands)
    except Exception:
        return {
            "error": "Model returned invalid JSON",
            "raw_response": response.content
        }

    if query.execute:
        return {
            "plan": commands,
            "results": run_commands(commands)
        }
    else:
        return {
            "plan": commands
        }
