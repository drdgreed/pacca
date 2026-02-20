import React, { useState } from 'react';

export function AdminDashboard() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

  const handleRegisterUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Assuming your register endpoint might eventually require an Admin JWT
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          username: username,
          password: password,
          email: email,
          full_name: fullName
        })
      });

      if (response.ok) {
        setStatus({ type: 'success', message: `✅ User ${username} successfully provisioned!` });
        // Clear the form
        setUsername('');
        setPassword('');
        setFullName('');
        setEmail('');
      } else {
        const errorData = await response.json();
        setStatus({ type: 'error', message: `❌ Error: ${errorData.detail || 'Failed to create user'}` });
      }
    } catch (error) {
      setStatus({ type: 'error', message: '❌ Connection error. Is the backend running?' });
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      <div className="mb-8 border-b pb-4">
        <h2 className="text-3xl font-bold text-gray-800">System Administration</h2>
        <p className="text-gray-600 mt-2">Provision new provider and reviewer accounts.</p>
      </div>

      <div className="bg-white p-8 rounded-lg shadow-md border-t-4 border-emerald-600 max-w-xl">
        <h3 className="text-xl font-bold mb-6 text-gray-800">Create New User</h3>
        
        {status && (
          <div className={`p-4 mb-6 rounded-md text-sm font-medium ${status.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
            {status.message}
          </div>
        )}

        <form onSubmit={handleRegisterUser} className="space-y-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Full Name</label>
            <input 
              type="text" 
              className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:border-emerald-500" 
              value={fullName} 
              onChange={(e) => setFullName(e.target.value)} 
              placeholder="Dr. Jane Smith"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Email Address</label>
            <input 
              type="email" 
              className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:border-emerald-500" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="jane.smith@hospital.org"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Username</label>
            <input 
              type="text" 
              className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:border-emerald-500" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              placeholder="jsmith_md"
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Temporary Password</label>
            <input 
              type="password" 
              className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:border-emerald-500" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="w-full bg-emerald-600 text-white font-bold py-3 px-4 rounded hover:bg-emerald-700 transition-colors mt-4"
          >
            Provision Account
          </button>
        </form>
      </div>
    </div>
  );
}