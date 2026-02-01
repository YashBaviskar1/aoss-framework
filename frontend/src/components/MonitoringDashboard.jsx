import { useState, useEffect } from 'react';
import { useUser } from '@clerk/clerk-react';
import {
    LayoutDashboard,
    Server,
    ShieldCheck,
    BarChart3,
    Bot,
    Cpu,
    Activity,
    Plus,
    ExternalLink,
    LineChart
} from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

// --- Reused Helper ---
function NavLink({ to, icon: Icon, children }) {
    const location = useLocation();
    const isActive = location.pathname === to;
    return (
        <li>
            <Link to={to} className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors duration-200 ${isActive ? 'bg-primary/10 text-primary font-semibold' : 'text-base-content/70 hover:bg-base-200 hover:text-primary'}`}>
                <Icon className="w-5 h-5" />
                <span>{children}</span>
            </Link>
        </li>
    );
}

// Hardcoded for now based on user request/example
const GRAFANA_URL = "http://localhost:3001/d/ad7kwf5/aoss-server-monitoring?orgId=1&refresh=5s&kiosk";

export default function MonitoringDashboard() {
    const { user, isLoaded } = useUser();
    const navigate = useNavigate();
    const [servers, setServers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState('list'); // 'list' | 'dashboard'
    const [selectedServer, setSelectedServer] = useState(null);

    useEffect(() => {
        if (isLoaded && user) {
            fetch(`http://localhost:8000/api/monitoring/status`)
                .then(res => res.json())
                .then(data => {
                    setServers(data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Failed to fetch status", err);
                    setLoading(false);
                });
        }
    }, [isLoaded, user]);

    const handleEnableClick = (serverId) => {
        // We navigate to the setup page with pre-selected server
        // Since setup page uses internal state for selection, we might need to pass state
        // or just let user select. For now, simple redirect.
        navigate("/monitoring/enable");
    };

    const handleViewDashboard = (server) => {
        setSelectedServer(server);
        setViewMode('dashboard');
    };

    return (
        <div className="flex min-h-screen bg-base-200">
            {/* Sidebar */}
            <aside className="w-64 bg-base-100 text-base-content flex flex-col border-r border-base-300/50 pt-24 hidden md:flex">
                <div className="flex items-center space-x-3 px-6 py-5 border-b border-base-300/50">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <Cpu className="w-6 h-6 text-primary" />
                    </div>
                    <span className="text-xl font-bold">AOSS</span>
                </div>
                <nav className="flex-1 px-4 py-4">
                    <ul className="space-y-2">
                        <NavLink to="/dashboard" icon={LayoutDashboard}>Dashboard</NavLink>
                        <NavLink to="/services" icon={Server}>Services</NavLink>
                        <NavLink to="/compliance" icon={ShieldCheck}>Compliance</NavLink>
                        <NavLink to="/monitoring" icon={BarChart3}>Monitoring</NavLink>
                        <NavLink to="/chat" icon={Bot}>Orchestrate</NavLink>
                    </ul>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col p-8 pt-24 overflow-hidden h-screen">
                <header className="mb-6 flex justify-between items-center shrink-0">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <Activity className="w-8 h-8 text-primary" />
                            Monitoring Dashboard
                        </h1>
                        <p className="text-base-content/60 mt-1">
                            Real-time metrics and observability for your infrastructure.
                        </p>
                    </div>
                    {viewMode === 'dashboard' && (
                        <button className="btn btn-ghost" onClick={() => setViewMode('list')}>
                            Back to Server List
                        </button>
                    )}
                </header>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <span className="loading loading-spinner loading-lg text-primary"></span>
                    </div>
                ) : (
                    <>
                        {viewMode === 'list' && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {servers.map(server => (
                                    <div key={server.id} className="card bg-base-100 shadow-xl border border-base-300 hover:shadow-2xl transition-all">
                                        <div className="card-body">
                                            <div className="flex justify-between items-start">
                                                <h2 className="card-title text-lg">{server.server_tag}</h2>
                                                {server.monitoring_enabled ? (
                                                    <div className="badge badge-success gap-2 text-white">
                                                        <Activity className="w-3 h-3" /> Active
                                                    </div>
                                                ) : (
                                                    <div className="badge badge-ghost opacity-70">Not Monitored</div>
                                                )}
                                            </div>
                                            <p className="text-sm font-mono text-base-content/70 mt-2">{server.ip_address}</p>

                                            <div className="card-actions justify-end mt-6">
                                                {server.monitoring_enabled ? (
                                                    <button
                                                        className="btn btn-primary btn-sm gap-2"
                                                        onClick={() => handleViewDashboard(server)}
                                                    >
                                                        <LineChart className="w-4 h-4" /> View Metrics
                                                    </button>
                                                ) : (
                                                    <button
                                                        className="btn btn-outline btn-sm gap-2"
                                                        onClick={() => handleEnableClick(server.id)}
                                                    >
                                                        <Plus className="w-4 h-4" /> Enable
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                <div className="card bg-base-200 border-2 border-dashed border-base-300 flex items-center justify-center p-8 hover:bg-base-200/80 transition-colors cursor-pointer" onClick={() => navigate("/dashboard")}>
                                    <div className="text-center text-base-content/50">
                                        <Server className="w-8 h-8 mx-auto mb-2" />
                                        <p>Add New Server</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {viewMode === 'dashboard' && selectedServer && (
                            <div className="flex-1 bg-base-100 rounded-2xl shadow-lg border border-base-300 overflow-hidden flex flex-col relative w-full h-full">
                                <div className="absolute top-4 right-4 z-10 flex gap-2">
                                    <a href={GRAFANA_URL} target="_blank" rel="noreferrer" className="btn btn-sm btn-circle btn-ghost bg-base-100/80 backdrop-blur" title="Open in Grafana">
                                        <ExternalLink className="w-4 h-4" />
                                    </a>
                                </div>
                                <iframe
                                    src={`${GRAFANA_URL}&var-instance=${selectedServer.ip_address}:9100`}
                                    className="w-full h-full border-0"
                                    title={`Monitoring Dashboard for ${selectedServer.server_tag}`}
                                />
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}
