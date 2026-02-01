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
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-semibold">Role Permissions</h2>
            <button
              onClick={() => {
                setRole("SRE_Junior");
                setAction("DELETE_PROD_DB");
                setRuleType("FORBID");
              }}
              className="btn btn-xs btn-outline"
            >
              Populate Example
            </button>
          </div>

          <input
            className="input input-bordered mb-2"
            placeholder="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <input
            className="input input-bordered mb-2"
            placeholder="Action (e.g. DELETE_LOGS)"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          />
          <select
            className="select select-bordered mb-2"
            value={ruleType}
            onChange={(e) => setRuleType(e.target.value)}
          >
            <option value="ALLOW">Allow</option>
            <option value="FORBID">Forbid</option>
          </select>
          <button
            className="btn btn-primary"
            onClick={async () => {
              try {
                await fetch("http://localhost:8000/api/compliance/org-policy", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    role: role,
                    action: action,
                    resource: "ProductionDatabase", // mocking for now as input missing
                    effect: ruleType
                  })
                });
                alert("Policy Saved to Graph!");
              } catch (e) {
                alert("Error saving");
              }
            }}
          >
            Apply Rule
          </button>
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
