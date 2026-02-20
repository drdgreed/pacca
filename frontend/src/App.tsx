import React, { useState } from 'react';
import { AdminDashboard } from './components/AdminDashboard';
import { ProviderDashboard } from './components/ProviderDashboard';
import { Login } from './components/Login';

function App() {
  const [view, setView] = useState<'provider' | 'admin'>('provider');
  // Check if token exists on initial load
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('token'));

  // If not logged in, render ONLY the login screen
  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 font-sans">
      <nav className="bg-white shadow-sm border-b border-gray-200 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg shadow-sm"></div>
          <span className="text-xl font-bold text-gray-800 tracking-tight">PACCA <span className="text-indigo-600">Level 5</span></span>
        </div>
        
        <div className="flex bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setView('provider')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              view === 'provider' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Provider View
          </button>
          <button
            onClick={() => setView('admin')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              view === 'admin' ? 'bg-white shadow-sm text-indigo-600' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Dark Factory Admin
          </button>
        </div>

        {/* Quick logout button */}
        <button 
          onClick={handleLogout}
          className="text-sm font-medium text-gray-500 hover:text-red-600 transition-colors"
        >
          Logout
        </button>
      </nav>

      <main className="py-8">
        {view === 'admin' ? <AdminDashboard /> : <ProviderDashboard />}
      </main>
    </div>
  );
}

export default App;
