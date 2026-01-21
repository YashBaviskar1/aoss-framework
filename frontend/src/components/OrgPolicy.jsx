import { useState } from "react";
import { Building2, Shield, AlertTriangle } from "lucide-react";

export default function OrgPolicy() {
  const [role, setRole] = useState("");
  const [action, setAction] = useState("");
  const [ruleType, setRuleType] = useState("ALLOW");
  const [approvalAction, setApprovalAction] = useState("");
  const [scopeAction, setScopeAction] = useState("");
  const [scope, setScope] = useState("SINGLE_RESOURCE");

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-10">
      <h1 className="text-3xl font-bold flex items-center gap-2">
        <Building2 className="w-7 h-7 text-primary" />
        Organizational Policy
      </h1>

      {/* Roles */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2">Define Role</h2>
          <input
            className="input input-bordered"
            placeholder="Role name (e.g. SRE, Intern)"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <button className="btn btn-primary mt-2">
            Save Role
          </button>
        </div>
      </section>

      {/* Role Permissions */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2">Role Permissions</h2>
          <input
            className="input input-bordered mb-2"
            placeholder="Role"
            onChange={(e) => setRole(e.target.value)}
          />
          <input
            className="input input-bordered mb-2"
            placeholder="Action (e.g. DELETE_LOGS)"
            onChange={(e) => setAction(e.target.value)}
          />
          <select
            className="select select-bordered mb-2"
            onChange={(e) => setRuleType(e.target.value)}
          >
            <option value="ALLOW">Allow</option>
            <option value="FORBID">Forbid</option>
          </select>
          <button className="btn btn-primary">Apply Rule</button>
        </div>
      </section>

      {/* Approval */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2 flex items-center gap-2">
            <Shield className="w-5 h-5" /> Approval Requirement
          </h2>
          <input
            className="input input-bordered mb-2"
            placeholder="Action"
            onChange={(e) => setApprovalAction(e.target.value)}
          />
          <button className="btn btn-warning">
            Require Approval
          </button>
        </div>
      </section>

      {/* Blast Radius */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" /> Blast Radius
          </h2>
          <input
            className="input input-bordered mb-2"
            placeholder="Action"
            onChange={(e) => setScopeAction(e.target.value)}
          />
          <select
            className="select select-bordered mb-2"
            onChange={(e) => setScope(e.target.value)}
          >
            <option>SINGLE_RESOURCE</option>
            <option>MULTI_RESOURCE</option>
            <option>GLOBAL</option>
          </select>
          <button className="btn btn-primary">Set Scope</button>
        </div>
      </section>
    </div>
  );
}
