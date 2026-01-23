import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
    Shield, Users, FileText, Activity, Server, Cpu, HardDrive,
    MemoryStick, RefreshCw, AlertTriangle, CheckCircle, Loader2,
    Trash2, RotateCcw, UserCog, Play, Brain, Power, ScrollText,
    Clock, XCircle, ChevronDown, ChevronUp
} from 'lucide-react';
import { cn } from '../lib/utils';

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
            const [statsRes, serverRes, usersRes, jobsRes, serviceRes] = await Promise.all([
                api.get('/admin/stats'),
                api.get('/admin/server'),
                api.get('/admin/users'),
                api.get('/admin/sync-jobs?limit=20'),
                api.get('/admin/service-status')
            ]);
            setStats(statsRes.data);
            setServerStats(serverRes.data);
            setUsers(usersRes.data);
            setSyncJobs(jobsRes.data);
            setServiceStatus(serviceRes.data);
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
                        Regenerate AI Reports (Romanian)
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
                                <th className="px-4 py-3 text-left">Provider</th>
                                <th className="px-4 py-3 text-center">Status</th>
                                <th className="px-4 py-3 text-center">Docs Found</th>
                                <th className="px-4 py-3 text-center">Processed</th>
                                <th className="px-4 py-3 text-left">Error</th>
                                <th className="px-4 py-3 text-right">Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {syncJobs.map(job => (
                                <tr key={job.id} className="hover:bg-slate-50">
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
                                    <td className="px-4 py-3 text-center text-sm text-slate-600">{job.documents_found}</td>
                                    <td className="px-4 py-3 text-center text-sm text-slate-600">{job.documents_processed}</td>
                                    <td className="px-4 py-3 text-sm text-rose-600 truncate max-w-xs">{job.error_message || '-'}</td>
                                    <td className="px-4 py-3 text-right text-xs text-slate-400">
                                        {job.created_at ? new Date(job.created_at).toLocaleString() : '-'}
                                    </td>
                                </tr>
                            ))}
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
        </div>
    );
};

export default Admin;
