import { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, Info, X, ExternalLink } from 'lucide-react';

const GRAFANA_DASHBOARD_URL = "http://localhost:3001/d/ad7kwf5/aoss-server-monitoring?orgId=1&refresh=5s";

function getSeverityIcon(severity) {
    switch (severity?.toLowerCase()) {
        case 'critical':
            return <AlertTriangle className="w-5 h-5 text-error" />;
        case 'warning':
            return <AlertCircle className="w-5 h-5 text-warning" />;
        default:
            return <Info className="w-5 h-5 text-info" />;
    }
}

function getSeverityBadgeClass(severity) {
    switch (severity?.toLowerCase()) {
        case 'critical':
            return 'badge-error';
        case 'warning':
            return 'badge-warning';
        default:
            return 'badge-info';
    }
}

export default function AlertsSidebar({ isOpen, onClose }) {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // all, firing, resolved

    useEffect(() => {
        if (isOpen) {
            fetchAlerts();
        }
    }, [isOpen, filter]);

    const fetchAlerts = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filter !== 'all') {
                params.append('status', filter);
            }
            
            const response = await fetch(`http://localhost:8000/api/monitoring/alerts?${params}`);
            const data = await response.json();
            setAlerts(data);
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const openInGrafana = (alert) => {
        let url = GRAFANA_DASHBOARD_URL;
        if (alert.instance) {
            url += `&var-instance=${alert.instance}`;
        }
        window.open(url, '_blank');
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div 
                className="fixed inset-0 bg-black/50 z-40"
                onClick={onClose}
            />
            
            {/* Sidebar */}
            <div className="fixed right-0 top-0 h-full w-96 bg-base-100 shadow-2xl z-50 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-base-300">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="w-6 h-6 text-primary" />
                        <h2 className="text-xl font-bold">Alerts</h2>
                    </div>
                    <button 
                        className="btn btn-sm btn-circle btn-ghost"
                        onClick={onClose}
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Filter Tabs */}
                <div className="flex gap-2 p-4 border-b border-base-300">
                    <button 
                        className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setFilter('all')}
                    >
                        All
                    </button>
                    <button 
                        className={`btn btn-sm ${filter === 'firing' ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setFilter('firing')}
                    >
                        Active
                    </button>
                    <button 
                        className={`btn btn-sm ${filter === 'resolved' ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setFilter('resolved')}
                    >
                        Resolved
                    </button>
                </div>

                {/* Alerts List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {loading ? (
                        <div className="flex justify-center items-center h-32">
                            <span className="loading loading-spinner loading-md"></span>
                        </div>
                    ) : alerts.length === 0 ? (
                        <div className="text-center py-8 text-base-content/50">
                            <Info className="w-12 h-12 mx-auto mb-2 opacity-30" />
                            <p>No alerts found</p>
                        </div>
                    ) : (
                        alerts.map((alert) => (
                            <div 
                                key={alert.id}
                                className={`card bg-base-200 shadow-md hover:shadow-lg transition-all cursor-pointer ${
                                    alert.status === 'resolved' ? 'opacity-60' : ''
                                }`}
                                onClick={() => openInGrafana(alert)}
                            >
                                <div className="card-body p-4">
                                    <div className="flex items-start gap-3 mb-2">
                                        {getSeverityIcon(alert.severity)}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-semibold text-sm truncate">
                                                    {alert.alertname}
                                                </h3>
                                                <div className={`badge badge-xs ${getSeverityBadgeClass(alert.severity)}`}>
                                                    {alert.severity}
                                                </div>
                                            </div>
                                            
                                            {alert.summary && (
                                                <p className="text-xs text-base-content/70 mb-2">
                                                    {alert.summary}
                                                </p>
                                            )}
                                            
                                            {alert.description && (
                                                <p className="text-xs text-base-content/60 mb-2 line-clamp-2">
                                                    {alert.description}
                                                </p>
                                            )}
                                            
                                            <div className="flex flex-wrap gap-2 text-xs text-base-content/50">
                                                {alert.server_tag && (
                                                    <div className="badge badge-sm badge-ghost">
                                                        {alert.server_tag}
                                                    </div>
                                                )}
                                                {alert.instance && (
                                                    <div className="badge badge-sm badge-ghost font-mono">
                                                        {alert.instance}
                                                    </div>
                                                )}
                                            </div>
                                            
                                            <div className="flex items-center justify-between mt-2">
                                                <span className="text-xs text-base-content/40">
                                                    {new Date(alert.starts_at || alert.received_at).toLocaleString()}
                                                </span>
                                                {alert.status === 'resolved' && (
                                                    <span className="badge badge-xs badge-success">Resolved</span>
                                                )}
                                            </div>
                                        </div>
                                        <ExternalLink className="w-4 h-4 text-base-content/30 flex-shrink-0" />
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </>
    );
}
