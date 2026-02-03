import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useUser } from '@clerk/clerk-react';
import Navbar from './Navbar';
import {
  LayoutDashboard,
  Server,
  ShieldCheck,
  BarChart3,
  Bot,
  Cpu,
  Cloud,
  BrainCircuit,
  PackageCheck,
  FileText
} from 'lucide-react';

// --- Helper component for Sidebar Links ---
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
            ? 'bg-primary/10 text-primary font-semibold'
            : 'text-base-content/70 hover:bg-base-200 hover:text-primary'
          }
        `}
      >
        <Icon className="w-5 h-5" />
        <span>{children}</span>
      </Link>
    </li>
  );
}

// --- Mock Data ---
const components = [
  { name: 'Planner Agent', status: 'Active', version: '2.1.0', icon: BrainCircuit, description: 'Parses natural language queries and creates execution plans.' },
  { name: 'Deployment Agent', status: 'Active', version: '1.8.2', icon: PackageCheck, description: 'Executes system commands for deployments and configurations.' },
  { name: 'Logger Agent', status: 'Active', version: '3.0.1', icon: FileText, description: 'Monitors and logs all system activities for auditing.' },
];


export default function Dashboard() {
  const { user, isLoaded } = useUser();
  const [serverData, setServerData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isLoaded && user) {
      fetchServerData();
    }
  }, [isLoaded, user]);

  const fetchServerData = () => {
    fetch(`http://localhost:8000/api/dashboard/${user.id}`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then(data => {
        // Initialize status as 'Unknown' if not present
        const serversWithStatus = data.servers.map(s => ({ ...s, status: 'Unknown', statusMessage: '' }));
        setServerData(serversWithStatus);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching dashboard data:", err);
        setLoading(false);
      });
  };

  const handleTestConnection = async (serverId) => {
    // Update status to testing
    setServerData(prev => prev.map(s => s.id === serverId ? { ...s, status: 'Testing...' } : s));

    try {
      const res = await fetch(`http://localhost:8000/api/server/${serverId}/test-connection`, { method: 'POST' });
      const data = await res.json();

      setServerData(prev => prev.map(s =>
        s.id === serverId ? { ...s, status: data.status, statusMessage: data.message } : s
      ));
    } catch (error) {
      console.error("Connection test failed", error);
      setServerData(prev => prev.map(s =>
        s.id === serverId ? { ...s, status: 'Offline', statusMessage: 'Network Error' } : s
      ));
    }
  };

  return (
    <div className="flex min-h-screen bg-base-200">
      {/* ===== Sidebar ===== */}
      <aside className="w-64 bg-base-100 text-base-content flex flex-col border-r border-base-300/50 pt-24">
        {/* Logo */}
        <div className="flex items-center space-x-3 px-6 py-5 border-b border-base-300/50">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Cpu className="w-6 h-6 text-primary" />
          </div>
          <span className="text-xl font-bold">AOSS</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4">
          <ul className="space-y-2">
            <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
            <NavLink to="/services" icon={Server}>Services</NavLink>
            <NavLink to="/compliance" icon={ShieldCheck}>Compliance</NavLink>
            <NavLink to="/monitoring" icon={BarChart3}>Monitoring</NavLink>
            <NavLink to="/chat" icon={Bot}>Orchestrate</NavLink>
            <NavLink to="/reports" icon={FileText}>Reports</NavLink>
          </ul>
        </nav>

        {/* User Profile Footer */}
        <div className="px-6 py-4 border-t border-base-300/50">
          <div className="flex items-center space-x-3">
            <div className="avatar placeholder">
              <div className="bg-neutral-focus text-neutral-content rounded-full w-10">
                <span>{user?.firstName?.[0] || 'A'}</span>
              </div>
            </div>
            <div>
              <p className="font-semibold text-sm">{user?.fullName || 'User'}</p>
              <p className="text-xs text-base-content/60">Admin</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ===== Main Content ===== */}
      <main className="flex-1 p-8 overflow-y-auto pt-24">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-base-content">Dashboard</h1>
            <p className="text-base-content/60 mt-1">
              Overview of your connected infrastructure and system components.
            </p>
          </div>
          <Link to="/profile-setup" className="btn btn-primary gap-2">
            <Server className="w-4 h-4" />
            Add Server
          </Link>
        </header>

        {/* Connected Servers Section */}
        <section>
          <h2 className="text-xl font-semibold text-base-content mb-4">Connected Servers</h2>

          {loading ? (
            <div className="flex justify-center p-8">
              <span className="loading loading-spinner loading-lg"></span>
            </div>
          ) : serverData.length === 0 ? (
            <div className="text-center py-8 border-dashed border-2 border-base-300 rounded-xl">
              <p className="text-base-content/60">No servers connected yet.</p>
              <Link to="/profile-setup" className="btn btn-primary btn-sm mt-4">Connect Server</Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {serverData.map((server) => (
                <div key={server.id} className="card bg-base-100 shadow-md border border-base-300/50">
                  <div className="card-body">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="card-title text-base-content">{server.server_tag}</h3>
                        <p className="text-sm text-base-content/60 font-mono">{server.ip_address}</p>
                      </div>
                      <div className={`badge ${server.status === 'Online' ? 'badge-success' :
                        server.status === 'Offline' ? 'badge-error' :
                          server.status === 'Testing...' ? 'badge-warning' : 'badge-ghost'
                        } gap-2`}>
                        {server.status === 'Online' && <span className="w-2 h-2 bg-current rounded-full animate-ping absolute"></span>}
                        <span className="w-2 h-2 bg-current rounded-full"></span>
                        {server.status || 'Unknown'}
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-base-content/80">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-primary" />
                          <span>{server.hostname || 'Unknown Host'}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleTestConnection(server.id)}
                        className="btn btn-xs btn-outline btn-primary"
                        disabled={server.status === 'Testing...'}
                      >
                        {server.status === 'Testing...' ? 'Testing...' : 'Test Connection'}
                      </button>
                    </div>
                    {server.statusMessage && (
                      <p className={`text-xs mt-2 ${server.status === 'Online' ? 'text-success' : 'text-error'}`}>
                        {server.statusMessage}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Components Section */}
        <section className="mt-12">
          <h2 className="text-xl font-semibold text-base-content mb-4">System Components</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {components.map((agent, index) => (
              <div key={index} className="card bg-base-100 shadow-md border border-base-300/50">
                <div className="card-body">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <agent.icon className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="card-title text-base-content">{agent.name}</h3>
                      <div className="flex items-center gap-2">
                        <span className="badge badge-success badge-sm">{agent.status}</span>
                        <span className="text-xs text-base-content/60">v{agent.version}</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-base-content/70 mt-4">{agent.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

      </main>
    </div>
  );
}