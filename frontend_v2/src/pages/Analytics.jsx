import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Loader2, RefreshCw, ExternalLink } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend, BarChart, Bar
} from 'recharts';

const COLORS = {
  blue: '#3b82f6',
  purple: '#a855f7',
  green: '#22c55e',
  orange: '#f59e0b',
  red: '#ef4444',
  teal: '#14b8a6',
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
  const biomarkerByDay = fillDays(data?.biomarker_by_day || [], 30, 'views');
  const analyzerByDay = fillDays(data?.analyzer_by_day || [], 30, 'views');

  // Visitor types for donut
  const visitorTypesData = [
    { name: t('analyticsPage.loggedIn'), value: vt.logged_in || 0, color: COLORS.blue },
    { name: 'Refcode', value: vt.refcode || 0, color: COLORS.orange },
    { name: t('analyticsPage.anonymous'), value: vt.anonymous || 0, color: COLORS.gray },
  ].filter(d => d.value > 0);

  const topBlogArticles = data?.top_blog_articles || [];
  const topBiomarkers = data?.top_biomarkers || [];
  const topPages = data?.top_pages || [];
  const sources = data?.sources || [];

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

      {/* KPI Cards - Row 1 */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
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
          accent="purple"
        />
        <KpiCard
          title={t('analyticsPage.biomarkerViews30d')}
          value={data?.biomarker_views_30d || 0}
          subtitle={`${data?.biomarker_views_7d || 0} ${t('analyticsPage.last7days')}`}
          accent="teal"
        />
        <KpiCard
          title={t('analyticsPage.analyzerViews30d')}
          value={data?.analyzer_views_30d || 0}
          subtitle={`${data?.analyzer_views_7d || 0} ${t('analyticsPage.last7days')}`}
          accent="orange"
        />
        <KpiCard
          title={t('analyticsPage.visitorConversion')}
          value={`${conv.rate || 0}%`}
          subtitle={`${conv.registered || 0} ${t('analyticsPage.from')} ${conv.total_visitors || 0} ${t('analyticsPage.visitors')}`}
        />
      </div>

      {/* Line Charts Row 1: Page views + Blog views */}
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

      {/* Line Charts Row 2: Biomarker + Analyzer views */}
      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title={t('analyticsPage.biomarkerViewsChart')}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={biomarkerByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              <Line type="monotone" dataKey="value" stroke={COLORS.teal} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title={t('analyticsPage.analyzerViewsChart')}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={analyzerByDay}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
              <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
              <Line type="monotone" dataKey="value" stroke={COLORS.orange} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Top Blog Articles Table */}
      <ChartCard title={t('analyticsPage.topBlogArticles')}>
        {topBlogArticles.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 px-3 text-slate-500 font-medium">#</th>
                  <th className="text-left py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.article')}</th>
                  <th className="text-right py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.views')}</th>
                  <th className="text-right py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.unique')}</th>
                </tr>
              </thead>
              <tbody>
                {topBlogArticles.map((a, i) => (
                  <tr key={a.page} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 px-3 text-slate-400">{i + 1}</td>
                    <td className="py-2 px-3">
                      <a
                        href={a.page}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center gap-1"
                      >
                        {formatSlug(a.slug)}
                        <ExternalLink size={12} className="text-slate-400" />
                      </a>
                    </td>
                    <td className="py-2 px-3 text-right font-semibold text-slate-700">{a.views}</td>
                    <td className="py-2 px-3 text-right text-slate-500">{a.unique}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center h-[120px] text-slate-400 text-sm">
            {t('analyticsPage.noArticles')}
          </div>
        )}
      </ChartCard>

      {/* Top Biomarker Pages Table */}
      <ChartCard title={t('analyticsPage.topBiomarkers')}>
        {topBiomarkers.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 px-3 text-slate-500 font-medium">#</th>
                  <th className="text-left py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.biomarker')}</th>
                  <th className="text-right py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.views')}</th>
                  <th className="text-right py-2 px-3 text-slate-500 font-medium">{t('analyticsPage.unique')}</th>
                </tr>
              </thead>
              <tbody>
                {topBiomarkers.map((b, i) => (
                  <tr key={b.page} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 px-3 text-slate-400">{i + 1}</td>
                    <td className="py-2 px-3">
                      <a
                        href={b.page}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal-600 hover:underline flex items-center gap-1"
                      >
                        {formatSlug(b.slug)}
                        <ExternalLink size={12} className="text-slate-400" />
                      </a>
                    </td>
                    <td className="py-2 px-3 text-right font-semibold text-slate-700">{b.views}</td>
                    <td className="py-2 px-3 text-right text-slate-500">{b.unique}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center h-[120px] text-slate-400 text-sm">
            {t('analyticsPage.noBiomarkers')}
          </div>
        )}
      </ChartCard>

      {/* Row: Top Pages + Sources + Visitor Types */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Top Pages */}
        <ChartCard title={t('analyticsPage.topPages')}>
          <div className="space-y-1 max-h-[280px] overflow-y-auto">
            {topPages.map((p, i) => (
              <div key={p.page} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-slate-50 text-sm">
                <span className="text-slate-600 truncate flex-1 mr-2">
                  <span className="text-slate-400 mr-1.5">{i + 1}.</span>
                  {p.page}
                </span>
                <span className="font-semibold text-slate-700 whitespace-nowrap">{p.views}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Traffic Sources */}
        <ChartCard title={t('analyticsPage.trafficSources')}>
          <div className="space-y-1 max-h-[280px] overflow-y-auto">
            {sources.map((s, i) => (
              <div key={s.source} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-slate-50 text-sm">
                <span className="text-slate-600 truncate flex-1 mr-2">
                  <span className="text-slate-400 mr-1.5">{i + 1}.</span>
                  {s.source}
                </span>
                <span className="font-semibold text-slate-700 whitespace-nowrap">{s.visitors}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Visitor Types Donut */}
        <ChartCard title={t('analyticsPage.visitorTypes')}>
          {visitorTypesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={visitorTypesData}
                  cx="50%"
                  cy="45%"
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
            <div className="flex items-center justify-center h-[280px] text-slate-400 text-sm">
              {t('analyticsPage.noData')}
            </div>
          )}
        </ChartCard>
      </div>

      {/* New Accounts Chart */}
      <ChartCard title={t('analyticsPage.newAccountsChart')}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={accountsByDay}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, color: '#1e293b' }} />
            <Line type="monotone" dataKey="value" stroke={COLORS.green} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

/* ----- Helper Components ----- */

function KpiCard({ title, value, subtitle, accent }) {
  const accentBorder = accent === 'purple' ? 'border-l-purple-400'
    : accent === 'teal' ? 'border-l-teal-400'
    : accent === 'orange' ? 'border-l-orange-400'
    : '';
  return (
    <div className={`bg-white rounded-2xl border border-slate-200 p-5 ${accent ? `border-l-4 ${accentBorder}` : ''}`}>
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

/* Format a slug to readable text: "hemoglobina-valori-normale" → "Hemoglobina valori normale" */
function formatSlug(slug) {
  if (!slug) return '';
  return slug.replace(/-/g, ' ').replace(/^\w/, c => c.toUpperCase());
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
