// ComplianceViewer.jsx
import { useEffect, useState } from "react";
import { getRules, addRule, deleteRule, fetchRules, indexDocument } from "../api/api";

export default function ComplianceViewer({ selectedDoc }) {
  const [rules, setRules] = useState({ allowed: [], forbidden: [], required: [] });
  const [newRule, setNewRule] = useState("");
  const [newType, setNewType] = useState("forbidden");
  const [loading, setLoading] = useState(false);

  async function loadRules() {
    if (!selectedDoc) {
      setRules({ allowed: [], forbidden: [], required: [] });
      return;
    }
    try {
      const res = await getRules(selectedDoc);
      setRules(res.rules || { allowed: [], forbidden: [], required: [] });
    } catch (err) {
      console.error("Failed to load rules:", err);
      setRules({ allowed: [], forbidden: [], required: [] });
      alert("Failed to load rules for the selected document.");
    }
  }

  useEffect(() => {
    loadRules();
  }, [selectedDoc]);

  async function handleFetchRules() {
    if (!selectedDoc) {
      alert("Select a document first.");
      return;
    }
    setLoading(true);
    try {
      await fetchRules(selectedDoc);
      await loadRules();
      alert("Rules extracted and saved. Check the list below.");
    } catch (err) {
      console.error("Error fetching rules:", err);
      alert("Failed to fetch rules. Make sure the PDF is uploaded.");
    } finally {
      setLoading(false);
    }
  }

  async function handleIndex() {
    if (!selectedDoc) {
      alert("Select a document first.");
      return;
    }
    setLoading(true);
    try {
      const res = await indexDocument(selectedDoc);
      alert(`Document indexed successfully: ${res.result?.chunks_indexed || "N/A"} chunks`);
    } catch (err) {
      console.error("Indexing failed:", err);
      alert("Indexing failed: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    if (!selectedDoc || !newRule.trim()) {
      alert("Select a document and enter a rule.");
      return;
    }
    setLoading(true);
    try {
      await addRule(selectedDoc, newType, newRule.trim());
      setNewRule("");
      await loadRules();
    } catch (err) {
      console.error("Failed to add rule:", err);
      alert("Failed to add rule.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(type, value) {
    if (!selectedDoc) return;
    setLoading(true);
    try {
      await deleteRule(selectedDoc, type, value);
      await loadRules();
    } catch (err) {
      console.error("Failed to delete rule:", err);
      alert("Failed to delete rule.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h3>Compliance Viewer</h3>

      <div style={{ marginBottom: "16px" }}>
        <button onClick={handleFetchRules} disabled={!selectedDoc || loading}>
          Fetch Rules (extract from PDF)
        </button>
        <button onClick={handleIndex} disabled={!selectedDoc || loading} style={{ marginLeft: "8px" }}>
          Index Document
        </button>
      </div>

      <div style={{ marginTop: "16px" }}>
        {["allowed", "forbidden", "required"].map((type) => (
          <div key={type} style={{ border: "1px solid #ddd", margin: "8px 0", padding: "8px" }}>
            <h4>{type.charAt(0).toUpperCase() + type.slice(1)}</h4>
            <ul>
              {(rules[type] || []).map((r, idx) => (
                <li key={idx}>
                  {r}{" "}
                  <button onClick={() => handleDelete(type, r)} style={{ marginLeft: "8px" }} disabled={loading}>
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "16px" }}>
        <h4>Add Rule to Selected Document</h4>
        <input
          type="text"
          value={newRule}
          onChange={(e) => setNewRule(e.target.value)}
          placeholder="Rule text (e.g. rm -rf / forbidden)"
        />
        <select value={newType} onChange={(e) => setNewType(e.target.value)} style={{ marginLeft: "8px" }}>
          <option value="forbidden">forbidden</option>
          <option value="allowed">allowed</option>
          <option value="required">required</option>
        </select>
        <button onClick={handleAdd} disabled={!selectedDoc || !newRule.trim() || loading} style={{ marginLeft: "8px" }}>
          Add
        </button>
      </div>
    </div>
  );
}
