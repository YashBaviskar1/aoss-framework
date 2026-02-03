import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';
import { Server, Activity, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

/**
 * Report Detail View with Server Selection (Enhanced)
 * 
 * Displays governance reports with:
 * - Server selector dropdown
 * - Server-specific execution timeline
 * - Health status with explanation
 * - Summary statistics per server
 */
export default function ReportDetail() {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const { user } = useUser();
  const [report, setReport] = useState(null);
  const [allServers, setAllServers] = useState([]);
  const [reportServers, setReportServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverReport, setServerReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, significant, failed

  useEffect(() => {
    const fetchData = async () => {
      if (!reportId || !user) return;

      try {
        // Fetch report
        const reportResponse = await fetch(
          `http://localhost:8000/api/reports/${reportId}`
        );
        if (reportResponse.ok) {
          const reportData = await reportResponse.json();
          setReport(reportData);
        }

        // Fetch all user servers
        const serversResponse = await fetch(
          `http://localhost:8000/api/dashboard/${user.id}`
        );
        if (serversResponse.ok) {
          const serversData = await serversResponse.json();
          setAllServers(serversData.servers || []);
        }

        // Fetch report servers
        const reportServersResponse = await fetch(
          `http://localhost:8000/api/reports/${reportId}/servers`
        );
        if (reportServersResponse.ok) {
          const reportServersData = await reportServersResponse.json();
          setReportServers(reportServersData);
        }

        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [reportId, user]);

  useEffect(() => {
    const fetchServerData = async () => {
      if (!selectedServer) {
        setServerReport(null);
        return;
      }

      try {
        const response = await fetch(
          `http://localhost:8000/api/reports/${reportId}/servers/${selectedServer}`
        );
        
        if (response.ok) {
          const data = await response.json();
          setServerReport(data);
        } else {
          setServerReport(null);
        }
      } catch (err) {
        console.error('Failed to fetch server report:', err);
        setServerReport(null);
      }
    };

    fetchServerData();
  }, [selectedServer, reportId]);

  const getServerStats = (serverId) => {
    const serverData = reportServers.find(s => s.server_id === serverId);
    return serverData || null;
  };

  const getFilteredExecutions = () => {
    if (!report?.executions) return [];
    
    switch (filter) {
      case 'significant':
        return report.executions.filter(e => e.is_significant);
      case 'failed':
        return report.executions.filter(e => e.status === 'Failed');
      default:
        return report.executions;
    }
  };

  const getStatusBadgeClass = (status) => {
    const statusLower = status?.toLowerCase() || '';
    if (statusLower === 'executed' || statusLower === 'success') {
      return 'badge-success';
    } else if (statusLower === 'failed') {
      return 'badge-error';
    } else if (statusLower === 'blocked') {
      return 'badge-warning';
    }
    return 'badge-ghost';
  };

  const getHealthBadgeClass = (health) => {
    switch (health) {
      case 'HEALTHY':
        return 'badge-success';
      case 'WARNING':
        return 'badge-warning';
      case 'CRITICAL':
        return 'badge-error';
      default:
        return 'badge-ghost';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'HEALTHY':
        return <CheckCircle className="w-5 h-5" />;
      case 'WARNING':
        return <AlertTriangle className="w-5 h-5" />;
      case 'CRITICAL':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="alert alert-error max-w-md">
          <span>Error loading report: {error || 'Report not found'}</span>
          <button className="btn btn-sm" onClick={() => navigate('/reports')}>
            Back to Reports
          </button>
        </div>
      </div>
    );
  }

  const filteredExecutions = getFilteredExecutions();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          className="btn btn-ghost btn-sm mb-4"
          onClick={() => navigate('/reports')}
        >
          ← Back to Reports
        </button>
        <h1 className="text-4xl font-bold mb-2">
          Governance Report
        </h1>
        <div className="flex gap-2 items-center">
          <p className="text-base-content/70">
            Created: {new Date(report.created_at).toLocaleString()}
          </p>
          <div className={`badge ${report.status === 'active' ? 'badge-primary' : 'badge-ghost'}`}>
            {report.status}
          </div>
        </div>
      </div>

      {/* Server Selector Section */}
      <div className="card bg-base-200 mb-8">
        <div className="card-body">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Server className="w-6 h-6" />
              <h2 className="card-title">Select a Server to View Report</h2>
            </div>
            {selectedServer && (
              <button 
                className="btn btn-sm btn-ghost"
                onClick={() => setSelectedServer(null)}
              >
                Clear Selection
              </button>
            )}
          </div>
          
          {allServers.length === 0 ? (
            <p className="text-base-content/70">No servers found</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {allServers.map((server) => {
                const stats = getServerStats(server.id);
                const hasActivity = stats !== null;
                
                return (
                  <div
                    key={server.id}
                    className={`card bg-base-100 cursor-pointer hover:shadow-lg transition-all ${
                      selectedServer === server.id ? 'ring-2 ring-primary' : ''
                    } ${!hasActivity ? 'opacity-60' : ''}`}
                    onClick={() => setSelectedServer(server.id)}
                  >
                    <div className="card-body p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">{server.server_tag}</h3>
                          <p className="text-xs text-base-content/60">{server.ip_address}</p>
                        </div>
                        {!hasActivity && (
                          <div className="badge badge-sm badge-ghost">
                            No Activity
                          </div>
                        )}
                      </div>
                      
                      {hasActivity ? (
                        <div className="text-sm space-y-1">
                          <p className="text-base-content/70">
                            Commands: {stats.execution_count}
                          </p>
                          <p className="text-base-content/70">
                            Success Rate: {stats.success_rate}%
                          </p>
                          <div className="flex gap-2 mt-2">
                            <span className="badge badge-success badge-sm">
                              {stats.success_count} OK
                            </span>
                            {stats.failure_count > 0 && (
                              <span className="badge badge-error badge-sm">
                                {stats.failure_count} Failed
                              </span>
                            )}
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-base-content/50">
                          No commands executed in this report period
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Server-Specific Report (Only shown when server is selected) */}
      {selectedServer && serverReport && (
        <div className="space-y-6">
          {/* Server Summary Card */}
          <div className="card bg-gradient-to-br from-primary to-secondary text-primary-content">
            <div className="card-body">
              <div className="flex items-center gap-3 mb-4">
                <Server className="w-8 h-8" />
                <div>
                  <h2 className="text-2xl font-bold">{serverReport.server.server_tag}</h2>
                  <p className="text-primary-content/70">
                    {serverReport.server.ip_address} • {serverReport.server.hostname || 'N/A'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="stat bg-base-100/10 rounded-lg p-4">
                  <div className="stat-title text-primary-content/70">Total Commands</div>
                  <div className="stat-value text-3xl">
                    {serverReport.summary.total_commands}
                  </div>
                </div>
                <div className="stat bg-base-100/10 rounded-lg p-4">
                  <div className="stat-title text-primary-content/70">Success Rate</div>
                  <div className="stat-value text-3xl">
                    {serverReport.summary.success_rate}%
                  </div>
                </div>
                <div className="stat bg-base-100/10 rounded-lg p-4">
                  <div className="stat-title text-primary-content/70">Successful</div>
                  <div className="stat-value text-3xl text-success">
                    {serverReport.summary.success_count}
                  </div>
                </div>
                <div className="stat bg-base-100/10 rounded-lg p-4">
                  <div className="stat-title text-primary-content/70">Failed</div>
                  <div className="stat-value text-3xl text-error">
                    {serverReport.summary.failure_count}
                  </div>
                </div>
              </div>

              {/* Health Status Explanation */}
              <div className="mt-6 p-4 bg-base-100/20 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  {getHealthIcon(serverReport.summary.health_status)}
                  <h3 className="font-semibold text-lg">
                    Health Status: {serverReport.summary.health_status}
                  </h3>
                </div>
                <p className="text-primary-content/90">
                  {serverReport.summary.health_explanation}
                </p>
              </div>
            </div>
          </div>

          {/* Execution Timeline */}
          <div className="card bg-base-200">
            <div className="card-body">
              <h2 className="card-title mb-4">Command History</h2>

              {serverReport.timeline.length === 0 ? (
                <div className="text-center py-8 text-base-content/70">
                  No commands executed on this server yet
                </div>
              ) : (
                <div className="space-y-4">
                  {serverReport.timeline.map((execution, index) => (
                    <div key={execution.execution_log_id || index} className="card bg-base-100">
                      <div className="card-body p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <div className={`badge ${getStatusBadgeClass(execution.status)}`}>
                              {execution.status}
                            </div>
                            <span className="text-sm text-base-content/70">
                              {new Date(execution.timestamp).toLocaleString()}
                            </span>
                          </div>
                        </div>
                        
                        <div className="font-mono text-sm bg-base-200 p-3 rounded mb-2">
                          $ {execution.command}
                        </div>

                        {execution.summary && (
                          <p className="text-sm text-base-content/70 mb-2">
                            {execution.summary}
                          </p>
                        )}

                        {/* Execution Details */}
                        {execution.execution_details && execution.execution_details.length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-sm font-semibold">
                              View Execution Output ({execution.execution_details.length} steps)
                            </summary>
                            <div className="mt-2 space-y-2 max-h-96 overflow-y-auto">
                              {execution.execution_details.map((detail, i) => (
                                <div key={i} className="p-3 bg-base-200 rounded">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-semibold">Step {detail.step || i+1}</span>
                                    <div className={`badge badge-xs ${
                                      detail.exit_code === 0 ? 'badge-success' : 'badge-error'
                                    }`}>
                                      Exit: {detail.exit_code}
                                    </div>
                                  </div>
                                  <div className="font-mono text-xs mb-1">
                                    {detail.command}
                                  </div>
                                  {detail.stdout && (
                                    <div className="text-xs text-success bg-base-300 p-2 rounded mt-1">
                                      {detail.stdout}
                                    </div>
                                  )}
                                  {detail.stderr && (
                                    <div className="text-xs text-error bg-base-300 p-2 rounded mt-1">
                                      {detail.stderr}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Message when server selected but no report data */}
      {selectedServer && !serverReport && (
        <div className="card bg-base-200">
          <div className="card-body text-center py-12">
            <Activity className="w-16 h-16 mx-auto mb-4 text-base-content/30" />
            <h3 className="text-xl font-semibold mb-2">No Activity Found</h3>
            <p className="text-base-content/70">
              This server has no recorded activity in this report period.
            </p>
          </div>
        </div>
      )}

      {/* Prompt when no server is selected */}
      {!selectedServer && (
        <div className="alert alert-info">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>Select a server above to view its detailed report and command history</span>
        </div>
      )}
    </div>
  );
}
