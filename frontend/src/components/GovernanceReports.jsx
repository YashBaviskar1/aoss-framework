import { useState, useEffect } from 'react';
import { useUser } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';

/**
 * Governance Reports View (Objective 1)
 * 
 * Displays a list of governance reports for the current user.
 * Each report shows summary statistics and can be clicked to view details.
 * 
 * This component is READ-ONLY and does not trigger report generation.
 */
export default function GovernanceReports() {
  const { user } = useUser();
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeReport, setActiveReport] = useState(null);

  useEffect(() => {
    if (user) {
      fetchReports();
      fetchActiveReport();
    }
  }, [user]);

  const fetchReports = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/reports/user/${user.id}?limit=20`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }
      
      const data = await response.json();
      setReports(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchActiveReport = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/reports/user/${user.id}/active`
      );
      
      if (!response.ok) return;
      
      const data = await response.json();
      if (data.report) {
        setActiveReport(data.report);
      }
    } catch (err) {
      console.error('Failed to fetch active report:', err);
    }
  };

  const viewReport = (reportId) => {
    navigate(`/reports/${reportId}`);
  };

  const getHealthBadgeClass = (stats) => {
    const successRate = stats?.success_rate || 0;
    if (successRate >= 90) return 'badge-success';
    if (successRate >= 70) return 'badge-warning';
    return 'badge-error';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="alert alert-error max-w-md">
          <span>Error loading reports: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Governance Reports</h1>
        <p className="text-base-content/70">
          Automated activity reports generated from your system operations
        </p>
      </div>

      {/* Active Report Summary Card */}
      {activeReport && (
        <div className="card bg-primary text-primary-content mb-8">
          <div className="card-body">
            <h2 className="card-title">Active Report</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div className="stat">
                <div className="stat-title text-primary-content/70">
                  Total Activities
                </div>
                <div className="stat-value text-2xl">
                  {activeReport.summary_stats?.total_executions || 0}
                </div>
              </div>
              <div className="stat">
                <div className="stat-title text-primary-content/70">
                  Success Rate
                </div>
                <div className="stat-value text-2xl">
                  {activeReport.summary_stats?.success_rate || 0}%
                </div>
              </div>
              <div className="stat">
                <div className="stat-title text-primary-content/70">
                  Significant Events
                </div>
                <div className="stat-value text-2xl">
                  {activeReport.summary_stats?.significant_events || 0}
                </div>
              </div>
              <div className="stat">
                <div className="stat-title text-primary-content/70">
                  Health Status
                </div>
                <div className="stat-value text-2xl">
                  <div className={`badge badge-lg ${
                    activeReport.executive_summary?.report_health === 'healthy' 
                      ? 'badge-success' 
                      : activeReport.executive_summary?.report_health === 'warning'
                      ? 'badge-warning'
                      : 'badge-error'
                  }`}>
                    {activeReport.executive_summary?.report_health || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
            <div className="card-actions justify-end mt-4">
              <button 
                className="btn btn-secondary"
                onClick={() => viewReport(activeReport.id)}
              >
                View Full Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reports List */}
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-2xl font-bold">Report History</h2>
        <div className="badge badge-neutral">
          {reports.length} {reports.length === 1 ? 'Report' : 'Reports'}
        </div>
      </div>

      {reports.length === 0 ? (
        <div className="card bg-base-200">
          <div className="card-body items-center text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-16 w-16 text-base-content/30 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-xl font-semibold mb-2">No Reports Yet</h3>
            <p className="text-base-content/70">
              Reports are automatically generated as you use the system.
              Execute some commands to see your first report!
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="card bg-base-200 hover:bg-base-300 transition-colors cursor-pointer"
              onClick={() => viewReport(report.id)}
            >
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="card-title">
                        Report from {new Date(report.created_at).toLocaleDateString()}
                      </h3>
                      <div className={`badge ${report.status === 'active' ? 'badge-primary' : 'badge-ghost'}`}>
                        {report.status}
                      </div>
                    </div>
                    <p className="text-sm text-base-content/70">
                      Last updated: {new Date(report.last_updated_at).toLocaleString()}
                    </p>
                  </div>
                  <div className={`badge badge-lg ${getHealthBadgeClass(report)}`}>
                    {report.success_rate}% Success
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div>
                    <div className="text-sm text-base-content/70">Total Activities</div>
                    <div className="text-2xl font-bold">{report.total_executions}</div>
                  </div>
                  <div>
                    <div className="text-sm text-base-content/70">Significant Events</div>
                    <div className="text-2xl font-bold">{report.significant_events}</div>
                  </div>
                  <div>
                    <div className="text-sm text-base-content/70">Period</div>
                    <div className="text-sm">
                      {report.period_start && new Date(report.period_start).toLocaleDateString()}
                      {report.period_end && ` - ${new Date(report.period_end).toLocaleDateString()}`}
                    </div>
                  </div>
                </div>

                <div className="card-actions justify-end mt-4">
                  <button className="btn btn-sm btn-primary">
                    View Details →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
