// UploadPanel.jsx
import { useState } from "react";
import { uploadDocument, listDocuments } from "../api/api";

export default function UploadPanel({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleUpload() {
    if (!file) return alert("Choose a PDF file first");
    
    setLoading(true);
    setStatus("Uploading...");
    
    try {
      await uploadDocument(file);
      setStatus("Upload successful!");
      
      // Refresh document list
      const docs = await listDocuments();
      onUploaded(docs.documents || []);
      
      // Reset form
      setFile(null);
      document.querySelector('input[type="file"]').value = "";
      
    } catch (e) {
      console.error("Upload failed:", e);
      setStatus("Upload failed: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-xl font-bold mb-4">Upload Document</h3>
      
      <div className="space-y-4">
        <div>
          <input 
            type="file" 
            accept=".pdf"
            onChange={(e) => {
              setFile(e.target.files[0]);
              setStatus("");
            }}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <p className="text-xs text-gray-500 mt-1">Only PDF files are supported</p>
        </div>
        
        <button 
          onClick={handleUpload} 
          disabled={!file || loading}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? "Uploading..." : "Upload PDF"}
        </button>
        
        {status && (
          <div className={`p-3 rounded ${
            status.includes("failed") 
              ? "bg-red-100 text-red-700 border border-red-200" 
              : "bg-green-100 text-green-700 border border-green-200"
          }`}>
            {status}
          </div>
        )}
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        <p>📝 After uploading, you can:</p>
        <ul className="list-disc list-inside mt-1 space-y-1">
          <li>Select the document to view/edit rules</li>
          <li>Extract rules automatically using AI</li>
          <li>Index the document for RAG search</li>
          <li>Test compliance queries with AI</li>
        </ul>
      </div>
    </div>
  );
}