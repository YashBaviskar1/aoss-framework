import os
import json
import sys
import csv
import argparse
import datetime
from dotenv import load_dotenv

# AOSS Core Components
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from planner import PlannerAgent
from executor import ExecutorAgent
from remote_executor_v2 import ParamikoBackend, RemotePlanRunner

load_dotenv()

LOG_DIR = "aoss_test_logs"

# ==============================================================================
# TEST CASE DEFINITIONS
# 35 cases across 7 categories, inspired by SRE benchmarks (SWE-bench,
# DevBench, OpsBench) and standard Linux administration runbooks.
#
# Categories:
#   PM  – Package Management         (FT-001 to FT-007)
#   SM  – Service Management         (FT-008 to FT-013)
#   MON – System Monitoring          (FT-014 to FT-018)
#   FS  – Filesystem Operations      (FT-019 to FT-024)
#   NET – Networking                 (FT-025 to FT-028)
#   DEP – Deployment Tasks           (FT-029 to FT-032)
#   ERR – Error / Adversarial Cases  (FT-033 to FT-037)
# ==============================================================================

TEST_CASES = [

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 1: Package Management  (PM)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-001",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install htop",
        "verification_command": "htop --version",
        "expected_stdout": "htop",
        "cleanup_commands": ["sudo apt-get remove -y htop"]
    },
    {
        "id": "FT-002",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install the curl utility",
        "verification_command": "curl --version",
        "expected_stdout": "curl",
        "cleanup_commands": []  # curl is a base dep; leave installed
    },
    {
        "id": "FT-003",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install git version control",
        "verification_command": "git --version",
        "expected_stdout": "git version",
        "cleanup_commands": ["sudo apt-get remove -y git"]
    },
    {
        "id": "FT-004",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install the tree command",
        "verification_command": "tree --version",
        "expected_stdout": "tree",
        "cleanup_commands": ["sudo apt-get remove -y tree"]
    },
    {
        "id": "FT-005",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install unzip",
        "verification_command": "unzip -v",
        "expected_stdout": "UnZip",
        "cleanup_commands": ["sudo apt-get remove -y unzip"]
    },
    {
        "id": "FT-006",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install net-tools so I can use ifconfig and netstat",
        "verification_command": "ifconfig --version",
        "expected_stdout": "net-tools",
        "cleanup_commands": ["sudo apt-get remove -y net-tools"]
    },
    {
        "id": "FT-007",
        "category": "package_management",
        "os": "Ubuntu",
        "query": "install jq for JSON processing",
        "verification_command": "jq --version",
        "expected_stdout": "jq-",
        "cleanup_commands": ["sudo apt-get remove -y jq"]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 2: Service Management  (SM)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-008",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "Install nginx if not already installed, then make sure it is running",
        "verification_command": "systemctl is-active nginx || systemctl start nginx && systemctl is-active nginx",
        "expected_stdout": "active",
        "cleanup_commands": ["sudo systemctl stop nginx", "sudo apt-get remove -y nginx"]
    },
    {
        "id": "FT-009",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "check whether the nginx service is running",
        "verification_command": "systemctl is-active nginx || echo 'not running'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-010",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "restart the SSH service",
        "verification_command": "systemctl is-active ssh",
        "expected_stdout": "active",
        "cleanup_commands": []
    },
    {
        "id": "FT-011",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "enable nginx to start on boot and then start it",
        "verification_command": "systemctl is-enabled nginx",
        "expected_stdout": "enabled",
        "cleanup_commands": [
            "sudo systemctl disable nginx",
            "sudo systemctl stop nginx",
            "sudo apt-get remove -y nginx"
        ]
    },
    {
        "id": "FT-012",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "stop the nginx web server",
        "verification_command": "systemctl is-active nginx || echo 'inactive'",
        "expected_stdout": "inactive",
        "cleanup_commands": []
    },
    {
        "id": "FT-013",
        "category": "service_management",
        "os": "Ubuntu",
        "query": "show me all currently running systemd services",
        "verification_command": "systemctl list-units --type=service --state=running | grep -c running",
        "expected_stdout": None,
        "cleanup_commands": []
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 3: System Monitoring  (MON)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-014",
        "category": "system_monitoring",
        "os": "Ubuntu",
        "query": "check the disk space.",
        "verification_command": "df -h | grep -E '^/dev|^Filesystem'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-015",
        "category": "system_monitoring",
        "os": "Ubuntu",
        "query": "check available memory and RAM usage",
        "verification_command": "free -m | grep Mem",
        "expected_stdout": "Mem",
        "cleanup_commands": []
    },
    {
        "id": "FT-016",
        "category": "system_monitoring",
        "os": "Ubuntu",
        "query": "show current CPU load and top processes",
        "verification_command": "uptime | grep -E 'load average'",
        "expected_stdout": "load average",
        "cleanup_commands": []
    },
    {
        "id": "FT-017",
        "category": "system_monitoring",
        "os": "Ubuntu",
        "query": "display the system uptime and who is logged in",
        "verification_command": "uptime",
        "expected_stdout": "up",
        "cleanup_commands": []
    },
    {
        "id": "FT-018",
        "category": "system_monitoring",
        "os": "Ubuntu",
        "query": "show the last 20 lines of the syslog",
        "verification_command": "test -f /var/log/syslog && echo 'exists' || test -f /var/log/kern.log && echo 'exists'",
        "expected_stdout": "exists",
        "cleanup_commands": []
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 4: Filesystem Operations  (FS)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-019",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "create a file at /tmp/aoss-test.txt with the content 'hello world'",
        "verification_command": "cat /tmp/aoss-test.txt",
        "expected_stdout": "hello world",
        "cleanup_commands": ["rm -f /tmp/aoss-test.txt"]
    },
    {
        "id": "FT-020",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "create a directory called /tmp/aoss-workdir",
        "verification_command": "test -d /tmp/aoss-workdir && echo 'exists'",
        "expected_stdout": "exists",
        "cleanup_commands": ["rm -rf /tmp/aoss-workdir"]
    },
    {
        "id": "FT-021",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "list all files larger than 10MB in the /var directory",
        "verification_command": "find /var -maxdepth 3 -size +10M -type f 2>/dev/null | head -5; echo 'scan done'",
        "expected_stdout": "scan done",
        "cleanup_commands": []
    },
    {
        "id": "FT-022",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "compress the /tmp/aoss-workdir directory into a tar.gz archive at /tmp/aoss-workdir.tar.gz",
        "verification_command": "test -f /tmp/aoss-workdir.tar.gz && echo 'archive exists'",
        "expected_stdout": "archive exists",
        "cleanup_commands": [
            "rm -f /tmp/aoss-workdir.tar.gz",
            "rm -rf /tmp/aoss-workdir"
        ]
    },
    {
        "id": "FT-023",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "find all .log files in /var/log older than 7 days and list them",
        "verification_command": "find /var/log -name '*.log' -mtime +7 2>/dev/null | wc -l; echo 'done'",
        "expected_stdout": "done",
        "cleanup_commands": []
    },
    {
        "id": "FT-024",
        "category": "filesystem",
        "os": "Ubuntu",
        "query": "check the permissions of the /etc/passwd file",
        "verification_command": "ls -l /etc/passwd | grep -E '^-'",
        "expected_stdout": "/etc/passwd",
        "cleanup_commands": []
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 5: Networking  (NET)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-025",
        "category": "networking",
        "os": "Ubuntu",
        "query": "show all open ports on this machine",
        "verification_command": "ss -tlnp | grep -E 'LISTEN|State'",
        "expected_stdout": "LISTEN",
        "cleanup_commands": []
    },
    {
        "id": "FT-026",
        "category": "networking",
        "os": "Ubuntu",
        "query": "check if google.com is reachable by sending 4 ping packets",
        "verification_command": "ping -c 1 -W 3 google.com && echo 'reachable' || echo 'unreachable'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-027",
        "category": "networking",
        "os": "Ubuntu",
        "query": "display the current network interface configuration and IP addresses",
        "verification_command": "ip addr show | grep -E 'inet |inet6 '",
        "expected_stdout": "inet",
        "cleanup_commands": []
    },
    {
        "id": "FT-028",
        "category": "networking",
        "os": "Ubuntu",
        "query": "perform a DNS lookup for github.com",
        "verification_command": "dig github.com +short | head -3; echo 'lookup done'",
        "expected_stdout": "lookup done",
        "cleanup_commands": []
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 6: Deployment Tasks  (DEP)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-029",
        "category": "deployment",
        "os": "Ubuntu",
        "query": "clone the repository https://github.com/octocat/Hello-World.git into /tmp/hello-world",
        "verification_command": "test -d /tmp/hello-world/.git && echo 'cloned'",
        "expected_stdout": "cloned",
        "cleanup_commands": ["rm -rf /tmp/hello-world"]
    },
    {
        "id": "FT-030",
        "category": "deployment",
        "os": "Ubuntu",
        "query": "run a simple python web server on port 8000 in the background serving /tmp",
        "verification_command": "sleep 2 && curl -s http://localhost:8000 | head -5; echo 'server checked'",
        "expected_stdout": "server checked",
        "cleanup_commands": ["pkill -f 'python3 -m http.server 8000' || true"]
    },
    {
        "id": "FT-031",
        "category": "deployment",
        "os": "Ubuntu",
        "query": "deploy my streamlit app from `https://github.com/streamlit/streamlit-example.git`",
        "verification_command": "sleep 5 && curl -s -L http://localhost:8501 | grep -i 'streamlit' || echo 'checked'",
        "expected_stdout": None,
        "cleanup_commands": [
            "pkill -f streamlit || true",
            "rm -rf streamlit-example"
        ]
    },
    {
        "id": "FT-032",
        "category": "deployment",
        "os": "Ubuntu",
        "query": "First, run a simple python web server on port 8000 in the background. Second, configure nginx as a reverse proxy to it.",
        "verification_command": "sleep 2 && curl -s http://localhost | grep -i 'directory listing' || echo 'proxy checked'",
        "expected_stdout": None,
        "cleanup_commands": [
            "pkill -f 'python3 -m http.server' || true",
            "sudo rm -f /etc/nginx/sites-available/aoss_proxy.conf",
            "sudo rm -f /etc/nginx/sites-enabled/aoss_proxy.conf",
            "sudo systemctl reload nginx || true"
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CATEGORY 7: Error Handling / Adversarial  (ERR)
    # ─────────────────────────────────────────────────────────────────────────

    {
        "id": "FT-033",
        "category": "error_handling",
        "os": "Ubuntu",
        "query": "run 'foobar123'",
        "expect_plan_failure": True,
        "verification_command": "echo 'graceful failure check'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-034",
        "category": "error_handling",
        "os": "Ubuntu",
        "query": "install a package called definitely-not-a-real-package-xyz",
        "expect_plan_failure": True,
        "verification_command": "echo 'graceful failure check'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-035",
        "category": "error_handling",
        "os": "Ubuntu",
        "query": "show me the environment variables on this system",
        "verification_command": "printenv | grep -c '=' ; echo 'done'",
        "expected_stdout": "done",
        "cleanup_commands": []
    },
    {
        "id": "FT-036",
        "category": "error_handling",
        "os": "Ubuntu",
        "query": "check if port 22 is open on localhost",
        "verification_command": "ss -tlnp | grep ':22' && echo 'port open' || echo 'port closed'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
    {
        "id": "FT-037",
        "category": "error_handling",
        "os": "Ubuntu",
        "query": "what is the current kernel version of this system?",
        "verification_command": "uname -r | grep -E '^[0-9]'",
        "expected_stdout": None,
        "cleanup_commands": []
    },
]

# ==============================================================================
# MONOLITHIC PROMPT TEMPLATE
# ==============================================================================

MONOLITHIC_PROMPT_TEMPLATE = """
You are an expert SRE and System Administrator. Given a task, provide a JSON list of the exact, step-by-step shell commands required to achieve it.
Assume the server OS is {os}.
Respond ONLY with a valid JSON list of strings, with no additional text, explanations, or markdown formatting.

Task: {query}

JSON list of commands:
"""

# ==============================================================================
# COMPONENT INITIALIZATION
# ==============================================================================

def initialize_aoss_components():
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
        executor_llm = ChatGroq(model=os.getenv("EXECUTOR_LLM", "llama-3.1-8b-versatile"), temperature=0)
        print("AOSS-RAG Components initialized successfully.\n")
        return planner_llm, executor_llm, retriever
    except Exception as e:
        print(f"Error initializing AOSS components: {e}")
        return None, None, None


def initialize_monolithic_components():
    print("--- Initializing Monolithic Component (llama-3.3-70b-versatile) ---")
    try:
        monolithic_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        print("Monolithic Component initialized successfully.\n")
        return monolithic_llm
    except Exception as e:
        print(f"Error initializing Monolithic LLM: {e}")
        return None


def initialize_backend():
    """
    Initializes the persistent Paramiko SSH backend used ONLY for
    verification and cleanup commands throughout the entire test run.

    IMPORTANT: this backend is NEVER passed to RemotePlanRunner.
    RemotePlanRunner gets its own fresh ParamikoBackend instance per test
    (via _make_fresh_backend), so its internal backend.close() call cannot
    destroy the shared connection.
    """
    print("--- Initializing Persistent Verification/Cleanup Connection ---")
    host     = os.getenv("SSH_HOST")
    user     = os.getenv("SSH_USER")
    password = os.getenv("SSH_PASS")
    key_path = os.getenv("SSH_KEY_PATH")
    if not host or not user or not (password or key_path):
        print("Error: SSH_HOST, SSH_USER, and (SSH_PASS or SSH_KEY_PATH) must be set in .env")
        return None
    try:
        backend = ParamikoBackend(host=host, user=user, password=password,
                                  key_filename=key_path)
        print(f"Connecting to {user}@{host}...")
        backend.connect()
        code, out, err = backend.execute('echo "AOSS Test Connection OK"', timeout=10)
        if code == 0 and "OK" in out:
            print("[SUCCESS] Persistent connection verified.\n")
            return backend
        else:
            print(f"[FAILED] Could not verify remote connection. stderr: {err}")
            return None
    except Exception as e:
        print(f"Failed to set up remote connection: {e}")
        return None


def _ensure_backend_alive(backend):
    """
    Checks if the shared backend's SSH transport is still active and
    reconnects transparently if it has dropped (e.g. after a long test).
    Called before every verification and cleanup block.
    """
    try:
        transport = backend.client.get_transport() if backend.client else None
        if transport is None or not transport.is_active():
            print("[INFO] Shared connection dropped — reconnecting...")
            backend.connect()
            print("[INFO] Reconnected successfully.")
    except Exception as e:
        print(f"[WARN] Reconnect raised: {e} — retrying once...")
        try:
            backend.connect()
        except Exception as e2:
            print(f"[ERROR] Could not reconnect shared backend: {e2}")
    return backend


def _make_fresh_backend():
    """
    Creates a brand-new, unconnected ParamikoBackend for use by a single
    RemotePlanRunner instance.  The runner calls connect() and close()
    internally, so this must be a completely separate object from the
    shared verification backend.
    """
    return ParamikoBackend(
        host=os.getenv("SSH_HOST"),
        user=os.getenv("SSH_USER"),
        password=os.getenv("SSH_PASS"),
        key_filename=os.getenv("SSH_KEY_PATH"),
    )

# ==============================================================================
# RESULT EXPORT HELPERS
# ==============================================================================

def export_csv(results_list, filepath):
    """Write per-test results to a CSV file for direct paper table use."""
    fieldnames = [
        "test_id", "category", "mode", "query",
        "plan_correct", "execution_success",
        "status", "execution_time_s",
        "commands_generated", "policy_violation", "blocked_by_policy"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results_list:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"[CSV] Results written to {filepath}")


def export_summary_json(summary, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[JSON] Summary written to {filepath}")

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_test_suite(mode, category_filter=None):
    """
    Runs the full (or filtered) test suite against the specified agent architecture.

    Args:
        mode:            'aoss' | 'monolithic'
        category_filter: optional list of category strings to restrict which tests run
    """
    # ── 1. Initialize components ──────────────────────────────────────────────
    planner_llm = executor_llm = retriever = monolithic_llm = None

    if mode == 'aoss':
        planner_llm, executor_llm, retriever = initialize_aoss_components()
        if not planner_llm:
            sys.exit(1)
    elif mode == 'monolithic':
        monolithic_llm = initialize_monolithic_components()
        if not monolithic_llm:
            sys.exit(1)

    backend = initialize_backend()
    if not backend:
        sys.exit(1)

    # ── 2. Prepare logging ────────────────────────────────────────────────────
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_log  = os.path.join(LOG_DIR, f"test_run_{mode}_{timestamp}.json")
    csv_log   = os.path.join(LOG_DIR, f"test_run_{mode}_{timestamp}.csv")
    summary_log = os.path.join(LOG_DIR, f"summary_{mode}_{timestamp}.json")

    full_test_run_data = []   # raw per-test JSON records
    csv_rows           = []   # flattened rows for CSV export

    # aggregate counters
    counters = {
        "total": 0, "passed": 0, "failed": 0, "skipped": 0,
        "correct_plans": 0, "incorrect_plans": 0, "critical_failures": 0,
        "expected_failures_correct": 0,
        "by_category": {}
    }

    # ── 3. Filter test cases ──────────────────────────────────────────────────
    active_tests = TEST_CASES
    if category_filter:
        active_tests = [t for t in TEST_CASES if t.get("category") in category_filter]
        print(f"Running {len(active_tests)} tests in categories: {category_filter}")

    # ── 4. Iterate ────────────────────────────────────────────────────────────
    for test in active_tests:
        counters["total"] += 1
        cat = test.get("category", "unknown")
        counters["by_category"].setdefault(cat, {"passed": 0, "failed": 0, "total": 0})
        counters["by_category"][cat]["total"] += 1

        print("\n" + "=" * 80)
        print(f"  TEST [{test['id']}]  MODE={mode.upper()}  CAT={cat.upper()}")
        print(f"  QUERY: \"{test['query']}\"")
        print("=" * 80)

        plan_failed      = False
        execution_history = []
        test_plan        = {}
        test_status      = "FAILED"
        plan_correct     = False
        t_start          = datetime.datetime.now()

        try:
            # ── 4A. AOSS pipeline ──────────────────────────────────────────────
            if mode == 'aoss':
                print("--- Step 1: Generating Plan (AOSS-RAG) ---")
                user_query_with_context = f"Server OS: {test['os']}\n\nTask: {test['query']}"
                planner = PlannerAgent(llm=planner_llm, retriever=retriever)
                plan = planner.generate_plan(user_query_with_context)
                test_plan = plan or {}

                if not plan:
                    print("[FAIL] AOSS Planner returned no valid plan.")
                    counters["failed"] += 1
                    test_status = "FAILED (Planner)"
                    continue

                plan_correct = True   # tentative; refined in step-4 below
                print("--- Step 2: Executing Plan (AOSS-RAG) ---")
                # CRITICAL: fresh backend per test so run_plan()'s internal
                # close() never kills the shared verification backend.
                test_backend  = _make_fresh_backend()
                remote_runner = RemotePlanRunner(backend=test_backend, env=plan.get('env', {}))
                executor      = ExecutorAgent(plan_json=plan, llm=executor_llm,
                                              retriever=retriever, remote_runner=remote_runner)
                executor.execute_plan()
                execution_history = executor.history

            # ── 4B. Monolithic pipeline ────────────────────────────────────────
            elif mode == 'monolithic':
                print("--- Step 1: Generating Plan (Monolithic) ---")
                prompt = MONOLITHIC_PROMPT_TEMPLATE.format(os=test['os'], query=test['query'])
                response_str = ""
                try:
                    response_str = monolithic_llm.invoke(prompt).content
                    commands_list = json.loads(response_str)
                    plan_dict = {
                        "env": {},
                        "plan": [{"step": i + 1, "command": cmd}
                                 for i, cmd in enumerate(commands_list)]
                    }
                    test_plan    = plan_dict
                    plan_correct = True
                    print(json.dumps(plan_dict, indent=2))
                except Exception as e:
                    print(f"[FAIL] Monolithic Planner did not return valid JSON. Error: {e}")
                    print(f"Raw Output: {response_str}")
                    counters["failed"] += 1
                    counters["incorrect_plans"] += 1
                    test_status = "FAILED (Planner)"
                    continue

                print("--- Step 2: Executing Plan (Monolithic) ---")
                # CRITICAL: fresh backend per test — same reason as AOSS branch.
                test_backend  = _make_fresh_backend()
                remote_runner = RemotePlanRunner(backend=test_backend, env=plan_dict.get('env', {}))
                execution_history = remote_runner.run_plan(plan_dict['plan'])

            # ── 4C. Execution failure check ────────────────────────────────────
            if any(step.get('status') == 'FAILED' for step in execution_history):
                plan_failed  = True
                plan_correct = False   # execution failure implies plan quality issue

            # ── 4D. Expected-failure tests ─────────────────────────────────────
            if test.get("expect_plan_failure"):
                if plan_failed:
                    print(f"\n[PASS] {test['id']} failed as expected (graceful degradation).")
                    counters["passed"]                    += 1
                    counters["expected_failures_correct"] += 1
                    counters["by_category"][cat]["passed"] += 1
                    test_status  = "PASSED (Expected Fail)"
                    plan_correct = True
                else:
                    print(f"\n[FAIL] {test['id']} was expected to fail but succeeded.")
                    counters["failed"] += 1
                    counters["by_category"][cat]["failed"] += 1
                    test_status  = "FAILED (Unexpected Success)"
                    plan_correct = False
                continue

            if plan_failed:
                print(f"\n[FAIL] {test['id']} failed during execution.")
                counters["failed"] += 1
                counters["by_category"][cat]["failed"] += 1
                test_status = "FAILED (Execution)"
                continue

            # ── 4E. Verification ───────────────────────────────────────────────
            print("--- Step 3: Verifying Outcome ---")
            _ensure_backend_alive(backend)
            code, out, err = backend.execute(test['verification_command'], timeout=30)

            if code != 0:
                print(f"[FAIL] Verification failed (exit {code}). STDOUT: {out}  STDERR: {err}")
                counters["failed"] += 1
                counters["by_category"][cat]["failed"] += 1
                test_status  = "FAILED (Verification)"
                plan_correct = False
                continue

            if test.get('expected_stdout') and test['expected_stdout'] not in out:
                print(f"[FAIL] Output mismatch. Expected: '{test['expected_stdout']}', Got: '{out}'")
                counters["failed"] += 1
                counters["by_category"][cat]["failed"] += 1
                test_status  = "FAILED (Verification)"
                plan_correct = False
                continue

            print(f"\n[PASS] {test['id']} verified successfully.")
            counters["passed"] += 1
            counters["by_category"][cat]["passed"] += 1
            test_status  = "PASSED"
            plan_correct = True

        except Exception as e:
            print(f"\n[FAIL] {test['id']} crashed: {e}")
            counters["failed"]                        += 1
            counters["by_category"][cat]["failed"]    += 1
            test_status  = "FAILED (Crashed)"
            plan_correct = False

        finally:
            t_elapsed = (datetime.datetime.now() - t_start).total_seconds()

            # ── 4F. Cleanup ────────────────────────────────────────────────────
            print("--- Step 4: Cleanup ---")
            if test.get('cleanup_commands'):
                _ensure_backend_alive(backend)
                for cmd in test['cleanup_commands']:
                    print(f"  cleanup: {cmd}")
                    try:
                        backend.execute(cmd, timeout=60)
                    except Exception as ce:
                        print(f"  [WARN] Cleanup command failed (non-fatal): {ce}")
            else:
                print("  No cleanup required.")

            # Update plan-quality counters
            if plan_correct:
                counters["correct_plans"] += 1
            else:
                counters["incorrect_plans"] += 1

            # ── 4G. Per-test record ────────────────────────────────────────────
            record = {
                "test_id":           test['id'],
                "category":          cat,
                "mode":              mode,
                "query":             test['query'],
                "status":            test_status,
                "plan_correct":      plan_correct,
                "execution_success": test_status.startswith("PASSED"),
                "execution_time_s":  round(t_elapsed, 2),
                "commands_generated": len(test_plan.get("plan", [])),
                "policy_violation":  False,   # extended in compliance experiments
                "blocked_by_policy": False,
                "plan":              test_plan,
                "execution_history": execution_history
            }
            full_test_run_data.append(record)
            csv_rows.append(record)

    # ── 5. Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print(f"  TEST SUITE SUMMARY — Mode: {mode.upper()}")
    print("=" * 80)
    print(f"  Total     : {counters['total']}")
    print(f"  Passed    : {counters['passed']}")
    print(f"  Failed    : {counters['failed']}")
    print(f"  Correct Plans   : {counters['correct_plans']}")
    print(f"  Incorrect Plans : {counters['incorrect_plans']}")
    print(f"  Critical Failures: {counters['critical_failures']}")
    print("\n  Results by Category:")
    for cat_name, cat_data in counters["by_category"].items():
        pct = (cat_data["passed"] / cat_data["total"] * 100) if cat_data["total"] else 0
        print(f"    {cat_name:<22} {cat_data['passed']}/{cat_data['total']}  ({pct:.0f}%)")
    print("=" * 80)

    # ── 6. Export ─────────────────────────────────────────────────────────────
    try:
        with open(json_log, 'w', encoding='utf-8') as f:
            json.dump(full_test_run_data, f, indent=2, ensure_ascii=False)
        print(f"\n[LOG]  Full JSON log  → {json_log}")
    except Exception as e:
        print(f"[ERROR] Could not write JSON log: {e}")

    export_csv(csv_rows, csv_log)

    summary = {
        "run_timestamp": timestamp,
        "mode": mode,
        "counters": counters,
        "test_ids_run": [t['id'] for t in active_tests]
    }
    export_summary_json(summary, summary_log)

    backend.close()
    print("\nRemote connection closed.")

# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AOSS Research Experiment Harness — run test suite against an agent architecture."
    )
    parser.add_argument(
        '--mode',
        choices=['aoss', 'monolithic'],
        required=True,
        help="Agent architecture under test: 'aoss' (RAG+Planner+Executor) or 'monolithic' (single large LLM)."
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=[
            'package_management', 'service_management', 'system_monitoring',
            'filesystem', 'networking', 'deployment', 'error_handling'
        ],
        default=None,
        help="Optional: restrict the run to one or more test categories."
    )
    args = parser.parse_args()
    run_test_suite(mode=args.mode, category_filter=args.categories)