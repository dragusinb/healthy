import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import DocumentList from './components/DocumentList';
import Trends from './components/Trends';
import { Activity, AlertCircle, FileText, CheckCircle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [documents, setDocuments] = useState([]);
  const [results, setResults] = useState([]);
  const [insights, setInsights] = useState({ trends: [], latest_summary: '' });
  const [loading, setLoading] = useState(true);

  // Fetch Data
  useEffect(() => {
    async function fetchData() {
      try {
        const [docsRes, resRes, insRes] = await Promise.all([
          fetch('http://localhost:8000/documents'),
          fetch('http://localhost:8000/results'),
          fetch('http://localhost:8000/insights')
        ]);

        const docs = await docsRes.json();
        const res = await resRes.json();
        const ins = await insRes.json();

        setDocuments(docs);
        setResults(res);
        setInsights(ins);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Stats
  const totalTests = results.length;
  const abnormalTests = results.filter(r => r.flags === 'HIGH' || r.flags === 'LOW').length;

  // Render Content based on Tab
  const renderContent = () => {
    if (activeTab === 'dashboard') {
      return (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                <FileText size={24} />
              </div>
              <div>
                <p className="text-gray-500 text-sm">Total Documents</p>
                <h3 className="text-2xl font-bold text-gray-900">{documents.length}</h3>
              </div>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-teal-50 flex items-center justify-center text-teal-600">
                <Activity size={24} />
              </div>
              <div>
                <p className="text-gray-500 text-sm">Total Tests Analyzed</p>
                <h3 className="text-2xl font-bold text-gray-900">{totalTests}</h3>
              </div>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${abnormalTests > 0 ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'}`}>
                {abnormalTests > 0 ? <AlertCircle size={24} /> : <CheckCircle size={24} />}
              </div>
              <div>
                <p className="text-gray-500 text-sm">Action Needed</p>
                <h3 className="text-2xl font-bold text-gray-900">{abnormalTests} Alerts</h3>
              </div>
            </div>
          </div>

          {/* AI Summary */}
          <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-xl p-6 text-white shadow-lg relative overflow-hidden">
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-2 text-teal-300">
                <Activity size={18} />
                <span className="text-xs font-bold uppercase tracking-wider">AI Health Insight</span>
              </div>
              <h2 className="text-lg font-semibold mb-2">Latest Analysis</h2>
              <p className="text-slate-300 text-sm leading-relaxed max-w-2xl">
                {insights.latest_summary || "No recent analysis available."}
              </p>
            </div>
            {/* Decorative Blob */}
            <div className="absolute right-0 top-0 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Trends */}
            <div className="lg:col-span-2 space-y-6">
              <h3 className="text-lg font-bold text-slate-800">Health Trends</h3>
              <Trends results={results} />
            </div>

            {/* Alerts/Insights Side */}
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-slate-800">Detected Insights</h3>
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-0 overflow-hidden">
                {insights.trends && insights.trends.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {insights.trends.map((trend, i) => (
                      <div key={i} className="p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex items-start gap-3">
                          <div className={`mt-1 p-1 rounded ${trend.includes('increased') ? 'bg-red-50 text-red-500' : 'bg-blue-50 text-blue-500'}`}>
                            <Activity size={14} />
                          </div>
                          <p className="text-sm text-gray-600">{trend}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-gray-400 text-sm">No major trends detected.</div>
                )}
              </div>
            </div>
          </div>

          <DocumentList documents={documents.slice(0, 5)} />
        </div>
      );
    }

    if (activeTab === 'documents') {
      return <DocumentList documents={documents} />;
    }

    if (activeTab === 'trends') {
      return (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-900">Detailed Analysis</h2>
          <Trends results={results} />
        </div>
      );
    }

    return <div className="p-12 text-center text-gray-500">Settings Coming Soon</div>;
  };

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        {/* Top Bar (Mobile placeholder) */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 capitalize">
              {activeTab === 'dashboard' ? 'Health Overview' : activeTab}
            </h1>
            <p className="text-slate-500 text-sm">Welcome back, Bogdan.</p>
          </div>
          <button className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm shadow-teal-200">
            + Upload Document
          </button>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
          </div>
        ) : renderContent()}
      </main>
    </div>
  );
}
