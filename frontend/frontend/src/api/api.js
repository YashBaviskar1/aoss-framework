const BASE_URL = "http://127.0.0.1:8000";

export async function uploadDocuments(files) {
  const formData = new FormData();
  for (let file of files) {
    formData.append("files", file); // matches backend List[UploadFile]
  }

  const res = await fetch(`${BASE_URL}/upload`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function checkStatus(uploadId) {
  const res = await fetch(`${BASE_URL}/status/${uploadId}`);
  if (!res.ok) throw new Error("Status check failed");
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  if (!res.ok) throw new Error("Fetching documents failed");
  const data = await res.json();
  return data.documents || data || [];
}

export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
}

export async function testRag(query) {
  const res = await fetch(`${BASE_URL}/test-rag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });
  if (!res.ok) throw new Error("Test RAG failed");
  return res.json();
}

export async function rag(query) {
  const res = await fetch(`${BASE_URL}/rag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });
  if (!res.ok) throw new Error("RAG failed");
  return res.json();
}

export async function extractRules(docId) {
  const res = await fetch(`${BASE_URL}/rules/${docId}`);
  if (!res.ok) throw new Error("Rules extraction failed");
  return res.json();
}

export async function resetIndex() {
  const res = await fetch(`${BASE_URL}/reset_index`, { method: "POST" });
  if (!res.ok) throw new Error("Reset index failed");
  return res.json();
}




// --- Policy APIs ---
export async function getPolicies(agent) {
  const res = await fetch(`${BASE_URL}/policies/${agent}`);
  if (!res.ok) throw new Error("Fetching policies failed");
  return res.json();
}

export async function addPolicy(agent, policy) {
  const res = await fetch(`${BASE_URL}/policies/${agent}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Adding policy failed");
  return res.json();
}

export async function updatePolicy(agent, policyId, policy) {
  const res = await fetch(`${BASE_URL}/policies/${agent}/${policyId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Updating policy failed");
  return res.json();
}

export async function deletePolicy(agent, policyId) {
  const res = await fetch(`${BASE_URL}/policies/${agent}/${policyId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Deleting policy failed");
  return res.json();
}
