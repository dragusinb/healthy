import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
    Shield, Users, FileText, Activity, Server, Cpu, HardDrive,
    MemoryStick, RefreshCw, AlertTriangle, CheckCircle, Loader2,
    Trash2, RotateCcw, UserCog, Play, Brain, Power, ScrollText,
    Clock, XCircle, ChevronDown, ChevronUp, UserSearch, Calendar,
    Zap, X, KeyRound, Wifi, Timer, Bug, Download, User
} from 'lucide-react';
import { cn } from '../lib/utils';

// Error category icons
const ERROR_ICONS = {
    auth: KeyRound,
    captcha: AlertTriangle,
    timeout: Timer,
    network: Wifi,
    site_down: Power,
    session: Clock,
    rate_limit: Zap,
    scraping: Bug,
    download: Download,
    unknown: XCircle
};

// Error Modal Component
const ErrorModal = ({ job, onClose }) => {
    if (!job) return null;

    const Icon = ERROR_ICONS[job.error_category] || XCircle;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
                <div className="p-6 border-b border-slate-100">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-rose-100 text-rose-600 rounded-lg">
                                <Icon size={20} />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-slate-800">Sync Error Details</h2>
                                <p className="text-sm text-slate-500">{job.provider_name} - {job.user_email}</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
                            <X size={20} className="text-slate-400" />
                        </button>
                    </div>
                </div>
                <div className="p-6 space-y-4 overflow-y-auto max-h-[60vh]">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="bg-slate-50 p-3 rounded-lg">
                            <span className="text-slate-500">Status</span>
                            <p className="font-medium text-slate-800">{job.status}</p>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-lg">
                            <span className="text-slate-500">Time</span>
                            <p className="font-medium text-slate-800">{job.created_at ? new Date(job.created_at).toLocaleString() : '-'}</p>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-lg">
                            <span className="text-slate-500">Docs Found</span>
                            <p className="font-medium text-slate-800">{job.documents_found}</p>
                        </div>
                        <div className="bg-slate-50 p-3 rounded-lg">
                            <span className="text-slate-500">Docs Processed</span>
                            <p className="font-medium text-slate-800">{job.documents_processed}</p>
                        </div>
                    </div>

                    {job.error_summary && (
                        <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
                            <h4 className="font-semibold text-amber-800 mb-1">Error Summary</h4>
                            <p className="text-amber-700">{job.error_summary}</p>
                        </div>
                    )}

                    {job.error_message && (
                        <div className="bg-rose-50 border border-rose-200 p-4 rounded-lg">
                            <h4 className="font-semibold text-rose-800 mb-2">Full Error Message</h4>
                            <pre className="text-xs text-rose-700 whitespace-pre-wrap font-mono bg-rose-100 p-3 rounded overflow-x-auto">
                                {job.error_message}
                            </pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Schedule Visual Component
const ScheduleVisual = ({ history, nextRuns }) => {
    // Generate last 14 days
    const days = [];
    for (let i = 13; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        const dayData = history?.find(h => h.date === dateStr);
        days.push({
            date: dateStr,
            dayName: date.toLocaleDateString('en', { weekday: 'short' }),
            dayNum: date.getDate(),
            ...dayData
        });
    }

    // Add future days for next runs
    const futureDays = [];
    for (let i = 1; i <= 3; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        const hasScheduled = nextRuns?.some(run => run.next_run?.startsWith(dateStr));
        futureDays.push({
            date: dateStr,
            dayName: date.toLocaleDateString('en', { weekday: 'short' }),
            dayNum: date.getDate(),
            isFuture: true,
            hasScheduled
        });
    }

    const getBoxColor = (day) => {
        if (day.isFuture) {
            return day.hasScheduled ? "bg-blue-100 border-blue-300" : "bg-slate-50 border-slate-200";
        }
        if (!day.total) return "bg-slate-50 border-slate-200";
        if (day.failed > 0 && day.completed === 0) return "bg-rose-100 border-rose-300";
        if (day.failed > 0) return "bg-amber-100 border-amber-300";
        return "bg-teal-100 border-teal-300";
    };

    const getBoxTooltip = (day) => {
        if (day.isFuture) return day.hasScheduled ? "Scheduled" : "No runs scheduled";
        if (!day.total) return "No runs";
        return `${day.completed} completed, ${day.failed} failed`;
    };

    return (
        <div className="card p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Calendar size={20} />
                Sync Schedule (Last 14 Days + Next 3)
            </h2>
            <div className="flex gap-1 flex-wrap">
                {[...days, ...futureDays].map((day, idx) => (
                    <div key={day.date} className="flex flex-col items-center">
                        <span className="text-[10px] text-slate-400 mb-1">{day.dayName}</span>
                        <div
                            className={cn(
                                "w-10 h-10 rounded-lg border-2 flex items-center justify-center text-xs font-medium transition-all cursor-default",
                                getBoxColor(day),
                                day.isFuture && "border-dashed"
                            )}
                            title={getBoxTooltip(day)}
                        >
                            {day.isFuture ? (
                                day.hasScheduled ? <Clock size={14} className="text-blue-500" /> : <span className="text-slate-300">{day.dayNum}</span>
                            ) : (
                                day.total ? (
                                    <span className={cn(
                                        day.failed > 0 && day.completed === 0 ? "text-rose-700" :
                                            day.failed > 0 ? "text-amber-700" : "text-teal-700"
                                    )}>{day.total}</span>
                                ) : <span className="text-slate-300">{day.dayNum}</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
            <div className="flex gap-4 mt-4 text-xs text-slate-500">
                <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded bg-teal-100 border border-teal-300"></div>
                    All successful
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded bg-amber-100 border border-amber-300"></div>
                    Some errors
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded bg-rose-100 border border-rose-300"></div>
                    All failed
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded bg-blue-100 border border-blue-300 border-dashed"></div>
                    Scheduled
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon: Icon, label, value, subValue, color = "primary" }) => {
    const colors = {
        primary: "bg-primary-50 text-primary-600 border-primary-100",
        teal: "bg-teal-50 text-teal-600 border-teal-100",
        amber: "bg-amber-50 text-amber-600 border-amber-100",
        rose: "bg-rose-50 text-rose-600 border-rose-100",
        violet: "bg-violet-50 text-violet-600 border-violet-100",
    };

    return (
        <div className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
            <div className="flex items-center gap-3">
                <div className={cn("p-2 rounded-lg border", colors[color])}>
                    <Icon size={20} />
                </div>
                <div>
                    <p className="text-sm text-slate-500">{label}</p>
                    <p className="text-2xl font-bold text-slate-800">{value}</p>
                    {subValue && <p className="text-xs text-slate-400">{subValue}</p>}
                </div>
            </div>
        </div>
    );
};

const ServerGauge = ({ label, percent, used, total, color = "primary" }) => {
    const colors = {
        primary: "bg-primary-500",
        teal: "bg-teal-500",
        amber: "bg-amber-500",
        rose: "bg-rose-500",
    };

    const getColor = () => {
        if (percent > 90) return "bg-rose-500";
        if (percent > 70) return "bg-amber-500";
        return colors[color];
    };

    return (
        <div className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
            <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-700">{label}</span>
                <span className="text-sm font-bold text-slate-800">{percent}%</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                    className={cn("h-full rounded-full transition-all", getColor())}
                    style={{ width: `${percent}%` }}
                />
            </div>
            <p className="text-xs text-slate-400 mt-1">{used} / {total}</p>
        </div>
    );
};

const Admin = () => {
    const { t } = useTranslation();
    const [stats, setStats] = useState(null);
    const [serverStats, setServerStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [syncJobs, setSyncJobs] = useState([]);
    const [serviceStatus, setServiceStatus] = useState(null);
    const [serverLogs, setServerLogs] = useState(null);
    const [showLogs, setShowLogs] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(null);
    const [selectedJob, setSelectedJob] = useState(null); // For error modal
    const [syncHistory, setSyncHistory] = useState(null);
    const [schedulerStatus, setSchedulerStatus] = useState(null);

    useEffect(() => {
        fetchData();
        // Auto-refresh service status every 30 seconds
        const interval = setInterval(fetchServiceStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchServiceStatus = async () => {
        try {
            const res = await api.get('/admin/service-status');
            setServiceStatus(res.data);
        } catch (e) {
            console.error("Failed to fetch service status", e);
        }
    };

    const fetchServerLogs = async () => {
        try {
            const res = await api.get('/admin/server-logs?lines=100');
            setServerLogs(res.data);
        } catch (e) {
            console.error("Failed to fetch logs", e);
        }
    };

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [statsRes, serverRes, usersRes, jobsRes, serviceRes, historyRes, schedulerRes] = await Promise.all([
                api.get('/admin/stats'),
                api.get('/admin/server'),
                api.get('/admin/users'),
                api.get('/admin/sync-jobs?limit=20'),
                api.get('/admin/service-status'),
                api.get('/admin/sync-history?days=14'),
                api.get('/admin/scheduler-status')
            ]);
            setStats(statsRes.data);
            setServerStats(serverRes.data);
            setUsers(usersRes.data);
            setSyncJobs(jobsRes.data);
            setServiceStatus(serviceRes.data);
            setSyncHistory(historyRes.data);
            setSchedulerStatus(schedulerRes.data);
        } catch (e) {
            console.error("Failed to fetch admin data", e);
            if (e.response?.status === 403) {
                setError(t('admin.accessDenied') || "Admin access required");
            } else {
                setError(e.response?.data?.detail || "Failed to load admin data");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleCleanupLimbo = async () => {
        setActionLoading('cleanup');
        try {
            const res = await api.post('/admin/cleanup-limbo-documents');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Cleanup failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleRetryFailed = async () => {
        setActionLoading('retry');
        try {
            const res = await api.post('/admin/retry-failed-syncs');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Retry failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleReprocessDocuments = async () => {
        setActionLoading('reprocess');
        try {
            const res = await api.post('/admin/reprocess-documents');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Reprocess failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleRegenerateReports = async () => {
        setActionLoading('regenerate');
        try {
            const res = await api.post('/admin/regenerate-health-reports');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Regeneration failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleScanProfiles = async () => {
        setActionLoading('scanprofiles');
        try {
            const res = await api.post('/admin/scan-profiles');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Profile scan failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleTriggerSync = async () => {
        setActionLoading('triggersync');
        try {
            const res = await api.post('/admin/trigger-sync-job?job_type=provider_sync');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Trigger failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleTriggerDocProcessing = async () => {
        setActionLoading('triggerdocs');
        try {
            const res = await api.post('/admin/trigger-sync-job?job_type=document_processing');
            alert(res.data.message);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Trigger failed");
        } finally {
            setActionLoading(null);
        }
    };

    const handleRestartServer = async () => {
        if (!confirm("Are you sure you want to restart the server? This will briefly disconnect all users.")) {
            return;
        }
        setActionLoading('restart');
        try {
            const res = await api.post('/admin/restart-server');
            alert(res.data.message);
            // Wait a bit then refresh status
            setTimeout(() => {
                fetchServiceStatus();
                setActionLoading(null);
            }, 5000);
        } catch (e) {
            alert(e.response?.data?.detail || "Restart failed");
            setActionLoading(null);
        }
    };

    const handleViewLogs = async () => {
        setShowLogs(!showLogs);
        if (!showLogs) {
            await fetchServerLogs();
        }
    };

    const handleToggleAdmin = async (userId, isAdmin) => {
        try {
            await api.post(`/admin/users/${userId}/set-admin?is_admin=${!isAdmin}`);
            fetchData();
        } catch (e) {
            alert(e.response?.data?.detail || "Failed to update user");
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-primary-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-xl flex items-center gap-3">
                <AlertTriangle size={24} />
                <div>
                    <h3 className="font-semibold">{t('common.error')}</h3>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-violet-100 text-violet-600 rounded-xl">
                        <Shield size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800">{t('admin.title')}</h1>
                        <p className="text-slate-500">{t('admin.systemStats')}</p>
                    </div>
                </div>
                <button
                    onClick={fetchData}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* System Stats */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    <StatCard
                        icon={Users}
                        label={t('admin.totalUsers')}
                        value={stats.users.total}
                        subValue={`+${stats.users.new_24h} (24h)`}
                        color="primary"
                    />
                    <StatCard
                        icon={FileText}
                        label={t('admin.totalDocuments')}
                        value={stats.documents.total}
                        subValue={`${stats.documents.pending} ${t('admin.pendingDocs')}`}
                        color="teal"
                    />
                    <StatCard
                        icon={Activity}
                        label={t('admin.totalBiomarkers')}
                        value={stats.biomarkers.total}
                        subValue={`${stats.biomarkers.abnormal} ${t('admin.abnormal')}`}
                        color="amber"
                    />
                    <StatCard
                        icon={Server}
                        label={t('admin.linkedAccounts')}
                        value={stats.linked_accounts.total}
                        subValue={`${stats.linked_accounts.error} ${t('admin.errorAccounts')}`}
                        color="violet"
                    />
                    <StatCard
                        icon={RefreshCw}
                        label={t('admin.syncJobs')}
                        value={stats.syncs.last_24h}
                        subValue={`${stats.syncs.failed_24h} ${t('admin.failed24h')}`}
                        color="primary"
                    />
                    <StatCard
                        icon={FileText}
                        label="Health Reports"
                        value={stats.health_reports.total}
                        color="teal"
                    />
                </div>
            )}

            {/* Server Resources */}
            {serverStats && (
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                        <Server size={20} />
                        {t('admin.serverStats')}
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ServerGauge
                            label={`${t('admin.cpu')} (${serverStats.cpu.cores} cores)`}
                            percent={serverStats.cpu.percent}
                            used={`${serverStats.cpu.percent}%`}
                            total={`Load: ${serverStats.cpu.load_avg_1m.toFixed(2)}`}
                            color="primary"
                        />
                        <ServerGauge
                            label={t('admin.memory')}
                            percent={serverStats.memory.percent}
                            used={`${serverStats.memory.used_gb} GB`}
                            total={`${serverStats.memory.total_gb} GB`}
                            color="teal"
                        />
                        <ServerGauge
                            label={t('admin.disk')}
                            percent={serverStats.disk.percent}
                            used={`${serverStats.disk.used_gb} GB`}
                            total={`${serverStats.disk.total_gb} GB`}
                            color="amber"
                        />
                    </div>
                </div>
            )}

            {/* Service Status */}
            {serviceStatus && (
                <div className="card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                            <Power size={20} />
                            Service Status
                        </h2>
                        <div className="flex items-center gap-2">
                            <span className={cn(
                                "px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1.5",
                                serviceStatus.is_active ? "bg-teal-100 text-teal-700" :
                                serviceStatus.is_failed ? "bg-rose-100 text-rose-700" :
                                "bg-amber-100 text-amber-700"
                            )}>
                                {serviceStatus.is_active ? <CheckCircle size={14} /> :
                                 serviceStatus.is_failed ? <XCircle size={14} /> :
                                 <AlertTriangle size={14} />}
                                {serviceStatus.is_active ? "Running" : serviceStatus.is_failed ? "Failed" : "Unknown"}
                            </span>
                            <button
                                onClick={handleRestartServer}
                                disabled={actionLoading === 'restart'}
                                className="flex items-center gap-1.5 px-3 py-1 bg-rose-100 text-rose-700 hover:bg-rose-200 rounded-lg text-sm transition-colors disabled:opacity-50"
                            >
                                {actionLoading === 'restart' ? <Loader2 size={14} className="animate-spin" /> : <Power size={14} />}
                                Restart
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                            <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                                <Clock size={14} />
                                Uptime
                            </div>
                            <p className="font-medium text-slate-800">{serviceStatus.uptime || "Unknown"}</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                            <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                                <MemoryStick size={14} />
                                Memory
                            </div>
                            <p className="font-medium text-slate-800">{serviceStatus.memory || "Unknown"}</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                            <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                                <Activity size={14} />
                                Recent Events
                            </div>
                            <p className="font-medium text-slate-800">{serviceStatus.recent_events?.length || 0} events</p>
                        </div>
                    </div>

                    {/* Recent Events */}
                    {serviceStatus.recent_events && serviceStatus.recent_events.length > 0 && (
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-slate-600 mb-2">Recent Restart Events</h3>
                            <div className="bg-slate-900 rounded-lg p-3 max-h-32 overflow-y-auto">
                                {serviceStatus.recent_events.map((event, i) => (
                                    <div key={i} className={cn(
                                        "text-xs font-mono",
                                        event.toLowerCase().includes('failed') || event.toLowerCase().includes('error') ? "text-rose-400" :
                                        event.includes('Started') ? "text-teal-400" :
                                        event.includes('Stopped') ? "text-amber-400" :
                                        "text-slate-400"
                                    )}>
                                        {event}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* View Logs Button */}
                    <button
                        onClick={handleViewLogs}
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800"
                    >
                        <ScrollText size={16} />
                        {showLogs ? "Hide Logs" : "View Server Logs"}
                        {showLogs ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>

                    {/* Server Logs */}
                    {showLogs && serverLogs && (
                        <div className="mt-4 space-y-3">
                            {serverLogs.errors && serverLogs.errors.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-semibold text-rose-600 mb-2">Recent Errors ({serverLogs.errors.length})</h4>
                                    <div className="bg-rose-950 rounded-lg p-3 max-h-40 overflow-y-auto">
                                        {serverLogs.errors.map((line, i) => (
                                            <div key={i} className="text-xs font-mono text-rose-300 break-all">{line}</div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div>
                                <h4 className="text-sm font-semibold text-slate-600 mb-2">Recent Logs</h4>
                                <div className="bg-slate-900 rounded-lg p-3 max-h-60 overflow-y-auto">
                                    {serverLogs.logs?.slice(-50).map((line, i) => (
                                        <div key={i} className={cn(
                                            "text-xs font-mono break-all",
                                            line.includes('ERROR') ? "text-rose-400" :
                                            line.includes('WARNING') ? "text-amber-400" :
                                            line.includes('INFO') ? "text-slate-400" :
                                            "text-slate-500"
                                        )}>
                                            {line}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Schedule Visual */}
            {syncHistory && (
                <ScheduleVisual history={syncHistory.history} nextRuns={syncHistory.next_runs} />
            )}

            {/* Scheduler Info */}
            {schedulerStatus && schedulerStatus.status === 'running' && (
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                        <Zap size={20} />
                        Scheduler Jobs
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                        {schedulerStatus.jobs.map(job => (
                            <div key={job.id} className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                <p className="font-medium text-slate-800 text-sm">{job.name}</p>
                                <p className="text-xs text-slate-500 mt-1">{job.trigger}</p>
                                {job.next_run && (
                                    <p className="text-xs text-primary-600 mt-1 flex items-center gap-1">
                                        <Clock size={12} />
                                        Next: {new Date(job.next_run).toLocaleString()}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <button
                            onClick={handleTriggerSync}
                            disabled={actionLoading === 'triggersync'}
                            className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg text-sm transition-colors disabled:opacity-50"
                        >
                            {actionLoading === 'triggersync' ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                            Run Provider Sync Now
                        </button>
                        <button
                            onClick={handleTriggerDocProcessing}
                            disabled={actionLoading === 'triggerdocs'}
                            className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg text-sm transition-colors disabled:opacity-50"
                        >
                            {actionLoading === 'triggerdocs' ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
                            Run Document Processing Now
                        </button>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="card p-6">
                <h2 className="text-lg font-semibold text-slate-800 mb-4">Admin Actions</h2>
                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={handleCleanupLimbo}
                        disabled={actionLoading === 'cleanup'}
                        className="flex items-center gap-2 px-4 py-2 bg-amber-100 text-amber-700 hover:bg-amber-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {actionLoading === 'cleanup' ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                        {t('admin.cleanupLimbo')}
                    </button>
                    <button
                        onClick={handleRetryFailed}
                        disabled={actionLoading === 'retry'}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 hover:bg-primary-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {actionLoading === 'retry' ? <Loader2 size={16} className="animate-spin" /> : <RotateCcw size={16} />}
                        {t('admin.retryFailed')}
                    </button>
                    <button
                        onClick={handleReprocessDocuments}
                        disabled={actionLoading === 'reprocess'}
                        className="flex items-center gap-2 px-4 py-2 bg-teal-100 text-teal-700 hover:bg-teal-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {actionLoading === 'reprocess' ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                        Reprocess Documents ({stats?.documents?.pending || 0})
                    </button>
                    <button
                        onClick={handleRegenerateReports}
                        disabled={actionLoading === 'regenerate'}
                        className="flex items-center gap-2 px-4 py-2 bg-violet-100 text-violet-700 hover:bg-violet-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {actionLoading === 'regenerate' ? <Loader2 size={16} className="animate-spin" /> : <Brain size={16} />}
                        Regenerate AI Reports
                    </button>
                    <button
                        onClick={handleScanProfiles}
                        disabled={actionLoading === 'scanprofiles'}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-700 hover:bg-indigo-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {actionLoading === 'scanprofiles' ? <Loader2 size={16} className="animate-spin" /> : <UserSearch size={16} />}
                        Scan Documents for Profiles
                    </button>
                </div>
            </div>

            {/* Users Table */}
            <div className="card overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                    <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                        <Users size={20} />
                        {t('admin.userManagement')}
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                            <tr>
                                <th className="px-4 py-3 text-left">Email</th>
                                <th className="px-4 py-3 text-center">Admin</th>
                                <th className="px-4 py-3 text-center">{t('admin.documents')}</th>
                                <th className="px-4 py-3 text-center">{t('admin.biomarkers')}</th>
                                <th className="px-4 py-3 text-center">Linked</th>
                                <th className="px-4 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {users.map(user => (
                                <tr key={user.id} className="hover:bg-slate-50">
                                    <td className="px-4 py-3 text-sm font-medium text-slate-800">{user.email}</td>
                                    <td className="px-4 py-3 text-center">
                                        {user.is_admin ? (
                                            <CheckCircle size={16} className="inline text-teal-500" />
                                        ) : (
                                            <span className="text-slate-300">-</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-center text-sm text-slate-600">{user.documents}</td>
                                    <td className="px-4 py-3 text-center text-sm text-slate-600">{user.biomarkers}</td>
                                    <td className="px-4 py-3 text-center text-sm text-slate-600">{user.linked_accounts}</td>
                                    <td className="px-4 py-3 text-right">
                                        <button
                                            onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                                            className={cn(
                                                "text-xs px-2 py-1 rounded",
                                                user.is_admin
                                                    ? "bg-rose-100 text-rose-600 hover:bg-rose-200"
                                                    : "bg-primary-100 text-primary-600 hover:bg-primary-200"
                                            )}
                                        >
                                            {user.is_admin ? t('admin.removeAdmin') : t('admin.makeAdmin')}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recent Sync Jobs */}
            <div className="card overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                    <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                        <RefreshCw size={20} />
                        Recent Sync Jobs
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                            <tr>
                                <th className="px-4 py-3 text-left">User</th>
                                <th className="px-4 py-3 text-left">Provider</th>
                                <th className="px-4 py-3 text-center">Status</th>
                                <th className="px-4 py-3 text-center">Docs</th>
                                <th className="px-4 py-3 text-left">Error</th>
                                <th className="px-4 py-3 text-right">Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {syncJobs.map(job => {
                                const ErrorIcon = ERROR_ICONS[job.error_category] || XCircle;
                                return (
                                    <tr
                                        key={job.id}
                                        className={cn(
                                            "hover:bg-slate-50 transition-colors",
                                            job.error_message && "cursor-pointer"
                                        )}
                                        onClick={() => job.error_message && setSelectedJob(job)}
                                    >
                                        <td className="px-4 py-3 text-sm text-slate-600">
                                            <div className="flex items-center gap-1.5">
                                                <User size={14} className="text-slate-400" />
                                                <span className="truncate max-w-[120px]" title={job.user_email}>
                                                    {job.user_email?.split('@')[0] || 'Unknown'}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-sm font-medium text-slate-800">{job.provider_name}</td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={cn(
                                                "text-xs px-2 py-1 rounded-full",
                                                job.status === 'completed' && "bg-teal-100 text-teal-700",
                                                job.status === 'failed' && "bg-rose-100 text-rose-700",
                                                job.status === 'running' && "bg-amber-100 text-amber-700",
                                                job.status === 'pending' && "bg-slate-100 text-slate-700"
                                            )}>
                                                {job.status}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-center text-sm text-slate-600">
                                            {job.documents_processed}/{job.documents_found}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {job.error_summary ? (
                                                <div className="flex items-center gap-1.5 text-rose-600">
                                                    <ErrorIcon size={14} />
                                                    <span className="truncate max-w-[150px]" title={job.error_summary}>
                                                        {job.error_summary}
                                                    </span>
                                                </div>
                                            ) : (
                                                <span className="text-slate-300">-</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right text-xs text-slate-400">
                                            {job.created_at ? new Date(job.created_at).toLocaleString() : '-'}
                                        </td>
                                    </tr>
                                );
                            })}
                            {syncJobs.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                                        No sync jobs yet
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Error Modal */}
            {selectedJob && (
                <ErrorModal job={selectedJob} onClose={() => setSelectedJob(null)} />
            )}
        </div>
    );
};

export default Admin;
