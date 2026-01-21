import { useState } from "react";
import { ShieldCheck, UploadCloud, FileText, Zap } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Server, BarChart3, Bot, Cpu } from "lucide-react";

function NavLink({ to, icon: Icon, children }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <li>
      <Link
        to={to}
        className={`
          flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-200
          ${isActive
            ? "bg-primary/10 text-primary font-semibold"
            : "text-base-content/70 hover:bg-base-200 hover:text-primary"
          }
        `}
      >
        <Icon className="w-5 h-5" />
        <span>{children}</span>
      </Link>
    </li>
  );
}

export default function Compliance() {
  const [docs, setDocs] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [rules, setRules] = useState({ allowed: [], forbidden: [], required: [] });
  const [newRule, setNewRule] = useState("");
  const [newType, setNewType] = useState("forbidden");
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  // ===== File Upload (local only) =====
  function handleUpload(file) {
    if (!file) return alert("Select a PDF first");
    const newDocs = [...docs, file.name];
    setDocs(newDocs);
    alert("File added successfully (frontend only)");
  }

  // ===== Add Rule =====
  function handleAddRule() {
    if (!selectedDoc || !newRule.trim()) return alert("Enter a rule");
    const updated = { ...rules };
    updated[newType] = [...updated[newType], newRule.trim()];
    setRules(updated);
    setNewRule("");
  }

  // ===== Delete Rule =====
  function handleDeleteRule(type, value) {
    const updated = { ...rules };
    updated[type] = updated[type].filter((r) => r !== value);
    setRules(updated);
  }

  // ===== Simulate Query Run =====
  function runQuery() {
    if (!query.trim()) return;
    setLoading(true);
    setTimeout(() => {
      setResponse({
        query,
        planner_raw: { mock: "Simulated RAG output (frontend only)" },
        violations: rules.forbidden.length
          ? [{ command: "delete-user", rule: rules.forbidden[0] }]
          : [],
      });
      setLoading(false);
    }, 1000);
  }

  return (
    <div className="flex min-h-screen bg-base-200 text-base-content">
      {/* ===== Sidebar ===== */}
      <aside className="w-64 bg-base-100 flex flex-col border-r border-base-300/50 pt-24 fixed h-full">
        {/* Logo */}
        <div className="flex items-center space-x-3 px-6 py-5 border-b border-base-300/50">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Cpu className="w-6 h-6 text-primary" />
          </div>
          <span className="text-xl font-bold">AOSS</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 overflow-y-auto">
          <ul className="space-y-2">
            <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
            <NavLink to="/services" icon={Server}>Services</NavLink>
            <NavLink to="/compliance" icon={ShieldCheck}>Compliance</NavLink>
            <NavLink to="/monitoring" icon={BarChart3}>Monitoring</NavLink>
            <NavLink to="/chat" icon={Bot}>Orchestrate</NavLink>
          </ul>
        </nav>

        {/* User Profile */}
        <div className="px-6 py-4 border-t border-base-300/50">
          <div className="flex items-center space-x-3">
            <div className="avatar placeholder">
              <div className="bg-neutral-focus text-neutral-content rounded-full w-10">
                <span>A</span>
              </div>
            </div>
            <div>
              <p className="font-semibold text-sm">Admin User</p>
              <p className="text-xs text-base-content/60">Lead SRE</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ===== Main Content ===== */}
      <main className="flex-1 p-8 pt-24 ml-64">
        <header className="mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-2 text-base-content">
            <ShieldCheck className="w-7 h-7 text-blue-400" /> Compliance
          </h1>
          <p className="text-base-content/60 mt-1">
            Manage compliance rules, upload policy documents, and test safe execution.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Upload Section */}
            <div className="card bg-base-100 shadow-md border border-base-300/50">
              <div className="card-body">
                <h2 className="card-title flex items-center gap-2">
                  <UploadCloud className="w-5 h-5 text-blue-400" /> Upload PDF
                </h2>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleUpload(e.target.files[0])}
                  className="mt-3 file-input file-input-bordered w-full bg-base-200 text-base-content border-base-300"
                />
              </div>
            </div>

            {/* Documents List */}
            <div className="card bg-base-100 shadow-md border border-base-300/50">
              <div className="card-body">
                <h2 className="card-title flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-400" /> Uploaded Documents
                </h2>
                <ul className="mt-4 space-y-2">
                  {docs.length > 0 ? (
                    docs.map((doc) => (
                      <li key={doc}>
                        <button
                          onClick={() => setSelectedDoc(doc)}
                          className={`w-full text-left px-4 py-2 rounded-lg ${
                            selectedDoc === doc
                              ? "bg-blue-600 text-white"
                              : "bg-base-200 hover:bg-base-300 text-base-content/70"
                          }`}
                        >
                          {doc}
                        </button>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-base-content/60">No documents uploaded</li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Middle Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Compliance Rules */}
            <div className="card bg-base-100 shadow-md border border-base-300/50">
              <div className="card-body">
                <h2 className="card-title flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-400" /> Compliance Rules
                </h2>

                <div className="mt-6 grid md:grid-cols-3 gap-4">
                  {["allowed", "forbidden", "required"].map((type) => (
                    <div key={type} className="border rounded-lg p-4 bg-base-200 border-base-300">
                      <h3 className="font-semibold capitalize mb-2">{type}</h3>
                      <ul className="space-y-1 text-sm">
                        {(rules[type] || []).length > 0 ? (
                          rules[type].map((r, idx) => (
                            <li
                              key={idx}
                              className="flex justify-between items-center bg-base-100 p-2 rounded-md border border-base-300"
                            >
                              <span>{r}</span>
                              <button
                                className="text-red-400 text-xs"
                                onClick={() => handleDeleteRule(type, r)}
                              >
                                Delete
                              </button>
                            </li>
                          ))
                        ) : (
                          <li className="text-base-content/60 text-sm">No rules</li>
                        )}
                      </ul>
                    </div>
                  ))}
                </div>

                {/* Add Rule */}
                <div className="mt-6 flex flex-wrap gap-3 items-center">
                  <input
                    type="text"
                    placeholder="Enter new rule..."
                    value={newRule}
                    onChange={(e) => setNewRule(e.target.value)}
                    className="input input-bordered w-full md:w-1/2 bg-base-200 text-base-content border-base-300"
                  />
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="select select-bordered bg-base-200 text-base-content border-base-300"
                  >
                    <option value="forbidden">forbidden</option>
                    <option value="allowed">allowed</option>
                    <option value="required">required</option>
                  </select>
                  <button
                    onClick={handleAddRule}
                    disabled={!selectedDoc || !newRule.trim()}
                    className="btn bg-blue-600 hover:bg-blue-700 border-none text-white"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Test RAG */}
            <div className="card bg-base-100 shadow-md border border-base-300/50">
              <div className="card-body">
                <h2 className="card-title flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-400" /> Test RAG Compliance
                </h2>

                <div className="mt-4 flex gap-3 flex-wrap">
                  <input
                    type="text"
                    placeholder="Enter your query..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="input input-bordered w-full md:w-2/3 bg-base-200 text-base-content border-base-300"
                  />
                  <button
                    onClick={runQuery}
                    disabled={loading}
                    className="btn bg-blue-600 hover:bg-blue-700 border-none text-white"
                  >
                    {loading ? "Running..." : "Run Query"}
                  </button>
                </div>

                {response && (
                  <div className="mt-6 p-4 bg-base-200 rounded-lg max-h-[400px] overflow-y-auto text-sm border border-base-300">
                    <h3 className="font-semibold">Query</h3>
                    <pre>{response.query}</pre>

                    <h3 className="font-semibold mt-2">Planner Output</h3>
                    <pre>{JSON.stringify(response.planner_raw, null, 2)}</pre>

                    <h3 className="font-semibold mt-2">Violations</h3>
                    {response.violations?.length > 0 ? (
                      <ul className="text-red-400 list-disc list-inside">
                        {response.violations.map((v, i) => (
                          <li key={i}>
                            Command: <b>{v.command}</b> → Rule: <b>{v.rule}</b>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-base-content/60">No violations.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}