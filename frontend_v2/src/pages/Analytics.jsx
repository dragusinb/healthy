import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Loader2, RefreshCw } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = {
  blue: '#3b82f6',
  purple: '#a855f7',
  green: '#22c55e',
  orange: '#f59e0b',
  gray: '#9ca3af',
  grid: '#e5e7eb',
};

export default function Analytics() {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, liveRes] = await Promise.all([
        api.get('/analytics/dashboard?period=30d'),
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

  useEffect(() => { fetchData(); }, []);

  // Auto-refresh live count
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
  const vt = data?.visitor_types || {};
  const conv = data?.conversion_30d || {};

  // Ensure by_day has all 30 days filled
  const pageViewsByDay = fillDays(v.by_day || [], 30, 'pageviews');
  const blogByDay = fillDays(data?.blog_by_day || [], 30, 'views');
  const accountsByDay = fillDays(data?.new_accounts_by_day || [], 30, 'count');

  // Visitor types for donut
  const visitorTypesData = [
    { name: t('analyticsPage.loggedIn'), value: vt.logged_in || 0, color: COLORS.blue },
    { name: 'Refcode', value: vt.refcode || 0, color: COLORS.orange },
    { name: t('analyticsPage.anonymous'), value: vt.anonymous || 0, color: COLORS.gray },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t('analyticsPage.title')}</h1>
          <p className="text-slate-500 text-sm mt-1">
            {t('analyticsPage.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {live && (
            <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-semibold text-green-700">
                {live.active_visitors} {live.active_visitors === 1 ? t('analyticsPage.visitorNow') : t('analyticsPage.visitorsNow')}
              </span>
            </div>
          )}
          <button
            onClick={fetchData}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title={t('analyticsPage.totalUsers')}
          value={data?.total_users || 0}
          subtitle={`+${data?.new_users_7d || 0} ${t('analyticsPage.last7days')}`}
        />
        <KpiCard
          title={t('analyticsPage.pageViews30d')}
          value={v.total || 0}
          subtitle={`${(data?.pageviews_7d || 0).toLocaleString()} ${t('analyticsPage.last7days')} / ${(data?.pageviews_today || 0).toLocaleString()} ${t('analyticsPage.today')}`}
        />
        <KpiCard
          title={t('analyticsPage.blogViews30d')}
          value={data?.blog_views_30d || 0}
          subtitle={`${data?.blog_views_7d || 0} ${t('analyticsPage.last7days')}`}
        />
        <KpiCard
          title={t('analyticsPage.visitorConversion')}
          value={`${conv.rate || 0}%`}
          subtitle={`${conv.registered || 0} ${t('analyticsPage.from')} ${conv.total_visitors || 0} ${t('analyticsPage.visitors')}`}
        />
      </div>

      {/* Line Charts Row 1 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title={t('analyticsPage.pageViewsChart')}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={pageViewsByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              <Line type="monotone" dataKey="value" stroke={COLORS.blue} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title={t('analyticsPage.blogViewsChart')}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={blogByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              <Line type="monotone" dataKey="value" stroke={COLORS.purple} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Line Chart + Donut Row 2 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title={t('analyticsPage.newAccountsChart')}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={accountsByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              <Line type="monotone" dataKey="value" stroke={COLORS.green} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title={t('analyticsPage.visitorTypes')}>
          {visitorTypesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={visitorTypesData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {visitorTypesData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value) => <span className="text-slate-600 text-sm">{value}</span>}
                  iconType="circle"
                />
                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-slate-400 text-sm">
              {t('analyticsPage.noData')}
            </div>
          )}
        </ChartCard>
      </div>
    </div>
  );
}

/* ----- Helper Components ----- */

function KpiCard({ title, value, subtitle }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{title}</p>
      <p className="text-3xl font-bold text-slate-800">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
      <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <h3 className="text-sm font-bold text-slate-800 mb-4">{title}</h3>
      {children}
    </div>
  );
}

/* Fill missing days in a date-series array so the chart has no gaps */
function fillDays(data, days, valueKey) {
  const map = {};
  data.forEach(d => { map[d.date] = d[valueKey] || 0; });

  const result = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const dt = new Date(now);
    dt.setDate(dt.getDate() - i);
    const key = dt.toISOString().split('T')[0];
    const label = `${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
    result.push({ date: key, label, value: map[key] || 0 });
  }
  return result;
}
