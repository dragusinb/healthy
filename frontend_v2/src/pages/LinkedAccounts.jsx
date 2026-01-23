import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Building, Link as LinkIcon, RefreshCw, CheckCircle, AlertCircle, Shield, Loader2, Save, Pencil } from 'lucide-react';
import { cn } from '../lib/utils';

const ProviderCard = ({ name, logoColor, isLinked, username, onLink, onSync, linking, syncing, syncStatus, t }) => {
    const [creds, setCreds] = useState({ username: '', password: '' });
    const [showForm, setShowForm] = useState(false);
    const [isEditing, setIsEditing] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        onLink(name, creds);
    };

    const getStatusDisplay = () => {
        if (!syncStatus) return null;
        const { stage, message, progress, total } = syncStatus;

        const stageKey = `linkedAccounts.syncStages.${stage}`;
        const stageLabel = t(stageKey) !== stageKey ? t(stageKey) : stage;

        const isCaptcha = stage === 'captcha';

        return (
            <div className={cn(
                "mt-3 p-3 rounded-lg border",
                isCaptcha ? "bg-amber-50 border-amber-200" : "bg-blue-50 border-blue-100"
            )}>
                <div className={cn(
                    "flex items-center gap-2 text-sm",
                    isCaptcha ? "text-amber-700" : "text-blue-700"
                )}>
                    <Loader2 size={14} className="animate-spin" />
                    <span className="font-medium">{stageLabel}</span>
                </div>
                <p className={cn("text-xs mt-1", isCaptcha ? "text-amber-600" : "text-blue-600")}>{message}</p>
                {progress > 0 && total > 0 && (
                    <div className="mt-2">
                        <div className="h-1.5 bg-blue-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-600 transition-all duration-300"
                                style={{ width: `${(progress / total) * 100}%` }}
                            />
                        </div>
                        <p className="text-xs text-blue-500 mt-1">{progress} / {total}</p>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-4">
                        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-md", logoColor)}>
                            <Building size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-slate-900">{name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                                {isLinked ? (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-100">
                                        <CheckCircle size={12} /> {t('linkedAccounts.connected')}
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-500 border border-slate-200">
                                        {t('linkedAccounts.notConnected')}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {isLinked ? (
                    <div>
                        {!isEditing ? (
                            <>
                                <div className="flex items-center justify-between text-sm text-slate-600 mb-6 bg-slate-50 p-3 rounded-lg border border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <Shield size={16} className="text-teal-500" />
                                        <span>{t('linkedAccounts.linkedAs')} <strong>{username}</strong></span>
                                    </div>
                                    <button
                                        onClick={() => {
                                            setCreds({ username: username, password: '' });
                                            setIsEditing(true);
                                        }}
                                        className="p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                                        title={t('linkedAccounts.editCredentials')}
                                    >
                                        <Pencil size={14} />
                                    </button>
                                </div>

                                <button
                                    onClick={() => onSync(name)}
                                    disabled={syncing}
                                    className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-all shadow-md shadow-primary-500/20 active:scale-95 flex items-center justify-center gap-2"
                                >
                                    {syncing ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
                                    {syncing ? t('linkedAccounts.syncing') : t('linkedAccounts.syncNow')}
                                </button>
                                {syncing && getStatusDisplay()}
                                {!syncing && <p className="text-xs text-center text-slate-400 mt-2">{t('linkedAccounts.clickToSync')}</p>}
                            </>
                        ) : (
                            <form onSubmit={(e) => { e.preventDefault(); onLink(name, creds); setIsEditing(false); }} className="space-y-4 animate-in slide-in-from-top-2">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{t('linkedAccounts.username')}</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                        value={creds.username}
                                        onChange={(e) => setCreds({ ...creds, username: e.target.value })}
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{t('linkedAccounts.newPassword')}</label>
                                    <input
                                        type="password"
                                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                        value={creds.password}
                                        onChange={(e) => setCreds({ ...creds, password: e.target.value })}
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setIsEditing(false)}
                                        className="flex-1 py-2 text-slate-500 font-medium hover:bg-slate-50 rounded-lg transition-colors"
                                        disabled={linking}
                                    >
                                        {t('common.cancel')}
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={linking}
                                        className="flex-1 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center justify-center gap-2"
                                    >
                                        {linking ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                                        {t('linkedAccounts.update')}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                ) : (
                    <div>
                        {!showForm ? (
                            <button
                                onClick={() => setShowForm(true)}
                                className="w-full py-2.5 bg-slate-900 text-white rounded-xl font-medium hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
                            >
                                <LinkIcon size={18} />
                                {t('linkedAccounts.connectAccount')}
                            </button>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4 animate-in slide-in-from-top-2">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{t('linkedAccounts.username')}</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                        value={creds.username}
                                        onChange={(e) => setCreds({ ...creds, username: e.target.value })}
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">{t('linkedAccounts.password')}</label>
                                    <input
                                        type="password"
                                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                        value={creds.password}
                                        onChange={(e) => setCreds({ ...creds, password: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowForm(false)}
                                        className="flex-1 py-2 text-slate-500 font-medium hover:bg-slate-50 rounded-lg transition-colors"
                                        disabled={linking}
                                    >
                                        {t('common.cancel')}
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={linking}
                                        className="flex-1 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center justify-center gap-2"
                                    >
                                        {linking ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                                        {t('common.save')}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const LinkedAccounts = () => {
    const { t } = useTranslation();
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [linking, setLinking] = useState(null);
    const [syncing, setSyncing] = useState(null);
    const [message, setMessage] = useState(null);
    const [syncStatus, setSyncStatus] = useState({});
    const syncingRef = useRef(null);

    useEffect(() => {
        fetchAccounts();
    }, []);

    useEffect(() => {
        syncingRef.current = syncing;
    }, [syncing]);

    useEffect(() => {
        if (!syncing) return;

        const currentProvider = syncing;

        const pollStatus = async () => {
            if (syncingRef.current !== currentProvider) return;

            try {
                const res = await api.get(`/users/sync-status/${currentProvider}`);

                if (syncingRef.current !== currentProvider) return;

                setSyncStatus(prev => ({ ...prev, [currentProvider]: res.data }));

                if (res.data.is_complete) {
                    if (res.data.is_error) {
                        setMessage({ type: 'error', text: res.data.message });
                    } else {
                        setMessage({ type: 'success', text: res.data.message });
                    }
                    setSyncing(null);
                    setTimeout(() => {
                        setSyncStatus(prev => ({ ...prev, [currentProvider]: null }));
                    }, 2000);
                }
            } catch (e) {
                console.error("Status poll failed", e);
            }
        };

        pollStatus();
        const interval = setInterval(pollStatus, 1500);
        return () => clearInterval(interval);
    }, [syncing]);

    const fetchAccounts = async () => {
        try {
            const res = await api.get('/users/me');
            setAccounts(res.data.linked_accounts || []);
        } catch (e) {
            console.error("Failed", e);
        } finally {
            setLoading(false);
        }
    };

    const isLinked = (provider) => {
        const acc = accounts.find(a => a.provider_name === provider);
        return acc ? acc.username : null;
    };

    const handleLink = async (provider, creds) => {
        setLinking(provider);
        setMessage(null);
        try {
            await api.post('/users/link-account', {
                provider_name: provider,
                username: creds.username,
                password: creds.password
            });
            setMessage({ type: 'success', text: `${t('common.success')}: ${provider}` });
            fetchAccounts();
        } catch (e) {
            setMessage({ type: 'error', text: `${t('common.error')}: ${e.response?.data?.detail || e.message}` });
        } finally {
            setLinking(null);
        }
    };

    const handleSync = async (provider) => {
        setSyncing(provider);
        setMessage(null);
        setSyncStatus(prev => ({ ...prev, [provider]: { stage: 'starting', message: t('linkedAccounts.syncStages.starting') } }));
        try {
            const res = await api.post(`/users/sync/${provider}`);
            if (res.data.status === 'in_progress') {
                setMessage({ type: 'info', text: t('linkedAccounts.syncing') });
            }
        } catch (e) {
            setMessage({ type: 'error', text: `${t('common.error')}: ${e.response?.data?.detail || e.message}` });
            setSyncing(null);
            setSyncStatus(prev => ({ ...prev, [provider]: null }));
        }
    };

    return (
        <div>
            <div className="mb-8">
                <p className="text-slate-500">{t('linkedAccounts.subtitle')}</p>
            </div>

            {message && (
                <div className={cn(
                    "mb-6 p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2 border",
                    message.type === 'error' ? "bg-rose-50 border-rose-100 text-rose-700" :
                        message.type === 'success' ? "bg-teal-50 border-teal-100 text-teal-700" :
                            "bg-blue-50 border-blue-100 text-blue-700"
                )}>
                    {message.type === 'error' ? <AlertCircle size={20} /> : message.type === 'success' ? <CheckCircle size={20} /> : <Loader2 size={20} className="animate-spin" />}
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
                <ProviderCard
                    name="Regina Maria"
                    logoColor="bg-purple-600"
                    isLinked={!!isLinked('Regina Maria')}
                    username={isLinked('Regina Maria')}
                    onLink={handleLink}
                    onSync={handleSync}
                    linking={linking === 'Regina Maria'}
                    syncing={syncing === 'Regina Maria'}
                    syncStatus={syncStatus['Regina Maria']}
                    t={t}
                />
                <ProviderCard
                    name="Synevo"
                    logoColor="bg-orange-500"
                    isLinked={!!isLinked('Synevo')}
                    username={isLinked('Synevo')}
                    onLink={handleLink}
                    onSync={handleSync}
                    linking={linking === 'Synevo'}
                    syncing={syncing === 'Synevo'}
                    syncStatus={syncStatus['Synevo']}
                    t={t}
                />
            </div>
        </div>
    );
};

export default LinkedAccounts;
