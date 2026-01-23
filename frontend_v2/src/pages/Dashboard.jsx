import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Activity, FileCheck, AlertTriangle, ArrowRight, TrendingUp, Plus, ShieldCheck, Brain } from 'lucide-react';
import { cn } from '../lib/utils';

const StatCard = ({ title, value, subtitle, icon: Icon, colorClass, delay }) => (
    <div className={cn("group card p-6 relative overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-backwards", delay)}>
        <div className="relative z-10 flex flex-col justify-between h-full">
            <div className="flex justify-between items-start mb-4">
                <div className={cn("p-3 rounded-2xl shadow-sm transition-colors", colorClass)}>
                    <Icon size={24} className="text-white" />
                </div>
            </div>

            <div>
                <h3 className="text-4xl font-bold text-slate-800 tracking-tight">{value}</h3>
                <p className="text-slate-500 font-medium text-sm mt-1">{title}</p>
                {subtitle && <p className="text-xs text-slate-400 mt-2 font-medium">{subtitle}</p>}
            </div>
        </div>
        {/* Decorative background circle */}
        <div className={cn("absolute -right-6 -top-6 w-28 h-28 rounded-full opacity-5 transition-transform group-hover:scale-125", colorClass)} />
    </div>
);

const Dashboard = () => {
    const { t } = useTranslation();
    const [stats, setStats] = useState({ documents_count: 0, biomarkers_count: 0, alerts_count: 0 });
    const [recentBiomarkers, setRecentBiomarkers] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, recentRes, alertsRes] = await Promise.all([
                    api.get('/dashboard/stats'),
                    api.get('/dashboard/recent-biomarkers'),
                    api.get('/dashboard/alerts-count')
                ]);
                setStats({
                    ...statsRes.data,
                    alerts_count: alertsRes.data.alerts_count
                });
                setRecentBiomarkers(recentRes.data);
            } catch (e) {
                console.error("Failed to fetch dashboard data", e);
            }
        };
        fetchData();
    }, []);

    return (
        <div>
            {/* Quick Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard
                    title={t('dashboard.documentsCount')}
                    value={stats.documents_count}
                    icon={FileCheck}
                    colorClass="bg-primary-500"
                    delay="delay-0"
                />
                <StatCard
                    title={t('dashboard.biomarkersCount')}
                    value={stats.biomarkers_count}
                    icon={Activity}
                    colorClass="bg-teal-500"
                    delay="delay-100"
                />
                <StatCard
                    title={t('dashboard.alertsCount')}
                    value={stats.alerts_count}
                    subtitle={stats.alerts_count === 0 ? t('dashboard.allNormal') : t('dashboard.outOfRangeAlert')}
                    icon={stats.alerts_count > 0 ? AlertTriangle : ShieldCheck}
                    colorClass={stats.alerts_count > 0 ? "bg-rose-500" : "bg-indigo-500"}
                    delay="delay-200"
                />
            </div>

            {/* Quick Actions Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Upload CTA */}
                <Link to="/documents" className="card p-6 flex items-center gap-4 hover:ring-2 hover:ring-primary-500/20 group cursor-pointer hover:shadow-md transition-all">
                    <div className="p-3 bg-primary-50 rounded-xl group-hover:scale-110 transition-transform">
                        <Plus size={24} className="text-primary-600" />
                    </div>
                    <div>
                        <h4 className="font-bold text-slate-800">{t('dashboard.uploadDocument')}</h4>
                        <p className="text-sm text-slate-500">{t('dashboard.addNewPdf')}</p>
                    </div>
                    <ArrowRight size={18} className="ml-auto text-slate-300 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
                </Link>

                {/* AI Analysis CTA */}
                <Link to="/health" className="card p-6 flex items-center gap-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white group hover:shadow-md transition-all">
                    <div className="p-3 bg-white/20 rounded-xl">
                        <Brain size={24} />
                    </div>
                    <div>
                        <h4 className="font-bold">{t('dashboard.runAnalysis')}</h4>
                        <p className="text-sm text-primary-100">{t('dashboard.getHealthInsights')}</p>
                    </div>
                    <ArrowRight size={18} className="ml-auto text-primary-200 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </Link>

                {/* Sync Account CTA */}
                <Link to="/linked-accounts" className="card p-6 flex items-center gap-4 bg-gradient-to-r from-slate-700 to-slate-800 text-white group hover:shadow-md transition-all">
                    <div className="p-3 bg-white/10 rounded-xl">
                        <Activity size={24} />
                    </div>
                    <div>
                        <h4 className="font-bold">{t('dashboard.syncProviders')}</h4>
                        <p className="text-sm text-slate-300">{t('dashboard.connectMedicalAccounts')}</p>
                    </div>
                    <ArrowRight size={18} className="ml-auto text-slate-400 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </Link>
            </div>

            {/* Recent Biomarkers */}
            <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                        <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg"><TrendingUp size={18} /></span>
                        {t('dashboard.recentBiomarkers')}
                    </h3>
                    <Link to="/biomarkers" className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors">
                        {t('dashboard.viewAll')} <ArrowRight size={14} />
                    </Link>
                </div>

                <div className="space-y-3">
                    {recentBiomarkers.length === 0 ? (
                        <div className="text-center py-12 text-slate-400">
                            <Activity size={40} className="mx-auto mb-3 opacity-50" />
                            <p className="text-lg font-medium">{t('dashboard.noRecentBiomarkers')}</p>
                            <p className="text-sm mt-1">{t('dashboard.noBiomarkersHint')}</p>
                        </div>
                    ) : (
                        recentBiomarkers.map((bio, i) => (
                            <Link
                                key={i}
                                to={`/evolution/${encodeURIComponent(bio.name)}`}
                                className="group flex items-center justify-between p-4 rounded-xl border border-slate-100 hover:border-primary-200 hover:bg-primary-50/30 transition-all duration-200"
                            >
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 border-white shadow-sm",
                                        bio.status === 'normal' ? 'bg-teal-50 text-teal-600' : 'bg-rose-50 text-rose-600'
                                    )}>
                                        {bio.name.charAt(0)}
                                    </div>
                                    <div>
                                        <p className="font-semibold text-slate-800 group-hover:text-primary-700 transition-colors">{bio.name}</p>
                                        <p className="text-xs text-slate-400">{bio.date}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <p className="font-bold text-slate-700">{bio.lastValue}</p>
                                        <p className={cn("text-xs font-semibold uppercase tracking-wider", bio.status === 'normal' ? "text-teal-500" : "text-rose-500")}>
                                            {bio.status === 'normal' ? t('dashboard.normal') : t('dashboard.attention')}
                                        </p>
                                    </div>
                                    <ArrowRight size={18} className="text-slate-300 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
