import { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  ChevronRight,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Activity,
  Plus,
} from 'lucide-react';
import { useAuthorizations } from '../hooks/useApi';
import type { Authorization } from '../types';

interface AuthorizationListProps {
  onSelect: (auth: Authorization) => void;
  onNew: () => void;
}

export function AuthorizationList({ onSelect, onNew }: AuthorizationListProps) {
  const { data, loading, error, fetch } = useAuthorizations();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch(1, statusFilter || undefined);
  }, [fetch, statusFilter]);

  const filteredItems = data?.items.filter((auth) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      auth.request_id.toLowerCase().includes(search) ||
      auth.diagnosis_description.toLowerCase().includes(search) ||
      auth.treatment_description.toLowerCase().includes(search) ||
      auth.diagnosis_code.toLowerCase().includes(search)
    );
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Authorizations</h2>
          <p className="text-gray-500 mt-1">
            {data?.total || 0} total authorization requests
          </p>
        </div>
        <button
          onClick={onNew}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Request
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by ID, diagnosis, or treatment..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Statuses</option>
              <option value="approved">Approved</option>
              <option value="denied">Denied</option>
              <option value="pending_review">Pending Review</option>
              <option value="submitted">Processing</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-600 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <Activity className="w-8 h-8 text-primary-600 mx-auto animate-spin" />
          <p className="text-gray-500 mt-2">Loading authorizations...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredItems.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <FileIcon className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="text-lg font-medium text-gray-900 mt-4">
            No authorizations found
          </h3>
          <p className="text-gray-500 mt-1">
            {searchTerm || statusFilter
              ? 'Try adjusting your filters'
              : 'Submit your first authorization request'}
          </p>
          {!searchTerm && !statusFilter && (
            <button
              onClick={onNew}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Create Request
            </button>
          )}
        </div>
      )}

      {/* List */}
      {!loading && filteredItems.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border divide-y">
          {filteredItems.map((auth) => (
            <AuthorizationRow
              key={auth.request_id}
              authorization={auth}
              onClick={() => onSelect(auth)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex justify-center gap-2">
          <button
            disabled={data.page === 1}
            onClick={() => fetch(data.page - 1, statusFilter || undefined)}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-gray-600">
            Page {data.page} of {Math.ceil(data.total / data.page_size)}
          </span>
          <button
            disabled={data.page * data.page_size >= data.total}
            onClick={() => fetch(data.page + 1, statusFilter || undefined)}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function AuthorizationRow({
  authorization,
  onClick,
}: {
  authorization: Authorization;
  onClick: () => void;
}) {
  const statusConfig = getStatusConfig(authorization.status, authorization.decision);

  return (
    <div
      onClick={onClick}
      className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-mono text-gray-500">
              {authorization.request_id}
            </span>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.className}`}
            >
              <statusConfig.icon className="w-3 h-3 mr-1" />
              {statusConfig.label}
            </span>
            {authorization.requires_human_review && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700">
                Needs Review
              </span>
            )}
          </div>

          <h3 className="mt-2 text-base font-medium text-gray-900 truncate">
            {authorization.treatment_description}
          </h3>

          <div className="mt-1 flex items-center gap-4 text-sm text-gray-500">
            <span>
              {authorization.diagnosis_code} — {authorization.diagnosis_description}
            </span>
            <span>•</span>
            <span>Patient Age: {authorization.patient_age}</span>
            {authorization.complexity && (
              <>
                <span>•</span>
                <span>Complexity: {authorization.complexity}/5</span>
              </>
            )}
          </div>

          {authorization.confidence_score !== null && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-gray-500">Confidence:</span>
              <div className="flex-1 max-w-32 bg-gray-200 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full ${getConfidenceColor(
                    authorization.confidence_score
                  )}`}
                  style={{ width: `${authorization.confidence_score * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium text-gray-700">
                {(authorization.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4" />
      </div>
    </div>
  );
}

function getStatusConfig(status: string, decision: string | null) {
  if (decision === 'approve' || status === 'approved') {
    return {
      icon: CheckCircle,
      label: 'Approved',
      className: 'bg-success-50 text-success-600',
    };
  }

  if (decision === 'deny' || status === 'denied') {
    return {
      icon: XCircle,
      label: 'Denied',
      className: 'bg-danger-50 text-danger-600',
    };
  }

  if (status === 'approved_with_conditions') {
    return {
      icon: CheckCircle,
      label: 'Approved w/ Conditions',
      className: 'bg-warning-50 text-warning-600',
    };
  }

  if (status === 'pending_review' || status === 'escalated' || status === 'in_review') {
    return {
      icon: Clock,
      label: 'Pending Review',
      className: 'bg-warning-50 text-warning-600',
    };
  }

  if (status === 'failed') {
    return {
      icon: AlertTriangle,
      label: 'Failed',
      className: 'bg-danger-50 text-danger-600',
    };
  }

  return {
    icon: Activity,
    label: 'Processing',
    className: 'bg-blue-50 text-blue-600',
  };
}

function getConfidenceColor(score: number): string {
  if (score >= 0.85) return 'bg-success-500';
  if (score >= 0.7) return 'bg-warning-500';
  return 'bg-danger-500';
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}
