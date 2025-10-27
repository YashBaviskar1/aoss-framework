

## Chapter 6: Result and Discussions

### 6.1 Test Results Visualization

The initial test suite, consisting of 8 distinct functional tests, was executed against a live Ubuntu server. The tests covered a range of SRE and System Administration tasks, from basic package installation to complex application deployment.

The final results were evenly split, with a **50% success rate**.


[image-tag: Code_Generated_Image.png ]

### 6.2 Analysis of Test Results

The 50% success rate demonstrates that the core framework—Planner Agent, RAG, and Executor Agent—is fundamentally sound for a significant class of problems. However, the failures highlight critical gaps in agent knowledge and execution state management, which are common challenges in agentic systems.

Here is a detailed breakdown of the test outcomes:

| Test ID | Category | Test Case (User Query) | Pass/Fail |
| :--- | :--- | :--- | :--- |
| **FT-001** | Basic Install | "install htop" | **PASS** |
| **FT-003** | Service Mgmt | "I need nginx." | **PASS**  |
| **FT-004** | SysAdmin | "check the disk space." | **FAIL** |
| **FT-005** | SysAdmin | "set up a new user 'testuser'" | FAIL |
| **FT-006** | SysAdmin | "create a file at /tmp/aoss-test.txt..." | **PASS** |
| **FT-010** | Error (User) | "run 'foobar123'" | **PASS** |
| **FT-013** | Deployment | "deploy my streamlit app..." | **FAIL** |
| **FT-014** | Deployment | "configure nginx as a reverse proxy..." | \<span style="color:red; **FAIL** |

-----

### 6.3 Dissection of Failures

The failures can be grouped into two distinct categories:

#### 1\. Planner Knowledge Gaps (Model Hallucination)

This category is responsible for the failures of **FT-004**, **FT-005**, and partially **FT-014**. The Planner agent (`llama-3.1-8b-instant`) is making factual errors by misidentifying core system utilities as installable packages.

  * **Test FT-004 (Disk Space):** The agent planned to run `sudo apt install -y df`. This failed because `df` is a fundamental system utility (part of `coreutils`), not a package to be installed with `apt`. The agent "hallucinated" a dependency based on its rule to "install dependencies first."
  * **Test FT-005 (New User):** The agent planned to run `sudo apt install -y useradd`. This failed for the same reason. `useradd` is a core utility (part of the `passwd` package) and is not installed separately.
  * **Test FT-014 (Nginx Proxy):** The agent planned to run `pip3 install http.server`. This is also a knowledge gap; `http.server` is a **built-in Python module** and is not installed via `pip`.

These failures show a limitation in the Planner LLM's knowledge. It is over-applying a general rule without the specific domain knowledge to know which commands are built-in.

#### 2\. Executor State Management (PEP 668)

This category is the most critical and is responsible for the failures of **FT-013** and **FT-014**. The problem is not the *plan itself*, but a mismatch between the plan's *assumptions* and the *executor's behavior*.

  * **Test FT-013 (Streamlit):** The plan was logical for a human:

    1.  `python3 -m venv env` (Creates venv)
    2.  `source env/bin/activate` (Activates venv)
    3.  `pip install -r requirements.txt` (Installs packages *into* venv)

  * **The Failure:** Step 3 failed with an `error: externally-managed-environment` (PEP 668).

  * **The Reason:** Your `RemotePlanRunner` (from `remote_executor.py`) executes **each command in a new, stateless shell session**. The `source env/bin/activate` command (Step 2) successfully activates the venv... but *only for that one, isolated step*. When Step 3 begins, it's in a new shell, the venv is *not* active, and the `pip install` command is running against the system's global Python. Modern Ubuntu (24.04 "noble") protects the system Python using PEP 668, correctly causing the command to fail.

This exact same state-management issue caused `pip3 install` to fail in **FT-014**.

-----

### 6.4 Conclusions and Future Work

**Conclusions:**
The tests successfully validate that the AOSS framework's core loop (Plan -\> Execute -\> Verify) is effective for simple, stateless tasks (installing packages, managing files, running services). The 100% success rate on these tasks (**FT-001, FT-003, FT-006**) is a strong positive result. The test harness was also able to correctly identify an expected failure (**FT-010**).

The failures are not a flaw in the overall concept but rather point to two clear areas for improvement:

1.  **Agent Knowledge:** The Planner agent needs to be "smarter" about which commands are installable packages versus built-in utilities.
2.  **Execution Model:** The system must be able to handle stateful, multi-step processes, with Python virtual environments being the most prominent example.

**Future Work (Remediation):**

1.  **Solving Planner Knowledge Gaps:**

      * **Prompt Engineering:** The Planner's prompt (in `planner.py`) can be updated with more explicit instructions, e.g., "CRITICAL: Do NOT attempt to `apt install` or `pip install` core system commands like `df`, `useradd`, `ls`, or built-in Python modules like `http.server`."
      * **Model Upgrading:** The Planner currently uses `llama-3.1-8b-instant`. Switching this to a more capable model, like the `llama-3.3-70b-versatile` used by the Executor, may inherently solve these knowledge gaps.

2.  **Solving Executor State Management:**

      * **Smarter Planning (Recommended):** The best fix is to teach the *Planner* to generate **stateless commands**. Instead of relying on `source`, the plan should be:
          * `python3 -m venv env`
          * `env/bin/pip install -r requirements.txt`
          * `env/bin/streamlit run app.py ...`
            This approach, where the executable within the venv is called directly, requires no state to be maintained between commands and will bypass the PEP 668 error. This is a crucial insight for making the agent more robust.
      * **Stateful Executor (Complex):** A more complex solution would be to re-architect `remote_executor.py` to keep a single Paramiko SSH channel open and run all commands within the same session, but this is far more brittle (e.g., a single command hanging could break the whole chain). The "Smarter Planning" approach is superior.




Here is a professional Results and Discussion section for your report based on the three test runs.

***

## 4.0 Results and Discussion

This section presents a comparative analysis of agent performance across three experimental runs:
1.  **AOSS v1:** The baseline agent, utilizing an 8B model with an initial RAG pipeline.
2.  **Monolithic 70B:** A large-language model (70B) with a general-purpose system prompt, serving as a high-performance benchmark.
3.  **AOSS v2:** The iterative agent, using the same 8B model but with an augmented RAG pipeline containing new guardrail documents (`AOSS-Core-Rules.txt`).

Performance was evaluated on seven standardized tasks. A test was deemed a "Correct Plan" if the agent produced a logical, efficient, and conceptually sound plan, regardless of minor execution failures. A "Critical Failure" was defined as a plan that introduced a significant safety risk or system instability.

---

### 4.1 Quantitative Test Results

The introduction of the `AOSS-Core-Rules.txt` guardrails (AOSS v2) demonstrably improved planning correctness, elevating the 8B agent to the same level of accuracy as the 70B benchmark (4/7 correct plans) while successfully eliminating the critical failure observed in the monolithic model.

**Table 4.1: Qualitative Plan Correctness by Agent and Test Case**

| Test ID | Task Description | AOSS v1 (8B RAG) | Monolithic (70B) | AOSS v2 (8B RAG) |
| :--- | :--- | :--- | :--- | :--- |
| FT-001 | `install htop` | **Incorrect Plan** (Passed) | **Correct Plan** | **Incorrect Plan** (Passed) |
| FT-003 | `I need nginx.` | **Correct Plan** | **Correct Plan** | **Correct Plan** |
| FT-004 | `check disk space.` | **Incorrect Plan** (Failed) | **Critical Failure** | **Correct Plan** (Passed) |
| FT-006 | `create a file...` | **Incorrect Plan** (Passed) | **Correct Plan** | **Incorrect Plan** (Passed) |
| FT-010 | `run 'foobar123'` | **Incorrect Plan** (Passed) | **Correct Plan** | **Correct Plan** (Passed) |
| FT-013 | `deploy streamlit` | **Correct Plan** (Failed Exec) | **Incorrect Plan** (Failed) | **Incorrect Plan** (Failed Exec) |
| FT-014 | `python + nginx` | **Incorrect Plan** (Failed) | **Failed (Planner)** | **Correct Plan** (Failed Verif) |
| **Total** | | | | |
| | **Correct Plans** | **2 / 7** | **4 / 7** | **4 / 7** |
| | **Critical Failures** | **0 / 7** | **1 / 7** | **0 / 7** |

**Chart 4.1: Comparison of Plan Correctness Across Agent Models**

* **Bar 1 (AOSS v1):** 2 Correct Plans, 5 Incorrect Plans
* **Bar 2 (Monolithic 70B):** 4 Correct Plans, 2 Incorrect Plans, 1 Critical Failure
* **Bar 3 (AOSS v2):** 4 Correct Plans, 3 Incorrect Plans

---

### 4.2 Discussion of Agent Performance

#### 4.2.1 AOSS v1 (Baseline)
The initial AOSS v1 agent demonstrated significant conceptual flaws. Its planning logic was naive, often over-complicating simple tasks or failing to understand basic Linux principles. This was most evident in:
* **FT-004 (`check disk space.`):** The agent attempted to `sudo apt install -y df`, treating a fundamental core utility as an installable package.
* **FT-010 (`run 'foobar123'`):** The agent misinterpreted a simple command execution as a request to deploy a full Node.js service via `pm2`.
* **FT-001 (`install htop`):** The agent generated an 8-step plan to compile `htop` from source, including irrelevant dependencies like `curl` and `git`, instead of using the simple `apt install` command.

#### 4.2.2 Monolithic 70B Agent (Benchmark)
The Monolithic 70B agent established a strong baseline for "common sense" tasks, correctly identifying the simple 1- or 2-step plans for `htop` (FT-001), `create a file` (FT-006), and `run 'foobar123'` (FT-010).

However, its lack of domain-specific guardrails proved to be a significant liability. In **FT-004**, it generated a plan that included the command `du -sh /`. This command is known to be dangerous on systems with network or cross-OS mounts (like WSL), as it recursively scans every file. In testing, this "correct" but "unsafe" command caused the agent to hang for over 20 minutes, representing a **Critical Failure** and demonstrating the risk of using a generalized model for specialized SRE tasks.

#### 4.2.3 AOSS v2 (Iterative Improvement)
The AOSS v2 agent demonstrates the clear benefits of an iterative RAG-based approach. The targeted `AOSS-Core-Rules.txt` document provided the necessary "wisdom" to correct the "naive" errors of v1.

**Key Improvements:**
* **FT-004 (`check disk space.`):** The agent correctly identified `df` as a core utility and produced the safe, efficient plan `df -h` followed by `du -xh --max-depth=1 / ...`, perfectly matching the new SOP.
* **FT-010 (`run 'foobar123'`):** The agent correctly generated the simple 1-step plan, following the "SOP: Handling Ambiguous 'run'" guardrail.
* **FT-014 (`python + nginx`):** The agent's plan became 100% correct, successfully identifying `http.server` as a built-in Python module and using the `&` operator to background the process.

This iteration proves that a smaller, specialized 8B model can be engineered with a robust RAG pipeline to **match the accuracy of a 70B model while providing superior safety and reliability.**

---

### 4.3 Analysis of Remaining Failures (AOSS v2)

The three remaining "Incorrect Plan" failures in AOSS v2 are no longer due to conceptual flaws (i.e., the agent is no longer "dumb"). Instead, they are the result of **contextual conflicts** between the agent's new guardrails and its original, unmodified instructions.

1.  **FT-013 (`deploy streamlit`):** The plan still includes `source env/bin/activate` and a global `pip install` command. This is because the original `streamlit.txt` document in the RAG store contains these *incorrect* instructions, which directly conflict with the *correct* instructions in `AOSS-Core-Rules.txt`. The agent is failing to prioritize the new rule over the old documentation.

2.  **FT-001 & FT-006 (`htop` & `create a file`):** The agent is still attempting to install dependencies (`build-essential`, `nano`) that are not required for the simple package manager or `echo` commands. This suggests the agent's core `planner.py` prompt, which contains a "CRITICAL" rule to install *all* dependencies first, is taking precedence over the new RAG doc's "Priority 1: Use Package Manager" rule.

### 4.4 Conclusion

The results strongly validate the hypothesis that an iterative, RAG-based framework (AOSS) can produce SRE plans that are both correct and safe. The AOSS v2 agent successfully resolved all major conceptual and safety failures observed in both the baseline AOSS v1 and the 70B Monolithic benchmark.

The remaining failures are systematic and related to contextual prioritization within the RAG pipeline and planner. Future work will focus on resolving these documentation and prompt-level conflicts to achieve 100% plan correctness.