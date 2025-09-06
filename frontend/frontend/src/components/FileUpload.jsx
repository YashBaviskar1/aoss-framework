// frontend/src/components/FileUpload.jsx
import React, { useState } from "react";
import { uploadFilesGetId, getStatus } from "../api/api";

export default function FileUpload({ onUploaded }) {
  const [files, setFiles] = useState([]);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const [uploadId, setUploadId] = useState(null);

  const handleFiles = (e) => {
    setFiles(Array.from(e.target.files));
  };

  const startPolling = (id) => {
    setUploadId(id);
    setStatusText("Queued for indexing...");
    const interval = setInterval(async () => {
      try {
        const s = await getStatus(id);
        setStatusText(s.status);
        if (s.status && (s.status.toLowerCase().includes("completed") || s.status.toLowerCase().includes("failed") || s.status.toLowerCase().startsWith("indexing failed") || s.status.toLowerCase().startsWith("embedding error"))) {
          clearInterval(interval);
          onUploaded && onUploaded(); // refresh file list
        }
      } catch (err) {
        console.error("status poll error", err);
        clearInterval(interval);
      }
    }, 2000);
  };

  const upload = async () => {
    if (!files.length) return alert("Select files first.");
    try {
      const data = await uploadFilesGetId(files, (e) => {
        if (e.total) setProgress(Math.round((e.loaded * 100) / e.total));
      });
      if (data.upload_id) {
        startPolling(data.upload_id);
      } else {
        alert("Upload response missing upload_id");
      }
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setProgress(0);
      setFiles([]);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-2">Upload Documents (.pdf, .md)</h3>
      <input type="file" multiple onChange={handleFiles} />
      <div className="mt-3 flex gap-2">
        <button onClick={upload} className="bg-blue-600 text-white px-4 py-2 rounded">Upload</button>
        <div className="flex-1">
          {progress > 0 && <div>Upload Progress: {progress}%</div>}
          {statusText && <div className="text-sm text-gray-600">Index status: {statusText}</div>}
        </div>
      </div>
    </div>
  );
}
