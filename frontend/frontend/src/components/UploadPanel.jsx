import { useState } from "react";
import { uploadDocuments, checkStatus } from "../api/api";

export default function UploadPanel() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async () => {
    if (files.length === 0) {
      setStatus("Please select at least one file.");
      return;
    }

    try {
      setIsUploading(true);
      setStatus("Uploading...");

      const data = await uploadDocuments(files);
      setStatus("Indexing in progress...");

      // Poll status endpoint until indexing completes
      let completed = false;
      while (!completed) {
        const statusData = await checkStatus(data.upload_id);
        const s = statusData.status.toLowerCase();
        if (s.includes("completed")) {
          setStatus("Upload & indexing completed ✅");
          completed = true;
        } else if (s.includes("failed")) {
          setStatus("Indexing failed ❌");
          completed = true;
        } else {
          setStatus(`Indexing... (${statusData.status})`);
          await new Promise((r) => setTimeout(r, 2000));
        }
      }

      setFiles([]); // clear selection after upload
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-4 bg-white shadow rounded">
      <h2 className="font-semibold mb-3">Upload Document(s)</h2>
      <input
        type="file"
        accept=".pdf,.md"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files))}
        disabled={isUploading}
      />
      <button
        onClick={handleUpload}
        disabled={files.length === 0 || isUploading}
        className={`ml-2 px-4 py-1 rounded text-white ${
          isUploading ? "bg-gray-400" : "bg-blue-500 hover:bg-blue-600"
        }`}
      >
        {isUploading ? "Uploading..." : "Upload"}
      </button>
      {status && <p className="mt-3 text-sm">{status}</p>}
    </div>
  );
}
