import React, { useState } from 'react';
import { ShieldAlert, User, Eye, LayoutDashboard } from 'lucide-react';
import AuditPanel from './pages/AuditPanel';
import SellerDashboard from './pages/SellerDashboard';
import CustomerView from './pages/CustomerView';

export default function App() {
  const [activeTab, setActiveTab] = useState('admin');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Global Navigation Header */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-6 h-6 text-indigo-600" />
              <span className="font-bold text-xl tracking-tight text-slate-800">Project Satya</span>
              <span className="bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full font-medium border border-indigo-100">MVP</span>
            </div>

            <div className="flex space-x-1 bg-slate-100 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('customer')}
                className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'customer'
                    ? 'bg-white text-indigo-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Eye className="w-4 h-4" />
                <span>Customer View</span>
              </button>

              <button
                onClick={() => setActiveTab('seller')}
                className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'seller'
                    ? 'bg-white text-indigo-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <User className="w-4 h-4" />
                <span>Seller Portal</span>
              </button>

              <button
                onClick={() => setActiveTab('admin')}
                className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'admin'
                    ? 'bg-white text-indigo-600 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Admin Audit</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="transition-opacity duration-200">
          {activeTab === 'customer' && <CustomerView />}
          {activeTab === 'seller' && <SellerDashboard />}
          {activeTab === 'admin' && <AuditPanel />}
        </div>
      </main>
    </div>
  );
}