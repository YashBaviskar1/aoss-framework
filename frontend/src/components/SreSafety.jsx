import { useState } from "react";
import { Cpu, AlertCircle, Snowflake } from "lucide-react";

export default function SreSafety() {
  const [service, setService] = useState("");
  const [env, setEnv] = useState("prod");

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
          <h2 className="font-semibold mb-2">Action Risk</h2>
          <input className="input input-bordered mb-2" placeholder="Action" />
          <select className="select select-bordered mb-2">
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
          </select>
          <label className="flex items-center gap-2">
            <input type="checkbox" className="checkbox" />
            Needs Approval
          </label>
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
