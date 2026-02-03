import { Activity, FileText, Home, Plus } from 'lucide-react';

interface HeaderProps {
  currentView: string;
  onNavigate: (view: 'dashboard' | 'list' | 'new') => void;
  isHealthy: boolean;
}

export function Header({ currentView, onNavigate, isHealthy }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-600">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">PACCA</h1>
              <p className="text-xs text-gray-500">Prior Authorization Platform</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-1">
            <button
              onClick={() => onNavigate('dashboard')}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentView === 'dashboard'
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </button>
            
            <button
              onClick={() => onNavigate('list')}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentView === 'list' || currentView === 'detail'
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <FileText className="w-4 h-4 mr-2" />
              Authorizations
            </button>
            
            <button
              onClick={() => onNavigate('new')}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors ml-2"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Request
            </button>
          </nav>

          {/* Health Indicator */}
          <div className="flex items-center">
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                isHealthy
                  ? 'bg-success-50 text-success-600'
                  : 'bg-danger-50 text-danger-600'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full mr-1.5 ${
                  isHealthy ? 'bg-success-500' : 'bg-danger-500'
                }`}
              />
              {isHealthy ? 'System Online' : 'System Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
