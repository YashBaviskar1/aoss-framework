# backend/main.py
import os
import shutil
import uuid
import yaml
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Chroma vector DB
from chromadb import PersistentClient

# ---------------- Config ----------------
UPLOAD_DIR = "uploads"
POLICY_DIR = "policies"             # YAML-based policies
CHROMA_DIR = "chroma_store"
CHROMA_COLLECTION = "documents"
MAX_FILE_SIZE_MB = 200

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(POLICY_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="Compliance Document Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

chroma_client = PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

progress_store: Dict[str, str] = {}
upload_meta: Dict[str, dict] = {}

# ---------------- Models ----------------
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Policy(BaseModel):
    id: str
    rule: str
    severity: str = "medium"
    category: str

class ManualPolicy(BaseModel):
    id: str
    text: str
    severity: Optional[str] = "medium"
    category: Optional[str] = "manual"

# ---------------- Helpers: Policies (YAML) ----------------
def _agent_yaml_path(agent: str) -> str:
    return os.path.join(POLICY_DIR, f"{agent}.yaml")

def load_policies_from_yaml(agent: str) -> List[Dict[str, Any]]:
    """Load policies from policies/{agent}.yaml under key '{agent}_policies'."""
    path = _agent_yaml_path(agent)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    key = f"{agent}_policies"
    return data.get(key, [])

def save_policies_to_yaml(agent: str, policies: List[Dict[str, Any]]):
    """Save policies back into policies/{agent}.yaml under key '{agent}_policies'."""
    path = _agent_yaml_path(agent)
    key = f"{agent}_policies"
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump({key: policies}, f, sort_keys=False, allow_unicode=True)

# Generic manual policies file (frontend may call /policies without agent)
MANUAL_POLICIES_FILE = os.path.join(POLICY_DIR, "manual.yaml")

def load_manual_policies() -> List[Dict[str, Any]]:
    if not os.path.exists(MANUAL_POLICIES_FILE):
        return []
    with open(MANUAL_POLICIES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("policies", [])

def save_manual_policies(policies: List[Dict[str, Any]]):
    with open(MANUAL_POLICIES_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump({"policies": policies}, f, sort_keys=False, allow_unicode=True)

# ---------------- Helpers: Document text extraction ----------------
def read_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF support not installed. Install 'pymupdf'. Error: {e}",
            )
        text_chunks = []
        with fitz.open(path) as doc:
            for page in doc:
                text_chunks.append(page.get_text("text"))
        return "\n".join(text_chunks)

    elif ext == ".docx":
        try:
            import docx  # python-docx
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"DOCX support not installed. Install 'python-docx'. Error: {e}",
            )
        d = docx.Document(path)
        return "\n".join([p.text for p in d.paragraphs if p.text.strip()])

    elif ext in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

# ---------------- Helpers: Rule extraction (heuristic) ----------------
_RULE_LINE_RE = re.compile(
    r"\b(must|should|required|shall|prohibit|forbid|not\s+allowed|deny|disallow)\b",
    flags=re.IGNORECASE,
)

def extract_rules_from_text(text: str) -> List[Dict[str, str]]:
    """
    Simple heuristic:
    - Break lines
    - Keep lines that look like requirements (contain must/should/…)
    - Normalize bullets
    """
    rules: List[Dict[str, str]] = []
    lines = text.splitlines()
    for idx, raw in enumerate(lines):
        line = raw.strip(" •-*>\t")
        if not line:
            continue
        if _RULE_LINE_RE.search(line):
            rules.append(
                {
                    "section": f"Line {idx+1}",
                    "clause": f"C{idx+1}",
                    "requirement": line,
                }
            )
    return rules

# ---------------- Routes ----------------
@app.get("/")
def root():
    return {
        "message": "API running",
        "endpoints": [
            "/upload",
            "/documents",
            "/documents/{doc_id}",
            "/status/{upload_id}",
            "/test-rag",
            "/rules/{doc_id}",
            "/policies/{agent}",
            "/policies",
            "/reset_index",
        ],
    }

# -------- Upload Handling (unchanged) --------
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_id = str(uuid.uuid4())
    progress_store[upload_id] = "Queued"
    meta_list = []

    for f in files:
        f.file.seek(0, os.SEEK_END)
        size = f.file.tell()
        f.file.seek(0)
        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{f.filename} exceeds max size")
        dest = os.path.join(UPLOAD_DIR, f.filename)
        i = 1
        # Avoid overwriting
        while os.path.exists(dest):
            name, ext = os.path.splitext(f.filename)
            dest = os.path.join(UPLOAD_DIR, f"{name}_{i}{ext}")
            i += 1
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        meta_list.append(
            {
                "filename": os.path.basename(dest),
                "size": size,
                "type": os.path.splitext(dest)[1].lower().lstrip("."),
                "uploaded_at": datetime.utcnow().isoformat() + "Z",
            }
        )

    upload_meta[upload_id] = {"files": meta_list, "created_at": datetime.utcnow().isoformat() + "Z"}
    progress_store[upload_id] = "Uploaded"

    return {"upload_id": upload_id, "files": meta_list}

@app.get("/status/{upload_id}")
def status(upload_id: str):
    return {
        "upload_id": upload_id,
        "status": progress_store.get(upload_id, "unknown"),
        "meta": upload_meta.get(upload_id),
    }

@app.get("/documents")
def list_documents():
    files = []
    for fname in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, fname)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        files.append(
            {
                "id": fname,                # id is the filename
                "filename": fname,
                "size": stat.st_size,
                "type": os.path.splitext(fname)[1].lower().lstrip("."),
                "uploaded_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
            }
        )
    return {"documents": files}

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    path = os.path.join(UPLOAD_DIR, doc_id)
    if os.path.exists(path):
        os.remove(path)
    try:
        collection.delete(where={"source": doc_id})
    except Exception:
        pass
    return {"deleted": doc_id}

# -------- RAG Test (unchanged) --------
@app.post("/test-rag")
def test_rag(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    try:
        res = collection.query(
            query_texts=[req.query],
            n_results=req.top_k,
            include=["metadatas", "documents"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return {
            "query": req.query,
            "results": [{"document": d, "metadata": m} for d, m in zip(docs, metas)],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chroma query failed: {e}")

# -------- Rules Extraction (RESTORED & ROBUST) --------
@app.get("/rules/{doc_id}")
def extract_rules(doc_id: str):
    """
    doc_id is the filename as returned by /documents.
    Reads the uploaded file, extracts rule-like lines, and returns JSON.
    """
    path = os.path.join(UPLOAD_DIR, doc_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        text = read_text_from_file(path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read document: {e}")

    rules = extract_rules_from_text(text)
    return {"doc_id": doc_id, "rules": rules}

# -------- Agent-scoped Policy Management (unchanged) --------
@app.get("/policies/{agent}")
def get_policies(agent: str):
    policies = load_policies_from_yaml(agent)
    return {"agent": agent, "policies": policies}

@app.post("/policies/{agent}")
def add_policy(agent: str, policy: Policy):
    policies = load_policies_from_yaml(agent)
    policies.append(policy.dict())
    save_policies_to_yaml(agent, policies)
    # Index into Chroma for retrieval (optional)
    try:
        collection.add(
            documents=[policy.rule],
            metadatas=[{"id": policy.id, "category": policy.category, "agent": agent, "source": "policy"}],
            ids=[policy.id],
        )
    except Exception as e:
        logger.warning(f"Chroma add failed for policy {policy.id}: {e}")
    return {"message": "Policy added", "policy": policy}

@app.put("/policies/{agent}/{policy_id}")
def update_policy(agent: str, policy_id: str, updated: Policy):
    policies = load_policies_from_yaml(agent)
    for idx, p in enumerate(policies):
        if p.get("id") == policy_id:
            policies[idx] = updated.dict()
            save_policies_to_yaml(agent, policies)
            return {"message": "Policy updated", "policy": updated}
    raise HTTPException(status_code=404, detail="Policy not found")

@app.delete("/policies/{agent}/{policy_id}")
def delete_policy(agent: str, policy_id: str):
    policies = load_policies_from_yaml(agent)
    new_policies = [p for p in policies if p.get("id") != policy_id]
    if len(new_policies) == len(policies):
        raise HTTPException(status_code=404, detail="Policy not found")
    save_policies_to_yaml(agent, new_policies)
    try:
        collection.delete(ids=[policy_id])
    except Exception:
        pass
    return {"message": "Policy deleted", "id": policy_id}

# -------- Generic Manual Policies (optional for UI without {agent}) --------
@app.get("/policies")
def get_manual_policies():
    return {"policies": load_manual_policies()}

@app.post("/policies")
def add_manual_policy(item: ManualPolicy):
    policies = load_manual_policies()
    policies.append(item.dict())
    save_manual_policies(policies)
    # Optional index
    try:
        collection.add(
            documents=[item.text],
            metadatas=[{"id": item.id, "category": item.category, "source": "manual-policy"}],
            ids=[item.id],
        )
    except Exception as e:
        logger.warning(f"Chroma add failed for manual policy {item.id}: {e}")
    return {"message": "Policy added", "policy": item}

@app.delete("/policies/{policy_id}")
def delete_manual_policy(policy_id: str):
    policies = load_manual_policies()
    new_policies = [p for p in policies if p.get("id") != policy_id]
    if len(new_policies) == len(policies):
        raise HTTPException(status_code=404, detail="Policy not found")
    save_manual_policies(new_policies)
    try:
        collection.delete(ids=[policy_id])
    except Exception:
        pass
    return {"message": "Policy deleted", "id": policy_id}

# -------- Index reset (unchanged) --------
@app.post("/reset_index")
def reset_index():
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    global chroma_client, collection
    chroma_client = PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
    return {"message": "Index reset"}
