import React, { useState } from "react";

function TestRagTool() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const runQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch("http://localhost:8000/rag", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error("Error running RAG:", err);
      setResponse({ error: "Failed to fetch response" });
    } finally {
      setLoading(false);
    }
  };

  // helper to safely render arrays
  const renderList = (label, data, color = "black") => (
    <>
      <h3>{label}</h3>
      {Array.isArray(data) && data.length > 0 ? (
        <ul style={{ color }}>
          {data.map((item, idx) => (
            <li key={idx}>
              {typeof item === "string" ? item : JSON.stringify(item)}
            </li>
          ))}
        </ul>
      ) : typeof data === "string" ? (
        <pre>{data}</pre>
      ) : (
        <p>None</p>
      )}
    </>
  );

  return (
    <div style={{ padding: "20px", fontFamily: "monospace" }}>
      <h2>🔍 Test RAG Compliance</h2>

      {/* Input Box */}
      <div style={{ marginBottom: "15px" }}>
        <input
          type="text"
          placeholder="Enter your query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            padding: "8px",
            width: "300px",
            marginRight: "10px",
            border: "1px solid #ccc",
            borderRadius: "4px",
          }}
        />
        <button onClick={runQuery} disabled={loading}>
          {loading ? "Running..." : "Run"}
        </button>
      </div>

      {/* Show Response */}
      {response && (
        <div
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            borderRadius: "6px",
            background: "#fafafa",
          }}
        >
          {response.error ? (
            <p style={{ color: "red" }}>⚠️ {response.error}</p>
          ) : (
            <>
              <h3>📌 Query</h3>
              <pre>{response.query}</pre>

              <h3>📝 Planner Output (Raw)</h3>
              <pre>{JSON.stringify(response.planner_raw, null, 2)}</pre>

              {renderList("📂 Full Plan", response.plan)}
              {renderList("✅ Safe Plan", response.safe_plan, "green")}

              <h3>🚨 Violations</h3>
              {Array.isArray(response.violations) &&
              response.violations.length > 0 ? (
                <ul style={{ color: "red" }}>
                  {response.violations.map((v, idx) => (
                    <li key={idx}>
                      Command: <b>{v.command}</b> → Rule: <b>{v.rule}</b>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No violations.</p>
              )}

              <h3>📜 Rules Used</h3>
              <pre>{JSON.stringify(response.rules, null, 2)}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default TestRagTool;
