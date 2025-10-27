import os
import json
import sys
from dotenv import load_dotenv

# AOSS Core Components
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from planner import PlannerAgent
from executor import ExecutorAgent
from remote_executor import ParamikoBackend, RemotePlanRunner # We will use Paramiko directly

# --- INSTRUCTIONS ---
#
# 1. Make sure you have run `context_maker.py` at least once.
# 2. Create a `.env` file in this directory with your remote server details:
#
#    GROQ_API_KEY=your_groq_api_key_here
#    SSH_HOST=your.server.ip.or.hostname
#    SSH_USER=your_username
#    SSH_PASS=your_password_for_ssh_and_sudo
#    # SSH_KEY_PATH=/path/to/your/id_rsa (Use this OR SSH_PASS)
#
# 3. Run this file: `python test_cases.py`
#
# --- --- --- --- ---

# --- Test Case Definitions ---
# This list is based on the Functional Test Cases from your report.
# We've added `verification_command` and `cleanup_commands` to automate the checks.
# NOTE: I've used a *real* public repo for the Streamlit test.
TEST_CASES = [
    {
        "id": "FT-001",
        "os": "Ubuntu",
        "query": "install htop",
        "verification_command": "htop --version",
        "expected_stdout": None, # We only care that the command succeeds (exit code 0)
        "cleanup_commands": ["sudo apt-get remove -y htop"]
    },
    {
        "id": "FT-003",
        "os": "Ubuntu",
        "query": "I need nginx.",
        "verification_command": "systemctl is-active nginx",
        "expected_stdout": "active",
        "cleanup_commands": ["sudo systemctl stop nginx", "sudo apt-get remove -y nginx"]
    },
    {
        "id": "FT-004",
        "os": "Ubuntu",
        "query": "check the disk space.",
        "verification_command": "df -h", # This command will just run, success is assumed if plan works
        "expected_stdout": "/", # Just check that it returns *some* disk info
        "cleanup_commands": []
    },
    {
        "id": "FT-005",
        "os": "Ubuntu",
        "query": "set up a new user 'testuser'",
        "verification_command": "grep '^testuser:' /etc/passwd",
        "expected_stdout": "testuser:", # Check that the user exists in /etc/passwd
        "cleanup_commands": ["sudo userdel testuser"]
    },
    {
        "id": "FT-006",
        "os": "Ubuntu",
        "query": "create a file at /tmp/aoss-test.txt with the content 'hello world'",
        "verification_command": "cat /tmp/aoss-test.txt",
        "expected_stdout": "hello world",
        "cleanup_commands": ["rm /tmp/aoss-test.txt"]
    },
    {
        "id": "FT-010",
        "os": "Ubuntu",
        "query": "run 'foobar123'",
        "expect_plan_failure": True, # This test PASSES if the plan execution FAILS
        "verification_command": "echo 'Checking for graceful failure'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-013",
        "os": "Ubuntu",
        "query": "deploy my streamlit app from `https://github.com/streamlit/streamlit-example.git`",
        "verification_command": "curl -s -L http://localhost:8501 | grep -i 'Streamlit'",
        "expected_stdout": "Streamlit", # Check if the Streamlit app page is loading
        "cleanup_commands": [
            "pkill -f streamlit", # Kill the streamlit process
            "rm -rf streamlit-example" # Remove the cloned repo
        ]
    },
    {
        "id": "FT-014",
        "os": "Ubuntu",
        "query": "First, run a simple python web server on port 8000 in the background. Second, configure nginx as a reverse proxy to it.",
        "verification_command": "curl -s http://localhost | grep -i 'Directory listing'",
        "expected_stdout": "Directory listing", # Nginx should proxy the python server's directory page
        "cleanup_commands": [
            "pkill -f 'python3 -m http.server'", # Kill the python server
            "sudo rm /etc/nginx/sites-enabled/default", # Remove default symlink
            "sudo rm /etc/nginx/sites-available/aoss_proxy.conf", # Remove our config
            "sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default", # Re-link default
            "sudo systemctl reload nginx"
        ]
    },
]

# --- AOSS Component Initialization ---

def initialize_components():
    """Initializes and returns the shared AOSS components."""
    print("--- Initializing Shared Components (LLMs, Retriever) ---")
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
        
        print("Components initialized successfully.\n")
        return planner_llm, executor_llm, retriever
    except Exception as e:
        print(f"Error initializing components: {e}")
        print("Please ensure GROQ_API_KEY is set and `context_maker.py` has been run.")
        return None, None, None

def initialize_backend():
    """Initializes and tests the Paramiko SSH backend from .env variables."""
    print("--- Initializing Remote Server Connection ---")
    host = os.getenv("SSH_HOST")
    user = os.getenv("SSH_USER")
    password = os.getenv("SSH_PASS")
    key_path = os.getenv("SSH_KEY_PATH")

    if not host or not user:
        print("Error: SSH_HOST and SSH_USER must be set in .env")
        return None
    if not password and not key_path:
        print("Error: SSH_PASS or SSH_KEY_PATH must be set in .env")
        return None

    try:
        backend = ParamikoBackend(
            host=host,
            user=user,
            password=password,
            key_filename=key_path
        )
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

def run_test_suite():
    """
    Main function to run the defined test cases against the AOSS framework.
    """
    load_dotenv()
    
    planner_llm, executor_llm, retriever = initialize_components()
    if not planner_llm:
        sys.exit(1)

    backend = initialize_backend()
    if not backend:
        sys.exit(1)
        
    results = {"passed": 0, "failed": 0, "skipped": 0}

    for test in TEST_CASES:
        print("\n" + "="*80)
        print(f"RUNNING TEST: [{test['id']}] - {test['os']} - \"{test['query']}\"")
        print("="*80)
        
        plan_failed = False
        execution_history = []
        
        try:
            # 1. --- PLAN PHASE ---
            print("--- 1. Generating Plan ---")
            user_query_with_context = f"Server OS: {test['os']}\n\nTask: {test['query']}"
            planner = PlannerAgent(llm=planner_llm, retriever=retriever)
            plan = planner.generate_plan(user_query_with_context)

            if not plan:
                print("[FAIL] Planner did not return a valid plan.")
                results["failed"] += 1
                continue

            # 2. --- EXECUTE PHASE ---
            print("--- 2. Executing Plan Remotely ---")
            # We must create a new backend instance for the runner, as it closes it
            # Or, we can modify RemotePlanRunner to not close the backend.
            # For this test, let's just re-use the connected backend.
            # We'll create a *new* runner for each test.
            
            # Re-create backend for the runner (or modify runner to not close)
            # Easiest way: just pass the already-connected backend
            
            # NOTE: We need to pass a *fresh* backend instance for the runner
            # because the runner closes it.
            test_backend = ParamikoBackend(
                host=os.getenv("SSH_HOST"), user=os.getenv("SSH_USER"),
                password=os.getenv("SSH_PASS"), key_filename=os.getenv("SSH_KEY_PATH")
            )
            
            remote_runner = RemotePlanRunner(backend=test_backend, env=plan.get('env', {}))
            executor = ExecutorAgent(
                plan_json=plan, 
                llm=executor_llm, 
                retriever=retriever,
                remote_runner=remote_runner
            )
            executor.execute_plan() # This will run and close test_backend
            execution_history = executor.history
            
            # Check for execution failure
            if any(step['status'] == 'FAILED' for step in execution_history):
                plan_failed = True

            # Handle tests that *expect* failure
            if test.get("expect_plan_failure"):
                if plan_failed:
                    print(f"\n[PASS] Test {test['id']} failed as expected.")
                    results["passed"] += 1
                else:
                    print(f"\n[FAIL] Test {test['id']} was expected to fail, but it succeeded.")
                    results["failed"] += 1
                continue # Skip verification
            elif plan_failed:
                print(f"\n[FAIL] Test {test['id']} failed during execution.")
                results["failed"] += 1
                continue # Skip verification

            # 3. --- VERIFY PHASE ---
            print("--- 3. Verifying Outcome ---")
            code, out, err = backend.execute(test['verification_command'])
            
            if code != 0:
                print(f"[FAIL] Verification command failed with code {code}.")
                print(f"STDOUT: {out}\nSTDERR: {err}")
                results["failed"] += 1
                continue

            if test['expected_stdout'] and test['expected_stdout'] not in out:
                print(f"[FAIL] Verification output mismatch.")
                print(f"Expected: '{test['expected_stdout']}'")
                print(f"Got:      '{out}'")
                results["failed"] += 1
                continue
            
            print(f"\n[PASS] Test {test['id']} successful.")
            results["passed"] += 1

        except Exception as e:
            print(f"\n[FAIL] Test {test['id']} crashed with an unhandled exception: {e}")
            results["failed"] += 1
        
        finally:
            # 4. --- CLEANUP PHASE ---
            print("--- 4. Running Cleanup ---")
            if test['cleanup_commands']:
                for cmd in test['cleanup_commands']:
                    print(f"Running cleanup: `{cmd}`")
                    backend.execute(cmd)
            else:
                print("No cleanup required.")

    # --- SUMMARY ---
    print("\n" + "="*80)
    print("--- TEST SUITE SUMMARY ---")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    print("="*80)
    
    backend.close()
    print("Remote connection closed.")


if __name__ == "__main__":
    run_test_suite()
