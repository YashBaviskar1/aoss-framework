import { useState } from "react";
import { Cpu, AlertCircle, Snowflake } from "lucide-react";

export default function SreSafety() {
  const [service, setService] = useState("");
  const [env, setEnv] = useState("prod");
  // New state
  const [action, setAction] = useState("");
  const [risk, setRisk] = useState("LOW");
  const [needs_approval, setNeedsApproval] = useState(false);

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-10">
      <h1 className="text-3xl font-bold flex items-center gap-2">
        <Cpu className="w-7 h-7 text-primary" />
        Platform / SRE Safety
      </h1>

      {/* Service Environment */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2">Service Environment</h2>
          <input
            className="input input-bordered mb-2"
            placeholder="Service name"
            onChange={(e) => setService(e.target.value)}
          />
          <select className="select select-bordered mb-2">
            <option>prod</option>
            <option>staging</option>
            <option>dev</option>
          </select>
          <button className="btn btn-primary">Save</button>
        </div>
      </section>

      {/* Action Risk */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-semibold">Action Risk</h2>
            <button
              onClick={() => {
                setService("payment-gateway");
                setEnv("prod");
                // We need state for action/risk too, adding below
                setAction("restart");
                setRisk("HIGH");
                setNeedsApproval(true);
              }}
              className="btn btn-xs btn-outline"
            >
              Populate Example
            </button>
          </div>

          <input
            className="input input-bordered mb-2"
            placeholder="Action"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          />
          <select
            className="select select-bordered mb-2"
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
          >
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
          </select>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="checkbox"
              checked={needs_approval}
              onChange={(e) => setNeedsApproval(e.target.checked)}
            />
            Needs Approval
          </label>

          <button
            className="btn btn-primary mt-4"
            onClick={async () => {
              try {
                await fetch("http://localhost:8000/api/compliance/sre-safety", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    service: service || "default-service",
                    env: env || "prod",
                    action: action || "restart",
                    risk: risk || "LOW",
                    needs_approval: needs_approval
                  })
                });
                alert("Safety Rule Saved!");
              } catch (e) {
                alert("Error saving rule");
              }
            }}
          >
            Save Risk Rule
          </button>
        </div>
      </section>

      {/* Incident */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" /> Declare Incident
          </h2>
          <input className="input input-bordered mb-2" placeholder="Incident ID" />
          <input className="input input-bordered mb-2" placeholder="Service" />
          <select className="select select-bordered mb-2">
            <option>SEV-1</option>
            <option>SEV-2</option>
          </select>
        </div>
      </section>

      {/* Freeze */}
      <section className="card bg-base-100 border border-base-300">
        <div className="card-body">
          <h2 className="font-semibold mb-2 flex items-center gap-2">
            <Snowflake className="w-5 h-5" /> Change Freeze
          </h2>
          <input className="input input-bordered mb-2" placeholder="Window ID" />
          <input className="input input-bordered mb-2" placeholder="Environment" />
          <input className="input input-bordered mb-2" placeholder="Start ISO" />
          <input className="input input-bordered mb-2" placeholder="End ISO" />
        </div>
      </section>
    </div>
  );
}
