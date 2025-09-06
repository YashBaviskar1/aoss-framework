// frontend/src/components/FileList.jsx
import React, { useEffect, useState } from "react";
import { listDocuments, deleteDocument } from "../api/api";

export default function FileList({ onSelect }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const d = await listDocuments();
      setDocs(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const remove = async (name) => {
    if (!confirm(`Delete ${name}? This removes stored file and vectors.`)) return;
    try {
      await deleteDocument(name);
      refresh();
    } catch (err) {
      console.error(err);
      alert("Delete failed");
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-2">Indexed Documents</h3>
      {loading ? <div>Loading...</div> : (
        <ul className="space-y-2">
          {docs.map((d) => (
            <li key={d} className="flex justify-between items-center">
              <button onClick={() => onSelect && onSelect(d)} className="text-left">{d}</button>
              <div>
                <button className="text-sm text-red-600" onClick={() => remove(d)}>Delete</button>
              </div>
            </li>
          ))}
          {docs.length === 0 && <li className="text-gray-500">No documents yet.</li>}
        </ul>
      )}
      <div className="mt-2"><button onClick={refresh} className="text-xs text-gray-600">Refresh</button></div>
    </div>
  );
}
