import UploadPanel from "./components/UploadPanel";
import DocumentList from "./components/DocumentList";
import ComplianceViewer from "./components/ComplianceViewer";
import TestRagTool from "./components/TestRagTool";

export default function App() {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Compliance Document Manager</h1>
      <UploadPanel />
      <DocumentList />
      <ComplianceViewer />
      <TestRagTool />
    </div>
  );
}
