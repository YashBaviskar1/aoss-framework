import React, { useState } from "react";
import { queryDocuments } from "../api/api";

export default function QueryBox() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const response = await queryDocuments(query);
      setResult(response);
    } catch (error) {
      console.error(error);
      alert("Search failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow p-4 rounded-md mt-6">
      <h2 className="text-lg font-bold mb-3">Search Documents</h2>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter search query"
        className="border p-2 w-full mb-3 rounded"
      />
      <button
        onClick={handleSearch}
        disabled={loading}
        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
      >
        {loading ? "Searching..." : "Search"}
      </button>
      {result && (
        <div className="mt-4 p-3 bg-gray-50 border rounded">
          <h3 className="font-semibold">Results:</h3>
          <pre className="text-sm">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
