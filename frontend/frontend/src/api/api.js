const BASE_URL = "http://localhost:8000";

async function handleJSONResponse(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new Error("Invalid server response: " + text);
  }
}

// ---------------------------
// Document Upload / List / Delete
// ---------------------------
export async function uploadDocument(file) {
  const fm = new FormData();
  fm.append("file", file);
  const res = await fetch(`${BASE_URL}/upload`, { method: "POST", body: fm });
  return handleJSONResponse(res);
}

export async function listDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  return handleJSONResponse(res);
}

export async function deleteDocument(filename) {
  const res = await fetch(`${BASE_URL}/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });
  return handleJSONResponse(res);
}

// ---------------------------
// Rules
// ---------------------------
export async function fetchRules(filename) {
  const res = await fetch(`${BASE_URL}/fetch_rules/${encodeURIComponent(filename)}`, {
    method: "POST",
  });
  return handleJSONResponse(res);
}

export async function getRules(filename) {
  const url = filename
    ? `${BASE_URL}/rules?filename=${encodeURIComponent(filename)}`
    : `${BASE_URL}/rules`;
  const res = await fetch(url);
  return handleJSONResponse(res);
}

export async function addRule(filename, ruleType, ruleValue) {
  const params = new URLSearchParams({
    filename,
    rule_type: ruleType,
    rule_value: ruleValue,
  });
  const res = await fetch(`${BASE_URL}/rules?${params.toString()}`, {
    method: "POST",
  });
  return handleJSONResponse(res);
}

export async function deleteRule(filename, ruleType, ruleValue) {
  const params = new URLSearchParams({
    filename,
    rule_type: ruleType,
    rule_value: ruleValue,
  });
  const res = await fetch(`${BASE_URL}/rules?${params.toString()}`, {
    method: "DELETE",
  });
  return handleJSONResponse(res);
}

// ---------------------------
// Index Document
// ---------------------------
export async function indexDocument(filename) {
  const res = await fetch(`${BASE_URL}/index/${encodeURIComponent(filename)}`, {
    method: "POST",
  });
  return handleJSONResponse(res);
}

// ---------------------------
// RAG Query
// ---------------------------
export async function testRag(query, filename) {
  const res = await fetch(`${BASE_URL}/rag/${encodeURIComponent(filename)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleJSONResponse(res);
}
