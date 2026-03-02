import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HeartPulse, Lock, AlertTriangle, Clock, Eye, Brain,
  Shield, ChevronDown, ChevronUp
} from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../api/client';

const RISK_COLORS = {
  normal: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  attention: 'bg-amber-50 text-amber-700 border-amber-200',
  concern: 'bg-orange-50 text-orange-700 border-orange-200',
  urgent: 'bg-rose-50 text-rose-700 border-rose-200',
};

export default function SharedReport() {
  const { token } = useParams();
  const { t, i18n } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [needsPassword, setNeedsPassword] = useState(false);
  const [password, setPassword] = useState('');
  const [expandedReports, setExpandedReports] = useState({});

  const fetchReport = async (pwd = null) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post(`/sharing/view/${token}`, { password: pwd });
      if (res.data.requires_password) {
        setNeedsPassword(true);
      } else {
        setData(res.data);
        setNeedsPassword(false);
      }
    } catch (e) {
      const status = e.response?.status;
      if (status === 401) {
        setError(t('sharing.wrongPassword'));
        setNeedsPassword(true);
      } else if (status === 410) {
        setError(t('sharing.expired'));
      } else if (status === 404) {
        setError(t('sharing.notFound'));
      } else {
        setError(t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReport(); }, [token]);

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    fetchReport(password);
  };

  const toggleReport = (index) => {
    setExpandedReports(prev => ({ ...prev, [index]: !prev[index] }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (needsPassword) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Lock size={28} className="text-primary-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">{t('sharing.passwordRequired')}</h2>
          <p className="text-slate-500 text-sm mb-6">{t('sharing.enterPassword')}</p>
          {error && (
            <div className="mb-4 p-3 bg-rose-50 text-rose-600 text-sm rounded-lg">{error}</div>
          )}
          <form onSubmit={handlePasswordSubmit}>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder={t('sharing.passwordPlaceholder')}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg mb-4"
              autoFocus
            />
            <button type="submit"
              className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
            >
              {t('sharing.viewReport')}
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle size={28} className="text-rose-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">{t('sharing.errorTitle')}</h2>
          <p className="text-slate-500">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const generalReport = data.reports.find(r => r.report_type === 'general');
  const specialistReports = data.reports.filter(r => r.report_type !== 'general');

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
              <HeartPulse className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-slate-800">Analize.Online</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1"><Eye size={12} /> {data.view_count} views</span>
            <span className="flex items-center gap-1"><Clock size={12} /> {t('sharing.expiresOn')} {new Date(data.expires_at).toLocaleDateString()}</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 md:p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-800 mb-1">{t('sharing.sharedReport')}</h1>
          <p className="text-slate-500 text-sm flex items-center gap-1">
            <Shield size={14} /> {t('sharing.readOnly')}
          </p>
        </div>

        {/* General Report */}
        {generalReport && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-primary-50 rounded-lg">
                <Brain size={20} className="text-primary-600" />
              </div>
              <div>
                <h2 className="font-bold text-slate-800">{generalReport.title}</h2>
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  {generalReport.risk_level && (
                    <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold border", RISK_COLORS[generalReport.risk_level])}>
                      {t(`healthReports.riskLevels.${generalReport.risk_level}`)}
                    </span>
                  )}
                  <span>{new Date(generalReport.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {generalReport.content?.summary && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wider mb-2">{t('healthReports.keyFindings')}</h3>
                <p className="text-slate-700 whitespace-pre-line">{generalReport.content.summary}</p>
              </div>
            )}

            {generalReport.content?.findings && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wider mb-2">{t('healthReports.findings')}</h3>
                <p className="text-slate-700 whitespace-pre-line">{generalReport.content.findings}</p>
              </div>
            )}

            {generalReport.content?.recommendations && (
              <div>
                <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wider mb-2">{t('healthReports.recommendations')}</h3>
                <p className="text-slate-700 whitespace-pre-line">{generalReport.content.recommendations}</p>
              </div>
            )}
          </div>
        )}

        {/* Specialist Reports */}
        {specialistReports.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-slate-800">{t('healthReports.specialistAnalyses')}</h2>
            {specialistReports.map((report, i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <button
                  onClick={() => toggleReport(i)}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-slate-800">{report.title}</span>
                    {report.risk_level && (
                      <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold border", RISK_COLORS[report.risk_level])}>
                        {t(`healthReports.riskLevels.${report.risk_level}`)}
                      </span>
                    )}
                  </div>
                  {expandedReports[i] ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </button>
                {expandedReports[i] && (
                  <div className="px-4 pb-4 border-t border-slate-100 pt-3">
                    {report.content?.summary && (
                      <p className="text-slate-700 whitespace-pre-line mb-3">{report.content.summary}</p>
                    )}
                    {report.content?.findings && (
                      <div className="mb-3">
                        <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1">{t('healthReports.findings')}</h4>
                        <p className="text-slate-700 whitespace-pre-line text-sm">{report.content.findings}</p>
                      </div>
                    )}
                    {report.content?.recommendations && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1">{t('healthReports.recommendations')}</h4>
                        <p className="text-slate-700 whitespace-pre-line text-sm">{report.content.recommendations}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
          {t('healthReports.disclaimer')}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-400">
          <p>{t('sharing.poweredBy')} <a href="https://analize.online" className="text-primary-600 hover:underline">Analize.Online</a></p>
        </div>
      </main>
    </div>
  );
}
