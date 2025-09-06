import { useEffect, useState } from "react";
import { listDocuments, deleteDocument } from "../api/api";

export default function DocumentList() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      // Handle both API formats: array or {documents: []}
      const documents = Array.isArray(data)
        ? data
        : data?.documents && Array.isArray(data.documents)
        ? data.documents
        : [];
      setDocs(documents);
    } catch (err) {
      console.error("Error fetching documents:", err);
      setError("Failed to load documents.");
      setDocs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await deleteDocument(docId);
      fetchDocs();
    } catch (err) {
      console.error("Error deleting document:", err);
      setError("Failed to delete document.");
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  return (
    <div className="p-4 border rounded-lg mt-4">
      <h2 className="font-bold text-lg mb-2">Uploaded Documents</h2>

      {loading && <p className="text-gray-500">Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && docs.length === 0 && (
        <p className="text-gray-500">No documents uploaded yet.</p>
      )}

      {!loading && docs.length > 0 && (
        <ul>
          {docs.map((doc) => (
            <li
              key={doc.id}
              className="flex justify-between items-center border-b py-2"
            >
              <span>{doc.filename}</span>
              <button
                className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
                onClick={() => handleDelete(doc.id)}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
