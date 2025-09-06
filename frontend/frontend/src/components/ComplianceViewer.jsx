import { useState, useEffect } from "react";
import {
  listDocuments,
  extractRules,
  getPolicies,
  addPolicy,
  deletePolicy,
} from "../api/api.js";

export default function ComplianceViewer() {
  const [docs, setDocs] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [rules, setRules] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingRules, setLoadingRules] = useState(false);
  const [error, setError] = useState(null);

  const [policies, setPolicies] = useState([]);
  const [newPolicy, setNewPolicy] = useState("");

  // Fetch documents on mount
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        setLoadingDocs(true);
        setError(null);
        const data = await listDocuments();
        const docArray = Array.isArray(data?.documents)
          ? data.documents
          : Array.isArray(data)
          ? data
          : [];
        setDocs(docArray);
      } catch (err) {
        console.error("Error loading documents:", err);
        setError("Failed to load documents.");
      } finally {
        setLoadingDocs(false);
      }
    };

    const fetchPolicies = async () => {
      try {
        const data = await getPolicies();
        setPolicies(Array.isArray(data?.policies) ? data.policies : []);
      } catch (err) {
        console.error("Error loading policies:", err);
      }
    };

    fetchDocs();
    fetchPolicies();
  }, []);

  // Fetch compliance rules
  const fetchRules = async () => {
    if (!selectedDoc) return;
    try {
      setLoadingRules(true);
      setError(null);
      const data = await extractRules(selectedDoc);
      setRules(Array.isArray(data?.rules) ? data.rules : []);
    } catch (err) {
      console.error("Error extracting rules:", err);
      setError("Failed to fetch compliance rules.");
    } finally {
      setLoadingRules(false);
    }
  };

  // Add new manual policy
  const handleAddPolicy = async () => {
    if (!newPolicy.trim()) return;
    try {
      const added = await addPolicy({ text: newPolicy });
      setPolicies((prev) => [...prev, added]);
      setNewPolicy("");
    } catch (err) {
      console.error("Error adding policy:", err);
    }
  };

  // Delete policy
  const handleDeletePolicy = async (id) => {
    try {
      await deletePolicy(id);
      setPolicies((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error("Error deleting policy:", err);
    }
  };

  return (
    <div className="p-4 border rounded-lg mt-4">
      <h2 className="font-bold text-lg mb-2">Compliance Rules</h2>

      {/* Document Selector */}
      <div className="flex gap-2 mb-3">
        <select
          onChange={(e) => setSelectedDoc(e.target.value)}
          value={selectedDoc}
          className="border px-2 py-1 rounded flex-grow"
        >
          <option value="">Select Document</option>
          {docs.map((doc) => (
            <option key={doc.filename} value={doc.filename}>
              {doc.filename || `Document`}
            </option>
          ))}
        </select>
        <button
          onClick={fetchRules}
          disabled={!selectedDoc || loadingRules}
          className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 disabled:opacity-50"
        >
          {loadingRules ? "Loading..." : "Fetch Rules"}
        </button>
      </div>

      {/* Loading / Error States */}
      {loadingDocs && <p className="text-gray-500">Loading documents...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {/* Rules Table */}
      {rules.length > 0 && (
        <table className="mt-4 border w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="border px-2 py-1 text-left">Section</th>
              <th className="border px-2 py-1 text-left">Clause</th>
              <th className="border px-2 py-1 text-left">Requirement</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="border px-2 py-1">{r?.section || "-"}</td>
                <td className="border px-2 py-1">{r?.clause || "-"}</td>
                <td className="border px-2 py-1">{r?.requirement || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* No rules found */}
      {!loadingRules && rules.length === 0 && selectedDoc && !error && (
        <p className="text-gray-500 mt-2">No rules found for this document.</p>
      )}

      {/* Manual Policy Management */}
      <div className="mt-6">
        <h3 className="font-semibold mb-2">Manual Policies</h3>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={newPolicy}
            onChange={(e) => setNewPolicy(e.target.value)}
            placeholder="Enter new policy rule..."
            className="border px-2 py-1 rounded flex-grow"
          />
          <button
            onClick={handleAddPolicy}
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
          >
            Add
          </button>
        </div>

        {policies.length > 0 ? (
          <ul className="list-disc pl-6">
            {policies.map((p) => (
              <li key={p.id} className="flex justify-between items-center">
                <span>{p.text}</span>
                <button
                  onClick={() => handleDeletePolicy(p.id)}
                  className="text-red-500 hover:underline ml-2"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No manual policies yet.</p>
        )}
      </div>
    </div>
  );
}
