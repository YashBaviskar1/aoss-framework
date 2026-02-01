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
    CheckCircle,
    AlertTriangle,
    Loader2
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

// --- Helper component for Sidebar Links (reused) ---
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

export default function MonitoringSetup() {
    const { user, isLoaded } = useUser();
    const [servers, setServers] = useState([]);
    const [selectedServerId, setSelectedServerId] = useState('');

    // Form State
    const [awsAccessKey, setAwsAccessKey] = useState('');
    const [awsSecretKey, setAwsSecretKey] = useState('');
    const [awsRegion, setAwsRegion] = useState('ap-south-1');
    const [instanceId, setInstanceId] = useState('');

    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null); // { type: 'success'|'error', message: '' }

    useEffect(() => {
        if (isLoaded && user) {
            fetch(`http://localhost:8000/api/dashboard/${user.id}`)
                .then(res => res.json())
                .then(data => {
                    setServers(data.servers);
                    if (data.servers.length > 0) setSelectedServerId(data.servers[0].id);
                });
        }
    }, [isLoaded, user]);

    const handleEnableMonitoring = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus(null);

        try {
            const res = await fetch(`http://localhost:8000/api/monitoring/enable/${selectedServerId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    aws_access_key: awsAccessKey,
                    aws_secret_key: awsSecretKey,
                    aws_region: awsRegion,
                    instance_id: instanceId
                })
            });

            const data = await res.json();

            if (res.ok) {
                setStatus({ type: 'success', message: data.message });
            } else {
                setStatus({ type: 'error', message: data.detail || 'Setup failed' });
            }
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setLoading(false);
        }
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
            <main className="flex-1 flex flex-col p-8 pt-24 overflow-y-auto">
                <div className="max-w-4xl mx-auto w-full">
                    <header className="mb-8">
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <Activity className="w-8 h-8 text-primary" />
                            Monitoring Setup
                        </h1>
                        <p className="text-base-content/60 mt-2">
                            Deploy Node Exporter and configure Prometheus with one click.
                        </p>
                    </header>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Config Form */}
                        <div className="card bg-base-100 shadow-xl border border-base-300">
                            <div className="card-body">
                                <h2 className="card-title text-base-content">
                                    <Server className="w-5 h-5" /> Target Configuration
                                </h2>

                                <form onSubmit={handleEnableMonitoring} className="space-y-4 mt-4">
                                    <div className="form-control">
                                        <label className="label"><span className="label-text">Select Server</span></label>
                                        <select
                                            className="select select-bordered w-full"
                                            value={selectedServerId}
                                            onChange={(e) => setSelectedServerId(e.target.value)}
                                        >
                                            {servers.map(s => (
                                                <option key={s.id} value={s.id}>{s.server_tag} ({s.ip_address})</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="divider text-xs opacity-50">AWS Credentials (Ephemeral)</div>

                                    <div className="form-control">
                                        <label className="label"><span className="label-text">AWS Access Key ID</span></label>
                                        <input
                                            type="text"
                                            placeholder="AKIA..."
                                            className="input input-bordered font-mono"
                                            value={awsAccessKey}
                                            onChange={(e) => setAwsAccessKey(e.target.value)}
                                            required
                                        />
                                    </div>

                                    <div className="form-control">
                                        <label className="label"><span className="label-text">AWS Secret Access Key</span></label>
                                        <input
                                            type="password"
                                            placeholder="Secret Key"
                                            className="input input-bordered font-mono"
                                            value={awsSecretKey}
                                            onChange={(e) => setAwsSecretKey(e.target.value)}
                                            required
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">Region</span></label>
                                            <input
                                                type="text"
                                                placeholder="ap-south-1"
                                                className="input input-bordered"
                                                value={awsRegion}
                                                onChange={(e) => setAwsRegion(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <div className="form-control">
                                            <label className="label"><span className="label-text">Instance ID</span></label>
                                            <input
                                                type="text"
                                                placeholder="i-0xxxxxxxx"
                                                className="input input-bordered font-mono"
                                                value={instanceId}
                                                onChange={(e) => setInstanceId(e.target.value)}
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="card-actions justify-end mt-6">
                                        <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                                            {loading ? <Loader2 className="animate-spin" /> : 'Enable Monitoring'}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        {/* Status / Instructions */}
                        <div className="space-y-6">
                            {status && (
                                <div className={`alert ${status.type === 'success' ? 'alert-success' : 'alert-error'} shadow-lg`}>
                                    {status.type === 'success' ? <CheckCircle /> : <AlertTriangle />}
                                    <div>
                                        <h3 className="font-bold">{status.type === 'success' ? 'Success!' : 'Error'}</h3>
                                        <div className="text-xs">{status.message}</div>
                                    </div>
                                </div>
                            )}

                            <div className="card bg-base-100 shadow border border-base-300">
                                <div className="card-body">
                                    <h3 className="card-title text-sm opacity-70">How it works</h3>
                                    <ul className="steps steps-vertical text-sm">
                                        <li className="step step-primary">Connect to AWS via Boto3</li>
                                        <li className="step step-primary">Open Security Group Port 9100</li>
                                        <li className="step step-primary">SSH into Server</li>
                                        <li className="step step-primary">Install Node Exporter Service</li>
                                        <li className="step step-primary">Register with Prometheus</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
