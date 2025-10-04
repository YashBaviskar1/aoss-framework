import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from compliance_utils import (
    extract_rules_from_pdf,
    get_all_rules,
    add_rule_to_file,
    delete_rule_from_file,
    UPLOADED_DIR,
    RULES_DIR
)

os.makedirs(UPLOADED_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

app = FastAPI(title="AOSS Compliance Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ----------------------------
# Upload PDF
# ----------------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    file_path = os.path.join(UPLOADED_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"filename": file.filename, "status": "uploaded"}


# ----------------------------
# List PDFs
# ----------------------------
@app.get("/documents")
async def list_documents():
    files = [f for f in os.listdir(UPLOADED_DIR) if f.endswith(".pdf")]
    return {"documents": files}


# ----------------------------
# Delete PDF
# ----------------------------
@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    file_path = os.path.join(UPLOADED_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        rules_file = os.path.join(RULES_DIR, f"{filename}.yml")
        if os.path.exists(rules_file):
            os.remove(rules_file)
        return {"message": "File and associated rules deleted"}
    raise HTTPException(status_code=404, detail="File not found")


# ----------------------------
# Fetch rules from PDF
# ----------------------------
# ----------------------------
# Fetch rules from PDF (debug raw LLM output)
# ----------------------------
@app.post("/fetch_rules/{filename}")
async def fetch_rules(filename: str):
    file_path = os.path.join(UPLOADED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get raw output
    from compliance_utils import call_llm
    from PyPDF2 import PdfReader
    import os
    
    reader = PdfReader(file_path)
    text = "".join(page.extract_text() or "" for page in reader.pages)
    
    prompt = f"Extract rules from this text (debug raw output):\n{text}"
    raw_output = call_llm(prompt)

    # Save exactly what LLM returns
    rules_file = os.path.join(RULES_DIR, f"{os.path.splitext(filename)[0]}.yml")
    with open(rules_file, "w", encoding="utf-8") as f:
        f.write(raw_output)
    
    return {"message": "Raw LLM output saved to YAML file", "raw_output": raw_output}

# ----------------------------
# Get rules
# ----------------------------
@app.get("/rules")
async def get_rules(filename: str):
    rules_file = os.path.join(RULES_DIR, f"{filename}.yml")
    if not os.path.exists(rules_file):
        raise HTTPException(status_code=404, detail="Rules file not found")
    data = get_all_rules(rules_file)
    return {"filename": filename, "rules": data}


# ----------------------------
# Add rule
# ----------------------------
@app.post("/rules")
async def add_rule(filename: str, rule_type: str, rule_value: str):
    rules_file = os.path.join(RULES_DIR, f"{filename}.yml")
    if not os.path.exists(rules_file):
        raise HTTPException(status_code=404, detail="Rules file not found")
    if rule_type not in ["allowed", "forbidden", "required"]:
        raise HTTPException(status_code=400, detail="Invalid rule type")
    add_rule_to_file(rules_file, rule_type, rule_value)
    return {"message": "Rule added successfully"}


# ----------------------------
# Delete rule
# ----------------------------
@app.delete("/rules")
async def delete_rule(filename: str, rule_type: str, rule_value: str):
    rules_file = os.path.join(RULES_DIR, f"{filename}.yml")
    if not os.path.exists(rules_file):
        raise HTTPException(status_code=404, detail="Rules file not found")
    if rule_type not in ["allowed", "forbidden", "required"]:
        raise HTTPException(status_code=400, detail="Invalid rule type")
    delete_rule_from_file(rules_file, rule_type, rule_value)
    return {"message": "Rule deleted successfully"}


# ----------------------------
# Index document (placeholder)
# ----------------------------
@app.post("/index/{filename}")
async def index_document(filename: str):
    file_path = os.path.join(UPLOADED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": f"Document {filename} indexed successfully"}


# ----------------------------
# RAG query (placeholder)
# ----------------------------
class QueryRequest(BaseModel):
    query: str

@app.post("/rag/{filename}")
async def rag_query(filename: str, query_req: QueryRequest):
    file_path = os.path.join(UPLOADED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return {"answer": f"RAG response placeholder for {filename}"}
