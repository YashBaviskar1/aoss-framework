import os
import json
import sys
import argparse
from dotenv import load_dotenv

# AOSS Core Components
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from planner import PlannerAgent
from executor import ExecutorAgent
from remote_executor import ParamikoBackend, RemotePlanRunner

# --- INSTRUCTIONS ---
# 1. Run `context_maker.py`
# 2. Set up your .env file (GROQ_API_KEY, SSH_HOST, etc.)
# 3. Run this script with a mode:
#    python test_cases_comparator.py --mode aoss
#    python test_cases_comparator.py --mode monolithic
# --- --- --- --- ---

load_dotenv()

# --- Test Case Definitions ---
# (Copied from your test_cases.py)
TEST_CASES = [
    {
        "id": "FT-001", "os": "Ubuntu", "query": "install htop",
        "verification_command": "htop --version", "expected_stdout": None,
        "cleanup_commands": ["sudo apt-get remove -y htop"]
    },
    {
        "id": "FT-003", "os": "Ubuntu", "query": "I need nginx.",
        "verification_command": "systemctl is-active nginx", "expected_stdout": "active",
        "cleanup_commands": ["sudo systemctl stop nginx", "sudo apt-get remove -y nginx"]
    },
    {
        "id": "FT-004", "os": "Ubuntu", "query": "check the disk space.",
        "verification_command": "df -h", "expected_stdout": "/",
        "cleanup_commands": []
    },
    {
        "id": "FT-006", "os": "Ubuntu", "query": "create a file at /tmp/aoss-test.txt with the content 'hello world'",
        "verification_command": "cat /tmp/aoss-test.txt", "expected_stdout": "hello world",
        "cleanup_commands": ["rm /tmp/aoss-test.txt"]
    },
    {
        "id": "FT-010", "os": "Ubuntu", "query": "run 'foobar123'",
        "expect_plan_failure": True, "verification_command": "echo 'Checking for graceful failure'",
        "expected_stdout": None, "cleanup_commands": []
    },
    {
        "id": "FT-013", "os": "Ubuntu", "query": "deploy my streamlit app from `https://github.com/streamlit/streamlit-example.git`",
        "verification_command": "curl -s -L http://localhost:8501 | grep -i 'Streamlit'", "expected_stdout": "Streamlit",
        "cleanup_commands": ["pkill -f streamlit", "rm -rf streamlit-example"]
    },
    {
        "id": "FT-014", "os": "Ubuntu", "query": "First, run a simple python web server on port 8000 in the background. Second, configure nginx as a reverse proxy to it.",
        "verification_command": "curl -s http://localhost | grep -i 'Directory listing'", "expected_stdout": "Directory listing",
        "cleanup_commands": [
            "pkill -f 'python3 -m http.server'", "sudo rm -f /etc/nginx/sites-available/aoss_proxy.conf",
            "sudo rm -f /etc/nginx/sites-enabled/aoss_proxy.conf", "sudo systemctl reload nginx"
        ]
    },
]

# --- Prompt for Monolithic Agent ---
MONOLITHIC_PROMPT_TEMPLATE = """
You are an expert SRE and System Administrator. Given a task, provide a JSON list of the exact, step-by-step shell commands required to achieve it.
Assume the server OS is {os}.
Respond ONLY with a valid JSON list of strings, with no additional text, explanations, or markdown formatting.

Task: {query}

JSON list of commands:
"""

# --- Component Initialization ---
def initialize_aoss_components():
    """Initializes components for the AOSS-RAG system."""
    print("--- Initializing AOSS-RAG Components (Planner, Executor, RAG) ---")
    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
            model_kwargs={'device': 'cpu'}
        )
        vectorstore = Chroma(
            persist_directory=os.getenv("PERSIST_DIRECTORY", "rag_store"),
            embedding_function=embedding_model
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        planner_llm = ChatGroq(model=os.getenv("PLANNER_LLM", "llama-3.1-8b-instant"), temperature=0)
        executor_llm = ChatGroq(model=os.getenv("EXECUTOR_LLM", "llama-3.3-70b-versatile"), temperature=0)
        print("AOSS-RAG Components initialized successfully.\n")
        return planner_llm, executor_llm, retriever
    except Exception as e:
        print(f"Error initializing AOSS components: {e}")
        return None, None, None

def initialize_monolithic_components():
    """Initializes the single, large LLM for the Monolithic system."""
    print("--- Initializing Monolithic Component (llama-3.3-70b-versatile) ---")
    try:
        monolithic_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        print("Monolithic Component initialized successfully.\n")
        return monolithic_llm
    except Exception as e:
        print(f"Error initializing Monolithic LLM: {e}")
        return None

def initialize_backend():
    """Initializes the Paramiko SSH backend from .env variables."""
    print("--- Initializing Remote Server Connection ---")
    host, user = os.getenv("SSH_HOST"), os.getenv("SSH_USER")
    password, key_path = os.getenv("SSH_PASS"), os.getenv("SSH_KEY_PATH")
    if not host or not user or not (password or key_path):
        print("Error: SSH_HOST, SSH_USER, and (SSH_PASS or SSH_KEY_PATH) must be set in .env")
        return None
    try:
        backend = ParamikoBackend(host=host, user=user, password=password, key_filename=key_path)
        print(f"Connecting to {user}@{host}...")
        backend.connect()
        code, out, err = backend.execute('echo "AOSS Test Connection OK"')
        if code == 0 and "OK" in out:
            print("[SUCCESS] Remote connection verified.\n")
            return backend
        else:
            print(f"[FAILED] Could not verify remote connection. stderr: {err}")
            return None
    except Exception as e:
        print(f"Failed to set up remote connection: {e}")
        return None

# --- Test Runner ---
def run_test_suite(mode):
    """
    Main function to run the defined test cases against the specified agent architecture.
    """
    # --- 1. Initialize Components ---
    planner_llm, executor_llm, retriever = None, None, None
    monolithic_llm = None

    if mode == 'aoss':
        planner_llm, executor_llm, retriever = initialize_aoss_components()
        if not planner_llm: sys.exit(1)
    elif mode == 'monolithic':
        monolithic_llm = initialize_monolithic_components()
        if not monolithic_llm: sys.exit(1)

    backend = initialize_backend()
    if not backend: sys.exit(1)
        
    results = {"passed": 0, "failed": 0, "skipped": 0}

    # --- 2. Iterate Through Test Cases ---
    for test in TEST_CASES:
        print("\n" + "="*80)
        print(f"RUNNING TEST: [{test['id']}] - MODE: {mode.upper()} - \"{test['query']}\"")
        print("="*80)
        
        plan_failed = False
        execution_history = []
        
        try:
            # --- 3.A. AOSS-RAG: Plan and Execute ---
            if mode == 'aoss':
                print("--- 1. Generating Plan (AOSS-RAG) ---")
                user_query_with_context = f"Server OS: {test['os']}\n\nTask: {test['query']}"
                planner = PlannerAgent(llm=planner_llm, retriever=retriever)
                plan = planner.generate_plan(user_query_with_context)
                if not plan:
                    print("[FAIL] AOSS-RAG Planner did not return a valid plan.")
                    results["failed"] += 1; continue
                
                print("--- 2. Executing Plan (AOSS-RAG) ---")
                test_backend = ParamikoBackend(host=os.getenv("SSH_HOST"), user=os.getenv("SSH_USER"), password=os.getenv("SSH_PASS"), key_filename=os.getenv("SSH_KEY_PATH"))
                remote_runner = RemotePlanRunner(backend=test_backend, env=plan.get('env', {}))
                executor = ExecutorAgent(plan_json=plan, llm=executor_llm, retriever=retriever, remote_runner=remote_runner)
                executor.execute_plan()
                execution_history = executor.history

            # --- 3.B. MONOLITHIC: Plan and Execute ---
            elif mode == 'monolithic':
                print("--- 1. Generating Plan (Monolithic) ---")
                prompt = MONOLITHIC_PROMPT_TEMPLATE.format(os=test['os'], query=test['query'])
                try:
                    response_str = monolithic_llm.invoke(prompt).content
                    commands_list = json.loads(response_str)
                    # Convert simple list to the format RemotePlanRunner expects
                    plan_dict = {"env": {}, "plan": [{"step": i+1, "command": cmd} for i, cmd in enumerate(commands_list)]}
                    print(json.dumps(plan_dict, indent=2))
                except Exception as e:
                    print(f"[FAIL] Monolithic Planner did not return valid JSON. Error: {e}")
                    print(f"Raw Output: {response_str}")
                    results["failed"] += 1; continue
                
                print("--- 2. Executing Plan (Monolithic) ---")
                test_backend = ParamikoBackend(host=os.getenv("SSH_HOST"), user=os.getenv("SSH_USER"), password=os.getenv("SSH_PASS"), key_filename=os.getenv("SSH_KEY_PATH"))
                remote_runner = RemotePlanRunner(backend=test_backend, env=plan_dict.get('env', {}))
                # The Monolithic system has no complex executor, so we call RemotePlanRunner directly
                execution_history = remote_runner.run_plan(plan_dict['plan'])

            # --- 4. Check for Execution Failure ---
            if any(step['status'] == 'FAILED' for step in execution_history):
                plan_failed = True

            if test.get("expect_plan_failure"):
                if plan_failed:
                    print(f"\n[PASS] Test {test['id']} failed as expected.")
                    results["passed"] += 1
                else:
                    print(f"\n[FAIL] Test {test['id']} was expected to fail, but it succeeded.")
                    results["failed"] += 1
                continue
            elif plan_failed:
                print(f"\n[FAIL] Test {test['id']} failed during execution.")
                results["failed"] += 1
                continue

            # --- 5. Verify Outcome ---
            print("--- 3. Verifying Outcome ---")
            code, out, err = backend.execute(test['verification_command'])
            if code != 0:
                print(f"[FAIL] Verification command failed (Code {code}). STDOUT: {out}\nSTDERR: {err}")
                results["failed"] += 1
                continue
            if test['expected_stdout'] and test['expected_stdout'] not in out:
                print(f"[FAIL] Verification output mismatch. Expected: '{test['expected_stdout']}', Got: '{out}'")
                results["failed"] += 1
                continue
            
            print(f"\n[PASS] Test {test['id']} successful.")
            results["passed"] += 1

        except Exception as e:
            print(f"\n[FAIL] Test {test['id']} crashed with an unhandled exception: {e}")
            results["failed"] += 1
        
        finally:
            # --- 6. Cleanup Phase ---
            print("--- 4. Running Cleanup ---")
            if test['cleanup_commands']:
                for cmd in test['cleanup_commands']:
                    print(f"Running cleanup: `{cmd}`")
                    backend.execute(cmd)
            else:
                print("No cleanup required.")

    # --- SUMMARY ---
    print("\n" + "="*80)
    print(f"--- TEST SUITE SUMMARY (Mode: {mode.upper()}) ---")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    print("="*80)
    
    backend.close()
    print("Remote connection closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AOSS test suite in a specific mode.")
    parser.add_argument('--mode', choices=['aoss', 'monolithic'], required=True, 
                        help="The agent architecture to test: 'aoss' (RAG+Planner+Executor) or 'monolithic' (Single LLM).")
    args = parser.parse_args()
    run_test_suite(args.mode)