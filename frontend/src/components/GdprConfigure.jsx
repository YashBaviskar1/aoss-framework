import { useState } from "react";
import { ShieldCheck } from "lucide-react";

export default function GdprConfigure() {
  const [company, setCompany] = useState("Acme");

  // State for the form
  const [serviceName, setServiceName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [dataTypes, setDataTypes] = useState([]);
  const [region, setRegion] = useState("");
  const [loading, setLoading] = useState(false);

  // Test Data Autofill
  const fillTestData = () => {
    setServiceName("nginx-access-logs");
    setPurpose("monitoring");
    setDataTypes(["ip", "user_agent", "timestamp"]);
    setRegion("EU");
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const payload = {
        service_name: serviceName || "nginx-logs",
        purpose: purpose || "debugging",
        data_types: dataTypes.length ? dataTypes : ["ip"],
        region: region || "US"
      };

      const res = await fetch("http://localhost:8000/api/compliance/gdpr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        alert("GDPR Policy Saved to Graph!");
      } else {
        alert("Failed to save");
      }
    } catch (e) {
      console.error(e);
      alert("Error saving policy");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base-200 p-8 pt-24 text-base-content">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <ShieldCheck className="w-7 h-7 text-blue-400" />
          GDPR Configuration
        </h1>
        <button onClick={fillTestData} className="btn btn-outline btn-sm">
          Populate Example (Nginx)
        </button>
      </div>

      {/* ================= RETENTION ================= */}
      <Section title="A. Retention Policy">
        <Input
          label="Service Name"
          value={serviceName}
          onChange={e => setServiceName(e.target.value)}
        />
        <CheckboxGroup
          label="Data Types"
          options={["log", "email", "ip", "user_id", "user_agent", "timestamp"]}
          selected={dataTypes}
          onChange={setDataTypes}
        />
        <Input label="Retention Days" type="number" />
      </Section>

      {/* ================= PROCESSING ACTIVITY ================= */}
      <Section title="B. Processing Activity & Purpose">
        <Input label="Activity Name (e.g. auth-log-processing)" />
        <Select
          label="Purpose"
          value={purpose}
          onChange={e => setPurpose(e.target.value)}
          options={[
            "",
            "authentication",
            "authorization",
            "billing",
            "monitoring",
            "debugging"
          ]}
        />
        <Input
          label="Region (Data Locality)"
          value={region}
          onChange={e => setRegion(e.target.value)}
        />
      </Section>

      {/* ... Other sections omitted for brevity in demo ... */}

      <button onClick={handleSave} className="btn btn-primary mt-6" disabled={loading}>
        {loading ? "Saving..." : "Save GDPR Configuration"}
      </button>
    </div>
  );
}

/* ===== Small UI Helpers ===== */

function Section({ title, children }) {
  return (
    <div className="card bg-base-100 border border-base-300 shadow-md mb-6">
      <div className="card-body">
        <h2 className="card-title mb-4">{title}</h2>
        <div className="space-y-4">{children}</div>
      </div>
    </div>
  );
}

function Input({ label, type = "text", value, onChange }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        className="input input-bordered w-full bg-base-200"
      />
    </div>
  );
}

function Select({ label, options, value, onChange }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <select
        value={value}
        onChange={onChange}
        className="select select-bordered w-full bg-base-200"
      >
        <option disabled value="">Select...</option>
        {options.map(o => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}

function CheckboxGroup({ label, options, selected = [], onChange }) {
  const toggle = (opt) => {
    if (!onChange) return;
    if (selected.includes(opt)) {
      onChange(selected.filter(x => x !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  return (
    <div>
      <label className="text-sm">{label}</label>
      <div className="flex gap-4 flex-wrap mt-1">
        {options.map(o => (
          <label key={o} className="text-sm cursor-pointer flex items-center">
            <input
              type="checkbox"
              className="mr-2 checkbox checkbox-xs"
              checked={selected.includes(o)}
              onChange={() => toggle(o)}
            /> {o}
          </label>
        ))}
      </div>
    </div>
  );
}

function RadioGroup({ label, options }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <div className="flex gap-4 flex-wrap mt-1">
        {options.map(o => (
          <label key={o} className="text-sm">
            <input type="radio" name={label} className="mr-1" /> {o}
          </label>
        ))}
      </div>
    </div>
  );
}
