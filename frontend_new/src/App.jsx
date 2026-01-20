import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import DocumentList from './components/DocumentList';
import ResultsList from './components/ResultsList';
import Trends from './components/Trends';
import DoctorDashboard, { TrendCard } from './components/DoctorDashboard';
import { Activity, AlertCircle, CheckCircle, FileText, Search, Bell } from 'lucide-react';
import axios from 'axios';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [documents, setDocuments] = useState([]);
  const [results, setResults] = useState([]);
  const [insights, setInsights] = useState({ trends: [], latest_summary: '' });
  const [loading, setLoading] = useState(true);

  // Navigation State
  const [trendCategory, setTrendCategory] = useState('');
  const [trendTest, setTrendTest] = useState('');

  // Results Filter State
  const [filterAbnormal, setFilterAbnormal] = useState(false);

  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setErrorMsg(null);
        const [docsRes, resRes, insRes] = await Promise.all([
          axios.get('/documents'),
          axios.get('/results'),
          axios.get('/insights')
        ]);

        setDocuments(docsRes.data);
        setResults(resRes.data);
        setInsights(insRes.data);
      } catch (error) {
        console.error("Failed to fetch data:", error);
        setErrorMsg(error.message + " (Check backend console)");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // Smart Default for Trend Chart
  useEffect(() => {
    if (results.length > 0 && !trendTest) {
      // 1. Sort by Date Descending
      const sorted = [...results].sort((a, b) => new Date(b.date) - new Date(a.date));

      // 2. Find most recent abnormal
      const recentAbnormal = sorted.find(r => r.flags === 'HIGH' || r.flags === 'LOW' || r.flags === 'POS');

      if (recentAbnormal) {
        setTrendTest(recentAbnormal.test_name);
        // Also set category if needed (Trends component handles sync, but good to be safe)
      } else {
        // Fallback to most recent test
        setTrendTest(sorted[0].test_name);
      }
    }
  }, [results, trendTest]);

  // Stats Calculation
  const totalTests = results.length;
  const abnormalTests = results.filter(r => r.flags === 'HIGH' || r.flags === 'LOW').length;

  // Handler for dashboard navigation
  const handleViewAlerts = () => {
    setFilterAbnormal(true);
    setActiveTab('results');
  };

  const renderContent = () => {
    if (activeTab === 'dashboard') {
      return (
        <div className="space-y-8 animate-in fade-in duration-500">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-500 text-sm font-medium">Total Documents</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-2">{documents.length}</h3>
                </div>
                <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                  <FileText size={24} />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-500 text-sm font-medium">Tests Analyzed</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-2">{totalTests}</h3>
                </div>
                <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
                  <Activity size={24} />
                </div>
              </div>
            </div>

            <div
              className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer group"
              onClick={handleViewAlerts}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-500 text-sm font-medium group-hover:text-amber-600 transition-colors">Attention Needed</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-2">{abnormalTests}</h3>
                </div>
                <div className={`p-3 rounded-xl ${abnormalTests > 0 ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'}`}>
                  {abnormalTests > 0 ? <AlertCircle size={24} /> : <CheckCircle size={24} />}
                </div>
              </div>
            </div>
          </div>

          {/* AI Insight Banner */}
          <div className="bg-slate-900 rounded-2xl p-8 text-white relative overflow-hidden shadow-xl">
            <div className="relative z-10 max-w-3xl">
              <div className="flex items-center gap-2 mb-3">
                <div className="px-2 py-1 bg-teal-500/20 rounded text-teal-300 text-xs font-bold uppercase tracking-wider border border-teal-500/30">
                  AI Analysis
                </div>
                <span className="text-slate-400 text-xs">Updated just now</span>
              </div>
              <h2 className="text-xl font-semibold mb-3">Health Insights</h2>
              <p className="text-slate-300 leading-relaxed text-lg">
                {insights.latest_summary || "No recent analysis available from your documents."}
              </p>
            </div>
            <div className="absolute right-0 top-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
          </div>

          {/* Main Grid: Trends & Alerts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 h-full">
              <Trends
                results={results}
                selectedTest={trendTest}
                setSelectedTest={setTrendTest}
                selectedCategory={trendCategory}
                setSelectedCategory={setTrendCategory}
              />
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Activity size={18} className="text-teal-600" />
                Detected Trends
              </h3>
              {insights.trends && insights.trends.length > 0 ? (
                <div className="space-y-4">
                  {insights.trends.map((trend, i) => (
                    <TrendCard
                      key={i}
                      trend={trend}
                      onClick={() => {
                        setTrendTest(trend.test_name);
                        setActiveTab('trends');
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">No significant trends detected.</div>
              )}
            </div>
          </div>

          <DocumentList documents={documents.slice(0, 5)} />
        </div>
      );
    }

    if (activeTab === 'documents') return <DocumentList documents={documents} />;

    if (activeTab === 'results') return (
      <ResultsList
        results={results}
        initialFilterAbnormal={filterAbnormal}
        onTestClick={(testName) => {
          setTrendTest(testName);
          setActiveTab('trends');
        }}
      />
    );

    if (activeTab === 'trends') return (
      <div className="h-[600px]">
        <Trends
          results={results}
          selectedTest={trendTest}
          setSelectedTest={setTrendTest}
          selectedCategory={trendCategory}
          setSelectedCategory={setTrendCategory}
        />
      </div>
    );

    if (activeTab === 'analysis') return (
      <DoctorDashboard
        onNavigate={(testName) => {
          setTrendTest(testName);
          setActiveTab('trends');
        }}
        onViewAlerts={handleViewAlerts}
      />
    );

    return <div className="p-12 text-center text-gray-500">Settings Section - Coming Soon</div>;
  };

  return (
    <div className="min-h-screen bg-slate-50/50 font-sans text-slate-900 selection:bg-teal-100">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="pl-64">
        {/* Top Header */}
        <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100 px-8 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-slate-900 capitalize tracking-tight">
              {activeTab === 'dashboard' ? 'Overview' : activeTab}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search records..."
                className="pl-10 pr-4 py-2 bg-slate-100 border-transparent focus:bg-white focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 rounded-lg text-sm transition-all outline-none w-64"
              />
            </div>
            <button className="bg-teal-600 hover:bg-teal-700 text-white px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-teal-500/20 flex items-center gap-2">
              <span>Upload New</span>
            </button>
          </div>
        </header>

        <div className="p-8 max-w-7xl mx-auto">
          {errorMsg && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
              <strong className="font-bold">Connection Error: </strong>
              <span className="block sm:inline">{errorMsg}</span>
              <p className="text-sm mt-1">Make sure backend is running on port 8000.</p>
            </div>
          )}
          {loading ? (
            <div className="flex h-[50vh] items-center justify-center flex-col gap-4">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal-600"></div>
              <p className="text-slate-500 text-sm font-medium animate-pulse">Loading health data...</p>
            </div>
          ) : renderContent()}
        </div>
      </main>
    </div>
  );
}
