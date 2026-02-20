import React, { useState, useEffect } from 'react';
import { ProviderDashboard } from './components/ProviderDashboard';
// We will build these two components next!
import { LoginScreen } from './components/LoginScreen'; 
import { DirectorQueue } from './components/DirectorQueue'; 
import { AdminDashboard } from './components/AdminDashboard';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState<'provider' | 'director' | 'admin'>('provider');

  // Check if we already have a token when the app loads
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  // If not logged in, only show the login screen
  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  // If logged in, show the full app with Navigation
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Bar */}
      <nav className="bg-indigo-700 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-bold tracking-tight">PACCA</h1>
            <div className="space-x-1">
              <button 
                onClick={() => setCurrentView('provider')}
                className={`px-4 py-2 rounded-md transition-colors ${currentView === 'provider' ? 'bg-indigo-800 font-semibold' : 'hover:bg-indigo-600'}`}
              >
                Submit Case
              </button>
              <button 
                onClick={() => setCurrentView('director')}
                className={`px-4 py-2 rounded-md transition-colors ${currentView === 'director' ? 'bg-indigo-800 font-semibold' : 'hover:bg-indigo-600'}`}
              >
                Director Queue
              </button>
            </div>
          </div>
          
<button 
  onClick={() => setCurrentView('admin')}
  className={`px-4 py-2 rounded-md transition-colors ${currentView === 'admin' ? 'bg-indigo-800 font-semibold' : 'hover:bg-indigo-600'}`}
>
  Admin Panel
</button>

          <button 
            onClick={handleLogout}
            className="text-sm bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded border border-indigo-500 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </nav>

<main className="py-8">
  {currentView === 'provider' && <ProviderDashboard />}
  {currentView === 'director' && <DirectorQueue />}
  {currentView === 'admin' && <AdminDashboard />}
</main>

      {/* Main Content Area */}
      <main className="py-8">
        {currentView === 'provider' ? <ProviderDashboard /> : <DirectorQueue />}
      </main>
    </div>
  );
}

export default App;