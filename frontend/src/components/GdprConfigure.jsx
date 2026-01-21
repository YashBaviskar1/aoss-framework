import { useState } from "react";
import { ShieldCheck } from "lucide-react";

export default function GdprConfigure() {
  const [company, setCompany] = useState("Acme");

  return (
    <div className="min-h-screen bg-base-200 p-8 pt-24 text-base-content">
      <h1 className="text-3xl font-bold flex items-center gap-2 mb-8">
        <ShieldCheck className="w-7 h-7 text-blue-400" />
        GDPR Configuration
      </h1>

      {/* ================= RETENTION ================= */}
      <Section title="A. Retention Policy">
        <Input label="Service Name" />
        <CheckboxGroup
          label="Data Types"
          options={["log", "email", "ip", "user_id"]}
        />
        <Input label="Retention Days" type="number" />
      </Section>

      {/* ================= PROCESSING ACTIVITY ================= */}
      <Section title="B. Processing Activity & Purpose">
        <Input label="Service Name" />
        <Input label="Activity Name (e.g. auth-log-processing)" />
        <Select
          label="Purpose"
          options={[
            "authentication",
            "authorization",
            "billing",
            "monitoring",
            "debugging"
          ]}
        />
        <CheckboxGroup
          label="Data Types Used"
          options={["log", "email", "ip"]}
        />
      </Section>

      {/* ================= LEGAL BASIS ================= */}
      <Section title="C. Lawful Basis (Mandatory)">
        <RadioGroup
          label="Legal Basis"
          options={[
            "Contract",
            "Consent",
            "Legal obligation",
            "Legitimate interest"
          ]}
        />
      </Section>

      {/* ================= DATA MINIMIZATION ================= */}
      <Section title="D. Data Minimization">
        <Input label="Service Name" />
        <CheckboxGroup
          label="Allowed Data Categories"
          options={["log", "email", "ip", "user_id"]}
        />
      </Section>

      {/* ================= ERASURE ================= */}
      <Section title="E. Erasure Policy">
        <Input label="Erasure SLA (days)" type="number" />
      </Section>

      {/* ================= LOCALIZATION ================= */}
      <Section title="F. Data Localization">
        <Select
          label="Data Type"
          options={["log", "email", "ip", "user_id"]}
        />
        <Select
          label="Allowed Region"
          options={["EU", "US", "India"]}
        />
      </Section>

      <button className="btn btn-primary mt-6">
        Save GDPR Configuration
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

function Input({ label, type = "text" }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <input
        type={type}
        className="input input-bordered w-full bg-base-200"
      />
    </div>
  );
}

function Select({ label, options }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <select className="select select-bordered w-full bg-base-200">
        {options.map(o => (
          <option key={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}

function CheckboxGroup({ label, options }) {
  return (
    <div>
      <label className="text-sm">{label}</label>
      <div className="flex gap-4 flex-wrap mt-1">
        {options.map(o => (
          <label key={o} className="text-sm">
            <input type="checkbox" className="mr-1" /> {o}
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
