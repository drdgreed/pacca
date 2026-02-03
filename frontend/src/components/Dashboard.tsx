import { useEffect } from 'react';
import {
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  Users,
  Zap,
  FileText,
} from 'lucide-react';
import { useMetrics, useAuthorizations } from '../hooks/useApi';

interface DashboardProps {
  onViewAll: () => void;
  onNewRequest: () => void;
}

export function Dashboard({ onViewAll, onNewRequest }: DashboardProps) {
  const { data: metrics, fetch: fetchMetrics } = useMetrics();
  const { data: authList, fetch: fetchAuths } = useAuthorizations();

  useEffect(() => {
    fetchMetrics();
    fetchAuths(1);
  }, [fetchMetrics, fetchAuths]);

  const recentAuths = authList?.items.slice(0, 5) || [];

  const stats = [
    {
      name: 'Total Processed',
      value: metrics?.authorizations_processed || 0,
      icon: FileText,
      color: 'bg-primary-500',
    },
    {
      name: 'Autonomous Decisions',
      value: metrics?.autonomous_decisions || 0,
      icon: Zap,
      color: 'bg-success-500',
    },
    {
      name: 'Escalated to Review',
      value: metrics?.escalated_decisions || 0,
      icon: Users,
      color: 'bg-warning-500',
    },
    {
      name: 'Avg Processing Time',
      value: `${((metrics?.average_processing_time_ms || 0) / 1000).toFixed(1)}s`,
      icon: Clock,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-500 mt-1">
            Overview of prior authorization processing
          </p>
        </div>
        <button
          onClick={onNewRequest}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Activity className="w-4 h-4 mr-2" />
          Submit New Request
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-xl shadow-sm border p-6 card-hover"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Authorizations */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">
                Recent Authorizations
              </h3>
              <button
                onClick={onViewAll}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                View all →
              </button>
            </div>
          </div>
          <div className="divide-y">
            {recentAuths.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No authorizations yet
              </div>
            ) : (
              recentAuths.map((auth) => (
                <div
                  key={auth.request_id}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900">
                        {auth.treatment_description}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {auth.diagnosis_code} • {auth.diagnosis_description}
                      </p>
                    </div>
                    <StatusBadge status={auth.status} decision={auth.decision} />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* System Performance */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              System Performance
            </h3>
          </div>
          <div className="p-6 space-y-6">
            {/* Automation Rate */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Automation Rate</span>
                <span className="font-medium text-gray-900">
                  {metrics?.authorizations_processed
                    ? Math.round(
                        (metrics.autonomous_decisions /
                          metrics.authorizations_processed) *
                          100
                      )
                    : 0}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-success-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${
                      metrics?.authorizations_processed
                        ? (metrics.autonomous_decisions /
                            metrics.authorizations_processed) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            {/* Uptime */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">System Uptime</span>
                <span className="font-medium text-gray-900">
                  {formatUptime(metrics?.uptime_seconds || 0)}
                </span>
              </div>
            </div>

            {/* Processing Stats */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-600">
                  {metrics?.requests_total || 0}
                </p>
                <p className="text-sm text-gray-500">Total Requests</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-success-600">
                  {((metrics?.average_processing_time_ms || 0) / 1000).toFixed(1)}s
                </p>
                <p className="text-sm text-gray-500">Avg Response</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold">
              AI-Powered Prior Authorization
            </h3>
            <p className="text-primary-100 mt-1">
              Submit authorization requests and receive intelligent,
              guideline-based recommendations
            </p>
          </div>
          <button
            onClick={onNewRequest}
            className="flex items-center px-6 py-3 bg-white text-primary-600 rounded-lg font-medium hover:bg-primary-50 transition-colors"
          >
            Get Started
            <TrendingUp className="w-4 h-4 ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({
  status,
  decision,
}: {
  status: string;
  decision: string | null;
}) {
  if (decision === 'approve' || status === 'approved') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-50 text-success-600">
        <CheckCircle className="w-3 h-3 mr-1" />
        Approved
      </span>
    );
  }

  if (decision === 'deny' || status === 'denied') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-danger-50 text-danger-600">
        <AlertTriangle className="w-3 h-3 mr-1" />
        Denied
      </span>
    );
  }

  if (status === 'pending_review' || status === 'escalated') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-warning-50 text-warning-600">
        <Clock className="w-3 h-3 mr-1" />
        Pending Review
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-600 status-processing">
      <Activity className="w-3 h-3 mr-1" />
      Processing
    </span>
  );
}

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }

  return `${hours}h ${minutes}m`;
}
