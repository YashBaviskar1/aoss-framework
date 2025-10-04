import { useState, useEffect } from "react";
import UploadPanel from "./components/UploadPanel";
import DocumentList from "./components/DocumentList";
import ComplianceViewer from "./components/ComplianceViewer";
import TestRagTool from "./components/TestRagTool";
import { listDocuments } from "./api/api";

export default function App() {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docs, setDocs] = useState([]);

  // Load documents on mount
  useEffect(() => {
    async function fetchDocs() {
      try {
        const res = await listDocuments();
        setDocs(res.documents || []);
      } catch (e) {
        console.error(e);
      }
    }
    fetchDocs();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2>AOSS Compliance UI</h2>

      <UploadPanel onUploaded={(newDocs) => setDocs(newDocs)} />

      <DocumentList docs={docs} onSelect={(name) => setSelectedDoc(name)} selectedDoc={selectedDoc} />

      <div style={{ display: "flex", gap: 20, marginTop: 20 }}>
        <div style={{ flex: 1 }}>
          <ComplianceViewer selectedDoc={selectedDoc} />
        </div>
        <div style={{ flex: 1 }}>
          <TestRagTool selectedDoc={selectedDoc} />
        </div>
      </div>

      <div style={{ marginTop: 20 }}>
        <strong>Selected doc:</strong> {selectedDoc || "None"}
      </div>
    </div>
  );
}
