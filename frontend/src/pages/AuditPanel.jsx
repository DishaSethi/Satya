import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Search, ShieldAlert, Loader2, CheckCircle2, ShieldCheck, Clock } from 'lucide-react';
import api from '../services/api';

export default function AuditPanel() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAuditQueue = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/audit');
      console.log("🔍 RAW BACKEND DATA:", response.data);
      setLogs(response.data);
    } catch (err) {
      console.error("Failed to fetch audit queue:", err);
      setError("Database connection failed. Ensure the backend is running and PostgreSQL is connected.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditQueue();
  }, []);

  const handleResolve = async (auditId, resolution) => {
    try {
      await api.post('/api/admin/resolve', {
        audit_id: auditId,
        resolution: resolution
      });

      alert(`✅ Database Transaction Complete: '${resolution}' applied to Audit ID: ${auditId.substring(0,8)}...`);
      setLogs(logs.filter(log => log.audit_id !== auditId));

    } catch (err) {
      console.error("Failed to resolve action:", err);
      alert("❌ Database execution failed. Check backend terminal.");
    }
  };

  const getActionStyling = (action) => {
    switch (action) {
      case 'ADMIN_PENDING':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          icon: <Clock className="w-3.5 h-3.5 mr-1.5" />,
          label: 'PENDING UI PATCH'
        };
      case 'FLAG_MANUAL':
        return {
          badge: 'bg-amber-100 text-amber-800 border-amber-200',
          icon: <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />,
          label: 'INVESTIGATION REQUIRED'
        };
      case 'PASS':
        return {
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
          icon: <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />,
          label: 'VERIFIED CLEAR'
        };
      default:
        return { badge: 'bg-slate-100 text-slate-800', icon: null, label: action };
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-3 font-medium">Loading Governance Queue...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-xl flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-bold text-sm">System Alert</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Governance Audit Queue</h1>
          <p className="text-slate-500 mt-1">Human-in-the-Loop pipeline for Agentic Swarm decisions.</p>
        </div>
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Audit ID..."
            className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 w-64"
          />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {logs.length === 0 && !error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Queue is Clear</h3>
            <p className="text-slate-500 text-sm mt-1 max-w-sm">
              The Agentic Swarm has successfully routed all logs. No manual intervention required.
            </p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Context & Telemetry</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Multimodal Metrics</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Swarm Verdict</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Human Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.map((log, index) => {

                // 🛡️ INDESTRUCTIBLE MAPPER: Reads both the old mockup keys AND the new DB keys
                const auditId = log.id || log.audit_id || log.auditId || `temp-${index}`;
                const productId = log.product || log.product_id || 'Unknown';
                const details = log.text || log.event_details || 'No telemetry recorded.';

                const rawVision = parseFloat(log.visionScore ?? log.vision_discrepancy_score);
                const visionScore = isNaN(rawVision) ? 0 : rawVision;

                // Handle both boolean scamIntent and numeric pulse scores
                let pulseScore = 0;
                if (log.pulse_sentiment_score !== undefined) pulseScore = parseFloat(log.pulse_sentiment_score);
                else if (log.scamIntent === true) pulseScore = -1;
                else if (log.scamIntent === false) pulseScore = 1;

                // If the backend didn't send executed_action, we extract it directly from the telemetry text!
                let actionType = log.executed_action || log.action;
                if (!actionType && typeof details === 'string') {
                  if (details.includes('ADMIN_PENDING')) actionType = 'ADMIN_PENDING';
                  else if (details.includes('FLAG_MANUAL')) actionType = 'FLAG_MANUAL';
                  else if (details.includes('PASS')) actionType = 'PASS';
                  else actionType = 'FLAG_MANUAL'; // Fallback
                }

                const styles = getActionStyling(actionType);

                return (
                  // COMBINED KEY: Guaranteed to be 100% unique, killing the React warning
                  <tr key={`${auditId}-${index}`} className="hover:bg-slate-50 transition-colors">

                    <td className="px-6 py-4 max-w-md">
                      <div className="font-mono text-slate-900 text-xs font-medium border border-slate-200 bg-slate-100 rounded px-1.5 py-0.5 inline-block mb-2">
                        Product: {productId}
                      </div>

                      <div className="mt-3 text-[11px] text-emerald-400 bg-slate-900 p-4 rounded-lg border border-slate-700 leading-relaxed font-mono shadow-inner whitespace-pre-wrap">
                        <div className="text-slate-400 mb-2 border-b border-slate-700 pb-1">-- Llama-3 Reasoning Log --</div>
                        {details}
                      </div>
                    </td>

                    <td className="px-6 py-4 align-top pt-6">
                      <div className="flex flex-col space-y-3 text-sm">
                        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                          <span className="text-slate-500 text-xs font-medium mr-3">Vision Variance:</span>
                          <span className={`font-mono font-medium px-2 py-0.5 rounded ${visionScore > 0.35 ? 'text-orange-600 bg-orange-50' : 'text-emerald-600 bg-emerald-50'}`}>
                            {visionScore.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500 text-xs font-medium mr-3">NLP Sentiment:</span>
                          <span className={`font-mono font-medium px-2 py-0.5 rounded ${pulseScore < 0 ? 'text-red-600 bg-red-50' : 'text-emerald-600 bg-emerald-50'}`}>
                            {pulseScore < 0 ? 'NEGATIVE' : 'POSITIVE'}
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4 align-top pt-6">
                      <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${styles.badge} mb-2`}>
                        {styles.icon}
                        {styles.label}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right space-y-2 align-top pt-6">
                      {actionType === 'ADMIN_PENDING' && (
                        <>
                          <button onClick={() => handleResolve(auditId, 'APPROVE_PATCH')} className="w-full inline-flex items-center justify-center px-3 py-1.5 bg-orange-600 text-white rounded-lg text-xs font-medium hover:bg-orange-700 shadow-sm transition-colors">
                            <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
                            Approve Warning Patch
                          </button>
                          <button onClick={() => handleResolve(auditId, 'REJECT')} className="w-full inline-flex items-center justify-center px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-50 shadow-sm transition-colors mt-2">
                            <XCircle className="w-3.5 h-3.5 mr-1.5" />
                            Reject & Clear
                          </button>
                        </>
                      )}

                      {actionType === 'FLAG_MANUAL' && (
                        <>
                          <button onClick={() => handleResolve(auditId, 'BAN_USER')} className="w-full inline-flex items-center justify-center px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-medium hover:bg-red-700 shadow-sm transition-colors">
                            <ShieldAlert className="w-3.5 h-3.5 mr-1.5" />
                            Ban Malicious User
                          </button>
                          <button onClick={() => handleResolve(auditId, 'DISMISS')} className="w-full inline-flex items-center justify-center px-3 py-1.5 bg-white border border-slate-200 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-50 shadow-sm transition-colors mt-2">
                            Dismiss Warning
                          </button>
                        </>
                      )}

                      {actionType === 'PASS' && (
                        <button onClick={() => handleResolve(auditId, 'ACKNOWLEDGE')} className="w-full inline-flex items-center justify-center px-3 py-1.5 bg-white border border-emerald-200 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-50 shadow-sm transition-colors">
                          <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                          Acknowledge Log
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        )}
      </div>
    </div>
  );
}