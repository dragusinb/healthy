import React, { useEffect, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
  BarChart3, Users, Eye, TrendingUp, Globe, Smartphone, Monitor,
  ArrowRight, Loader2, RefreshCw, Clock, Target, ChevronDown
} from 'lucide-react';
import { cn } from '../lib/utils';

const PERIODS = [
  { value: 'today', label: 'Azi' },
  { value: '7d', label: '7 zile' },
  { value: '30d', label: '30 zile' },
  { value: '90d', label: '90 zile' },
];

const FUNNEL_LABELS = {
  home: { label: 'Pagina principală', color: 'bg-blue-500' },
  pricing: { label: 'Prețuri', color: 'bg-cyan-500' },
  login_page: { label: 'Login / Register', color: 'bg-teal-500' },
  registered: { label: 'Cont creat', color: 'bg-emerald-500' },
  dashboard: { label: 'Dashboard', color: 'bg-green-500' },
  linked_accounts: { label: 'Conturi conectate', color: 'bg-lime-500' },
  documents: { label: 'Documente', color: 'bg-yellow-500' },
  health_reports: { label: 'Rapoarte AI', color: 'bg-amber-500' },
};

export default function Analytics() {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('7d');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, liveRes] = await Promise.all([
        api.get(`/analytics/dashboard?period=${period}`),
        api.get('/analytics/live'),
      ]);
      setData(dashRes.data);
      setLive(liveRes.data);
    } catch (e) {
      console.error('Failed to fetch analytics', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [period]);

  // Auto-refresh live count every 30s
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get('/analytics/live');
        setLive(res.data);
      } catch {}
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-teal-500" size={32} />
      </div>
    );
  }

  const v = data?.visitors || {};
  const funnel = data?.funnel || {};
  const maxFunnel = Math.max(...Object.values(funnel), 1);
  const topPages = data?.top_pages || [];
  const sources = data?.sources || [];
  const devices = data?.devices || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart3 size={24} className="text-teal-600" />
            Analytics
          </h1>
          <p className="text-slate-500 text-sm mt-1">Vizitatori și comportament utilizatori</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Live indicator */}
          {live && (
            <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-semibold text-green-700">
                {live.active_visitors} {live.active_visitors === 1 ? 'vizitator' : 'vizitatori'} acum
              </span>
            </div>
          )}
          {/* Period selector */}
          <div className="flex bg-slate-100 rounded-xl p-1">
            {PERIODS.map(p => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  period === p.value
                    ? "bg-white shadow-sm text-slate-800"
                    : "text-slate-500 hover:text-slate-700"
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
          <button onClick={fetchData} className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Eye} label="Vizualizări" value={v.total || 0} color="text-blue-600" bg="bg-blue-50" />
        <StatCard icon={Users} label="Vizitatori unici" value={v.unique || 0} color="text-teal-600" bg="bg-teal-50" />
        <StatCard icon={TrendingUp} label="Reveniri" value={v.returning || 0} color="text-amber-600" bg="bg-amber-50" />
        <StatCard
          icon={Target}
          label="Rată conversie"
          value={v.unique > 0 ? `${((funnel.registered || 0) / v.unique * 100).toFixed(1)}%` : '0%'}
          color="text-emerald-600" bg="bg-emerald-50"
        />
      </div>

      {/* Chart: daily visitors */}
      {v.by_day?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">Vizitatori pe zi</h2>
          <div className="flex items-end gap-1 h-40">
            {v.by_day.map((d, i) => {
              const maxPv = Math.max(...v.by_day.map(x => x.pageviews), 1);
              const h = Math.max(4, (d.pageviews / maxPv) * 100);
              const maxVis = Math.max(...v.by_day.map(x => x.visitors), 1);
              const hVis = Math.max(2, (d.visitors / maxVis) * 100);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                    {d.date}: {d.visitors} viz, {d.pageviews} pv
                  </div>
                  <div className="w-full flex flex-col items-center gap-0.5">
                    <div
                      className="w-full bg-blue-200 rounded-t-sm transition-all"
                      style={{ height: `${h}%` }}
                    />
                    <div
                      className="w-3/4 bg-teal-400 rounded-t-sm transition-all"
                      style={{ height: `${hVis}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 mt-1">
                    {new Date(d.date).toLocaleDateString('ro', { day: 'numeric', month: 'short' })}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex items-center gap-4 mt-4 text-xs text-slate-400">
            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-blue-200 rounded" /> Vizualizări</div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-teal-400 rounded" /> Vizitatori unici</div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Funnel */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Target size={18} className="text-teal-600" />
            Funnel de conversie
          </h2>
          <div className="space-y-3">
            {Object.entries(FUNNEL_LABELS).map(([key, meta]) => {
              const count = funnel[key] || 0;
              const pct = maxFunnel > 0 ? (count / maxFunnel * 100) : 0;
              return (
                <div key={key}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-600">{meta.label}</span>
                    <span className="font-bold text-slate-800">{count}</span>
                  </div>
                  <div className="h-6 bg-slate-100 rounded-lg overflow-hidden">
                    <div
                      className={`h-full ${meta.color} rounded-lg transition-all duration-500 flex items-center justify-end pr-2`}
                      style={{ width: `${Math.max(pct, 2)}%` }}
                    >
                      {pct > 15 && <span className="text-white text-xs font-bold">{Math.round(pct)}%</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          {funnel.home > 0 && funnel.registered > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100 text-center">
              <span className="text-sm text-slate-500">
                Din <strong>{funnel.home}</strong> vizitatori, <strong>{funnel.registered}</strong> au creat cont
                ({((funnel.registered / funnel.home) * 100).toFixed(1)}%)
              </span>
            </div>
          )}
        </div>

        {/* Top pages */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Eye size={18} className="text-blue-600" />
            Top pagini
          </h2>
          <div className="space-y-2">
            {topPages.slice(0, 12).map((p, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
                <span className="w-6 text-xs text-slate-400 font-mono">{i + 1}.</span>
                <span className="flex-1 text-sm text-slate-700 truncate font-mono">{p.page}</span>
                <span className="text-sm font-bold text-slate-800">{p.views}</span>
                <span className="text-xs text-slate-400">{p.unique} unici</span>
              </div>
            ))}
            {topPages.length === 0 && <p className="text-slate-400 text-sm">Nicio vizualizare încă.</p>}
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Traffic sources */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Globe size={18} className="text-violet-600" />
            Surse de trafic
          </h2>
          <div className="space-y-2">
            {sources.map((s, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
                <span className="text-sm text-slate-700 flex-1">{s.source || 'direct'}</span>
                <span className="text-sm font-bold text-slate-800">{s.visitors}</span>
              </div>
            ))}
            {sources.length === 0 && <p className="text-slate-400 text-sm">Nicio sursă de trafic încă.</p>}
          </div>
        </div>

        {/* Devices */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <Smartphone size={18} className="text-orange-600" />
            Dispozitive
          </h2>
          <div className="flex items-center gap-8 justify-center py-4">
            <div className="text-center">
              <Monitor size={32} className="mx-auto text-slate-400 mb-2" />
              <p className="text-3xl font-bold text-slate-800">{devices.desktop || 0}</p>
              <p className="text-sm text-slate-500">Desktop</p>
            </div>
            <div className="w-px h-16 bg-slate-200" />
            <div className="text-center">
              <Smartphone size={32} className="mx-auto text-slate-400 mb-2" />
              <p className="text-3xl font-bold text-slate-800">{devices.mobile || 0}</p>
              <p className="text-sm text-slate-500">Mobile</p>
            </div>
          </div>
          {(devices.desktop > 0 || devices.mobile > 0) && (
            <div className="h-4 bg-slate-100 rounded-full overflow-hidden flex mt-4">
              <div
                className="bg-blue-400 h-full transition-all"
                style={{ width: `${(devices.desktop / ((devices.desktop || 0) + (devices.mobile || 0))) * 100}%` }}
              />
              <div className="bg-orange-400 h-full flex-1" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, bg }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center`}>
          <Icon size={20} className={color} />
        </div>
      </div>
      <p className="text-2xl font-bold text-slate-800">{typeof value === 'number' ? value.toLocaleString() : value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
