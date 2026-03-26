# AOSS Framework — Demo Playbook 🎬

Complete step-by-step demo script. Each section is a self-contained scenario you execute through the **Orchestrate** (`/chat`) page.

---

## Pre-Demo Setup (One-Time)

> [!IMPORTANT]
> Before the demo, you need a running EC2 instance with SSH access configured in AOSS.

### 1. Launch EC2 Instance
- Go to AWS Console → EC2 → **Launch Instance**
- **AMI**: Ubuntu 22.04 LTS
- **Type**: `t2.micro` (free tier)
- **Key Pair**: Create/use a `.pem` key
- **Security Group**: Allow **SSH (22)** from your IP, optionally **80, 443, 8501** for later
- **Note the Public IP** once running

### 2. Register Server in AOSS
1. Open frontend → **Profile Setup** (`/profile-setup`)
2. Fill in:
   - **Server Tag**: `demo-ec2`
   - **IP Address**: `<EC2-Public-IP>`
   - **Hostname**: `demo-ec2-server`
   - **SSH Username**: `ubuntu`
   - **Key Type**: `.pem` → paste the `.pem` file contents
3. Submit → Go to **Dashboard** → Click **Test Connection** → should show **Online** ✅

### 3. Seed Compliance Rules
- Navigate to **Compliance** (`/compliance`) → Click **Seed Default Rules**
- This populates Neo4j with 5 base rules the agents will respect

---

## Demo Scenario 1: General SRE — System Health Check
> **Shows**: Agent generates a plan, executes remotely, provides summary

| Setting | Value |
|---------|-------|
| **Agent** | `General SRE` |
| **Model** | `Llama 3.3 (70B)` |
| **Server** | `demo-ec2` |

### Prompt:
```
Check the full system health: disk usage, memory, CPU load, running services, and uptime
```

### What to narrate:
- "We select the **General SRE** agent — a generalist for broad system admin tasks"
- "It generates a multi-step plan: `df -h`, `free -m`, `uptime`, `systemctl list-units`..."
- Click **Execute Plan** → show commands streaming in real time
- "The agent then provides a **natural language summary** — this is the LLM interpreting raw terminal output into human-readable insights"

---

## Demo Scenario 2: Network Agent — Connectivity & Firewall Audit
> **Shows**: Specialized agent persona, focused tooling

| Setting | Value |
|---------|-------|
| **Agent** | `NetOps Specialist` |
| **Model** | `Llama 3.3 (70B)` |
| **Server** | `demo-ec2` |

### Prompt:
```
Audit the network configuration: check open ports, active connections, firewall rules, and DNS resolution for google.com
```

### What to narrate:
- "Now we switch to the **NetOps Specialist** — it uses networking-specific tools like `ss`, `ip`, `dig`, `ufw`"
- "Notice the plan is different from what a general agent would generate — it's more targeted"
- "This demonstrates **multi-agent specialization** — the same query yields different plans from different agents"

---

## Demo Scenario 3: Database Agent — Install & Configure PostgreSQL
> **Shows**: Full automation of toil task, package installation, service management

| Setting | Value |
|---------|-------|
| **Agent** | `DB Administrator` |
| **Model** | `Llama 3.3 (70B)` |
| **Server** | `demo-ec2` |

### Prompt:
```
Install PostgreSQL 15 on this server, create a database called "demo_app" with user "demo_user" and password "securepass123", and verify the service is running
```

### What to narrate:
- "The **DB Administrator** agent understands database workflows"
- "It installs PostgreSQL, creates users, sets up the database — all in one prompt"
- "This normally takes an SRE 10-15 minutes of manual commands"
- After execution: "The summary confirms the database is running and accessible"

---

## Demo Scenario 4: Deployment Agent — Deploy Streamlit App
> **Shows**: Full application deployment pipeline, self-healing loop

| Setting | Value |
|---------|-------|
| **Agent** | `General SRE` |
| **Model** | `Llama 3.3 (70B)` |
| **Server** | `demo-ec2` |

### Prompt:
```
Clone the repository https://github.com/YashBaviskar1/Streamlit-App, install Python3 and pip, install the requirements from requirements.txt, and run the Streamlit app on port 8501 in the background using nohup
```

### What to narrate:
- "Now the most impressive demo — a **full deployment** from a single natural language command"
- "The agent plans: install git → clone repo → install python3-pip → pip install → run with nohup"
- Click **Execute Plan**
- **If `git clone` fails** because directory already exists (from a previous run), watch the **Agent Brain** panel:
  - "The self-healing loop activates — it detects the error, consults the planner, and generates a fix (`rm -rf` then retry clone)"
  - "This is **autonomous error recovery** — no human intervention needed"
- "The app is now live at `http://<EC2-IP>:8501`"

> [!TIP]
> If you want to guarantee the self-healing demo triggers, run the deployment once beforehand. The second run will fail on `git clone` (directory exists) and the agent will self-heal.

---

## Demo Scenario 5: Security Agent — Hardening Audit
> **Shows**: SecOps persona, compliance-aware planning

| Setting | Value |
|---------|-------|
| **Agent** | `SecOps Auditor` |
| **Model** | `Llama 3.3 (70B)` |
| **Server** | `demo-ec2` |

### Prompt:
```
Run a security audit: check for unauthorized SSH login attempts, list all users with sudo access, verify file permissions on /etc/shadow and /etc/passwd, and check if unattended-upgrades is enabled
```

### What to narrate:
- "The **SecOps Auditor** focuses on security hardening and compliance"
- "Notice it checks auth logs, sudo permissions, sensitive file permissions"
- "The compliance rules we seeded in Neo4j are injected into the agent's prompt — so the agent's plans are **compliance-aware**"

---

## Demo Scenario 6: Monitoring — Enable Real-Time Metrics
> **Shows**: One-click monitoring setup, Grafana integration

### Steps:
1. Go to **Monitoring** page (`/monitoring`)
2. Click **Enable Monitoring** on your `demo-ec2` server
3. Fill in AWS credentials:
   - Access Key, Secret Key, Region, Instance ID
4. Click **Enable** → This will:
   - Open port 9100 on the EC2 security group
   - SSH in and install Node Exporter
   - Register the target in Prometheus
5. Open **Grafana** at `http://localhost:3001` → The AOSS dashboard should show EC2 metrics

### What to narrate:
- "One-click monitoring setup — the platform handles AWS security groups, installs the agent, and configures Prometheus automatically"
- "Grafana displays real-time CPU, memory, disk, and network metrics"

---

## Demo Scenario 7: Compliance — Graph-Based Policy Engine
> **Shows**: Neo4j compliance graph, rule enforcement

### Steps:
1. Go to **Compliance** page → Show the seeded rules
2. Add a custom rule via the UI:
   - **Name**: `SEC-1`
   - **Description**: `No root SSH login allowed`
   - **Type**: `forbidden`
3. Go back to **Orchestrate** → Run with **General SRE** agent:

### Prompt:
```
Check the server status and list all running services
```

### What to narrate:
- "Before executing, the planner queries Neo4j for all active compliance rules"
- "These rules are injected into the LLM's system prompt, so the agent **won't suggest forbidden operations**"
- "This is the **Compliance-as-Code** layer — policies stored in a knowledge graph, enforced at planning time"

---

## Recommended Demo Flow (15 min)

| Time | Scenario | Key Feature |
|------|----------|-------------|
| 0:00 | Pre-setup walkthrough | Architecture overview |
| 1:00 | Scenario 1 — Health Check | Basic agent + streaming execution |
| 3:00 | Scenario 2 — Network Audit | Multi-agent specialization |
| 5:00 | Scenario 4 — Deploy Streamlit | Full deployment + **Self-Healing** ⭐ |
| 9:00 | Scenario 7 — Compliance | Neo4j graph + compliance-aware planning |
| 12:00 | Scenario 6 — Monitoring | Grafana + one-click setup |
| 14:00 | Q&A | |

> [!TIP]
> **Star moments** to emphasize:
> 1. 🧠 **Self-Healing Loop** — The agent brain panel lighting up during failure recovery
> 2. 🔄 **Agent Specialization** — Same query, different agent, different plan
> 3. 📊 **Compliance Graph** — Neo4j rules enforced at LLM planning time
> 4. 📈 **One-Click Monitoring** — AWS + SSH + Prometheus automated end-to-end
