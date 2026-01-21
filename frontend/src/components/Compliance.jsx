import { ShieldCheck, Layers, Settings, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Compliance() {
  const navigate = useNavigate();

  const layers = [
    {
      title: "Regulatory Compliance (GDPR)",
      desc: "Configure data retention, purpose limitation, erasure SLA, and data locality.",
      path: "/compliance/gdpr",
      icon: ShieldCheck,
    },
    {
      title: "Organizational Policy",
      desc: "Define roles, allowed actions, approval rules, and blast radius limits.",
      path: "/compliance/org-policy",
      icon: Layers,
    },
    {
      title: "Platform / SRE Safety",
      desc: "Configure incidents, freeze windows, action risk, and environment safety.",
      path: "/compliance/sre-safety",
      icon: Settings,
    },
  ];

  return (
    <main className="p-8 pt-24 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Compliance</h1>
      <p className="text-base-content/60 mb-8">
        Configure graph-backed compliance layers that govern automation execution.
      </p>

      <div className="space-y-6">
        {layers.map((layer) => (
          <div
            key={layer.title}
            className="card bg-base-100 border border-base-300 shadow-sm"
          >
            <div className="card-body flex-row items-center justify-between">
              <div className="flex items-center gap-4">
                <layer.icon className="w-6 h-6 text-primary" />
                <div>
                  <h2 className="font-semibold text-lg">{layer.title}</h2>
                  <p className="text-sm text-base-content/60">{layer.desc}</p>
                </div>
              </div>

              <button
                onClick={() => navigate(layer.path)}
                className="btn btn-primary btn-sm gap-2"
              >
                Configure
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Customize rules (OLD UI) */}
      <div className="mt-10 pt-6 border-t border-base-300">
        <button
          onClick={() => navigate("/compliance/customize")}
          className="btn btn-outline"
        >
          Customize Rules (YAML)
        </button>
      </div>
    </main>
  );
}
