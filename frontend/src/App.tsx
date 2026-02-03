import { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { AuthorizationList } from './components/AuthorizationList';
import { AuthorizationDetail } from './components/AuthorizationDetail';
import { NewAuthorizationForm } from './components/NewAuthorizationForm';
import { Header } from './components/Header';
import { useHealth } from './hooks/useApi';
import type { Authorization } from './types';

type View = 'dashboard' | 'list' | 'detail' | 'new';

function App() {
  const [view, setView] = useState<View>('dashboard');
  const [selectedAuth, setSelectedAuth] = useState<Authorization | null>(null);
  const { data: health, fetch: fetchHealth } = useHealth();

  useEffect(() => {
    fetchHealth();
    // Refresh health every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const handleSelectAuthorization = (auth: Authorization) => {
    setSelectedAuth(auth);
    setView('detail');
  };

  const handleBack = () => {
    setSelectedAuth(null);
    setView('list');
  };

  const handleNewSubmitted = (auth: Authorization) => {
    setSelectedAuth(auth);
    setView('detail');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        currentView={view}
        onNavigate={setView}
        isHealthy={health?.status === 'healthy'}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {view === 'dashboard' && (
          <Dashboard
            onViewAll={() => setView('list')}
            onNewRequest={() => setView('new')}
          />
        )}
        
        {view === 'list' && (
          <AuthorizationList
            onSelect={handleSelectAuthorization}
            onNew={() => setView('new')}
          />
        )}
        
        {view === 'detail' && selectedAuth && (
          <AuthorizationDetail
            authorization={selectedAuth}
            onBack={handleBack}
          />
        )}
        
        {view === 'new' && (
          <NewAuthorizationForm
            onSubmitted={handleNewSubmitted}
            onCancel={() => setView('dashboard')}
          />
        )}
      </main>
      
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            PACCA - Prior Authorization & Care Coordination Agent Platform
            {health && (
              <span className="ml-2">
                | v{health.version} | {health.environment}
              </span>
            )}
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
