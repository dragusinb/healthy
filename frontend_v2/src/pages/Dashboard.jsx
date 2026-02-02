import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
    Activity, FileCheck, AlertTriangle, ArrowRight, TrendingUp, Plus, ShieldCheck, Brain, KeyRound, X,
    User, Calendar, Clock, Heart, Droplets, Bell, CheckCircle2, AlertCircle, Sparkles
} from 'lucide-react';
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
    const [accountErrors, setAccountErrors] = useState([]);
    const [dismissedErrors, setDismissedErrors] = useState([]);
    const [healthOverview, setHealthOverview] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, recentRes, alertsRes, userRes, overviewRes] = await Promise.all([
                    api.get('/dashboard/stats'),
                    api.get('/dashboard/recent-biomarkers'),
                    api.get('/dashboard/alerts-count'),
                    api.get('/users/me'),
                    api.get('/dashboard/health-overview')
                ]);
                setStats({
                    ...statsRes.data,
                    alerts_count: alertsRes.data.alerts_count
                });
                setRecentBiomarkers(recentRes.data);
                setHealthOverview(overviewRes.data);

                // Check for unacknowledged provider errors
                const accounts = userRes.data.linked_accounts || [];
                const errors = accounts.filter(acc =>
                    acc.status === 'ERROR' && !acc.error_acknowledged
                );
                setAccountErrors(errors);
            } catch (e) {
                console.error("Failed to fetch dashboard data", e);
            }
        };
        fetchData();
    }, []);

    const dismissError = async (accountId) => {
        try {
            await api.post(`/users/accounts/${accountId}/acknowledge-error`);
            setDismissedErrors(prev => [...prev, accountId]);
        } catch (e) {
            console.error("Failed to dismiss error", e);
        }
    };

    // Filter out server errors (users can't fix those) and dismissed errors
    const visibleErrors = accountErrors.filter(acc =>
        !dismissedErrors.includes(acc.id) &&
        acc.error_type !== 'server_error' &&
        acc.error_type !== 'timeout'  // Also hide timeouts - not user-fixable
    );

    const getErrorMessage = (errorType) => {
        const messages = {
            wrong_password: t('linkedAccounts.errors.wrongPassword'),
            captcha_failed: t('linkedAccounts.errors.captchaFailed'),
            site_down: t('linkedAccounts.errors.siteDown'),
            server_error: t('linkedAccounts.errors.serverError'),
            session_expired: t('linkedAccounts.errors.sessionExpired'),
            timeout: t('linkedAccounts.errors.timeout'),
            unknown: t('linkedAccounts.errors.unknown')
        };
        return messages[errorType] || messages.unknown;
    };

    return (
        <div>
            {/* Provider Error Notifications */}
            {visibleErrors.length > 0 && (
                <div className="mb-6 space-y-3">
                    {visibleErrors.map(acc => (
                        <div key={acc.id} className="flex items-center gap-4 p-4 bg-rose-50 border border-rose-200 rounded-xl animate-in fade-in slide-in-from-top-4 duration-300">
                            <div className="p-2 bg-rose-100 rounded-lg">
                                <KeyRound size={20} className="text-rose-600" />
                            </div>
                            <div className="flex-1">
                                <p className="font-semibold text-rose-800">
                                    {acc.provider_name}: {getErrorMessage(acc.error_type || 'unknown')}
                                </p>
                                <p className="text-sm text-rose-600">
                                    {t('linkedAccounts.errors.' + (acc.error_type || 'unknown') + 'Desc')}
                                </p>
                            </div>
                            <Link
                                to="/linked-accounts"
                                className="px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 transition-colors"
                            >
                                {t('linkedAccounts.updateCredentials') || 'Fix'}
                            </Link>
                            <button
                                onClick={() => dismissError(acc.id)}
                                className="p-2 hover:bg-rose-100 rounded-lg transition-colors text-rose-400 hover:text-rose-600"
                                title={t('common.close')}
                            >
                                <X size={18} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Health Overview Section */}
            {healthOverview && (
                <div className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="card p-6">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                                <span className="p-1.5 bg-primary-50 text-primary-600 rounded-lg"><Heart size={18} /></span>
                                {t('dashboard.healthOverview') || 'Health Overview'}
                            </h2>
                            {!healthOverview.profile_complete && (
                                <Link to="/profile" className="text-sm text-amber-600 hover:text-amber-700 flex items-center gap-1">
                                    <AlertCircle size={14} />
                                    {t('dashboard.completeProfile') || 'Complete your profile'}
                                </Link>
                            )}
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Patient Identity */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white text-xl font-bold shadow-lg">
                                        {healthOverview.profile?.full_name?.charAt(0)?.toUpperCase() || <User size={24} />}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-slate-800 text-lg">
                                            {healthOverview.profile?.full_name || t('dashboard.unknownPatient') || 'Unknown Patient'}
                                        </h3>
                                        <div className="flex items-center gap-3 text-sm text-slate-500">
                                            {healthOverview.profile?.age && (
                                                <span className="flex items-center gap-1">
                                                    <Calendar size={12} />
                                                    {healthOverview.profile.age} {t('dashboard.yearsOld') || 'years'}
                                                </span>
                                            )}
                                            {healthOverview.profile?.gender && (
                                                <span className="capitalize">{t(`profile.${healthOverview.profile.gender}`) || healthOverview.profile.gender}</span>
                                            )}
                                            {healthOverview.profile?.blood_type && (
                                                <span className="flex items-center gap-1 px-2 py-0.5 bg-rose-50 text-rose-600 rounded-full text-xs font-semibold">
                                                    <Droplets size={10} />
                                                    {healthOverview.profile.blood_type}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Tracking Timeline */}
                                <div className="p-3 bg-slate-50 rounded-xl space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-slate-500 flex items-center gap-1.5">
                                            <Clock size={14} />
                                            {t('dashboard.trackingSince') || 'Tracking since'}
                                        </span>
                                        <span className="font-medium text-slate-700">
                                            {healthOverview.timeline?.first_record_date
                                                ? new Date(healthOverview.timeline.first_record_date).toLocaleDateString()
                                                : '-'}
                                        </span>
                                    </div>
                                    {healthOverview.timeline?.tracking_duration && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-slate-500">{t('dashboard.duration') || 'Duration'}</span>
                                            <span className="font-medium text-primary-600">{healthOverview.timeline.tracking_duration}</span>
                                        </div>
                                    )}
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-slate-500">{t('dashboard.totalRecords') || 'Total records'}</span>
                                        <span className="font-medium text-slate-700">{healthOverview.timeline?.total_documents || 0}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Health Status */}
                            <div className="space-y-3">
                                <h4 className="text-sm font-semibold text-slate-600 uppercase tracking-wider">
                                    {t('dashboard.healthStatus') || 'Health Status'}
                                </h4>

                                {/* Analysis Status */}
                                {healthOverview.health_status?.has_analysis ? (
                                    <div className="p-3 bg-teal-50 border border-teal-100 rounded-xl">
                                        <div className="flex items-center gap-2 mb-1">
                                            <CheckCircle2 size={16} className="text-teal-600" />
                                            <span className="font-medium text-teal-800">{t('dashboard.analysisComplete') || 'Analysis Complete'}</span>
                                        </div>
                                        <p className="text-xs text-teal-600">
                                            {t('dashboard.lastAnalysis') || 'Last analysis'}:{' '}
                                            {healthOverview.health_status.last_analysis_date
                                                ? new Date(healthOverview.health_status.last_analysis_date).toLocaleDateString()
                                                : '-'}
                                            {healthOverview.health_status.days_since_analysis > 30 && (
                                                <span className="ml-2 text-amber-600">
                                                    ({healthOverview.health_status.days_since_analysis} {t('dashboard.daysAgo') || 'days ago'})
                                                </span>
                                            )}
                                        </p>
                                    </div>
                                ) : (
                                    <Link to="/health" className="block p-3 bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 transition-colors">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Sparkles size={16} className="text-amber-600" />
                                            <span className="font-medium text-amber-800">{t('dashboard.noAnalysisYet') || 'No analysis yet'}</span>
                                        </div>
                                        <p className="text-xs text-amber-600">
                                            {t('dashboard.runFirstAnalysis') || 'Run your first AI health analysis'}
                                        </p>
                                    </Link>
                                )}

                                {/* Quick Stats */}
                                <div className="grid grid-cols-2 gap-2">
                                    <div className="p-2 bg-slate-50 rounded-lg text-center">
                                        <p className="text-2xl font-bold text-slate-700">{healthOverview.health_status?.biomarkers_tracked || 0}</p>
                                        <p className="text-xs text-slate-500">{t('dashboard.biomarkersTracked') || 'Biomarkers'}</p>
                                    </div>
                                    <div className={cn(
                                        "p-2 rounded-lg text-center",
                                        healthOverview.health_status?.alerts_count > 0 ? "bg-rose-50" : "bg-teal-50"
                                    )}>
                                        <p className={cn(
                                            "text-2xl font-bold",
                                            healthOverview.health_status?.alerts_count > 0 ? "text-rose-600" : "text-teal-600"
                                        )}>
                                            {healthOverview.health_status?.alerts_count || 0}
                                        </p>
                                        <p className={cn(
                                            "text-xs",
                                            healthOverview.health_status?.alerts_count > 0 ? "text-rose-500" : "text-teal-500"
                                        )}>
                                            {t('dashboard.alertsLabel') || 'Alerts'}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Reminders & Warnings */}
                            <div className="space-y-3">
                                <h4 className="text-sm font-semibold text-slate-600 uppercase tracking-wider">
                                    {t('dashboard.reminders') || 'Reminders'}
                                </h4>

                                {/* Overdue Screenings */}
                                {healthOverview.reminders_count > 0 ? (
                                    <Link to="/screenings" className="block p-3 bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 transition-colors">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Bell size={16} className="text-amber-600" />
                                            <span className="font-medium text-amber-800">
                                                {healthOverview.reminders_count} {t('dashboard.overdueScreenings') || 'overdue screenings'}
                                            </span>
                                        </div>
                                        <div className="space-y-1">
                                            {healthOverview.reminders?.slice(0, 2).map((r, i) => (
                                                <p key={i} className="text-xs text-amber-700 truncate">
                                                    • {r.test_name}
                                                </p>
                                            ))}
                                            {healthOverview.reminders_count > 2 && (
                                                <p className="text-xs text-amber-600">
                                                    +{healthOverview.reminders_count - 2} {t('dashboard.more') || 'more'}...
                                                </p>
                                            )}
                                        </div>
                                    </Link>
                                ) : healthOverview.missing_essential_tests?.length > 0 ? (
                                    <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
                                        <div className="flex items-center gap-2 mb-2">
                                            <AlertCircle size={16} className="text-blue-600" />
                                            <span className="font-medium text-blue-800">
                                                {t('dashboard.missingTests') || 'Consider adding'}
                                            </span>
                                        </div>
                                        <div className="flex flex-wrap gap-1">
                                            {healthOverview.missing_essential_tests.map((test, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                                                    {test}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-3 bg-teal-50 border border-teal-100 rounded-xl">
                                        <div className="flex items-center gap-2">
                                            <CheckCircle2 size={16} className="text-teal-600" />
                                            <span className="font-medium text-teal-800">
                                                {t('dashboard.allUpToDate') || 'All up to date!'}
                                            </span>
                                        </div>
                                        <p className="text-xs text-teal-600 mt-1">
                                            {t('dashboard.noOverdueScreenings') || 'No overdue screenings'}
                                        </p>
                                    </div>
                                )}

                                {/* Analysis reminder if old */}
                                {healthOverview.health_status?.has_analysis && healthOverview.health_status?.days_since_analysis > 90 && (
                                    <Link to="/health" className="block p-3 bg-violet-50 border border-violet-200 rounded-xl hover:bg-violet-100 transition-colors">
                                        <div className="flex items-center gap-2">
                                            <Brain size={16} className="text-violet-600" />
                                            <span className="text-sm font-medium text-violet-800">
                                                {t('dashboard.rerunAnalysis') || 'Time for a new analysis'}
                                            </span>
                                        </div>
                                        <p className="text-xs text-violet-600 mt-1">
                                            {t('dashboard.lastAnalysisWas') || 'Your last analysis was'} {healthOverview.health_status.days_since_analysis} {t('dashboard.daysAgo') || 'days ago'}
                                        </p>
                                    </Link>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
