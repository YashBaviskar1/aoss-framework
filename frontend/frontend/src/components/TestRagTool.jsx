import { useState } from "react";
import { testRag } from "../api/api.js";

export default function TestRagTool() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const data = await testRag(query);
    setResults(data.chunks || []);
  };

  return (
    <div className="p-4 border rounded-lg mt-4">
      <h2 className="font-bold text-lg mb-2">Test RAG Search</h2>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="border px-2 py-1 mr-2"
        placeholder="Enter query..."
      />
      <button
        onClick={handleSearch}
        className="bg-purple-500 text-white px-3 py-1 rounded"
      >
        Search
      </button>

      {results.length > 0 && (
        <ul className="mt-4">
          {results.map((chunk, idx) => (
            <li key={idx} className="border p-2 mb-2">
              <strong>{chunk.doc_name} - Page {chunk.page}</strong>
              <p>{chunk.text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
