import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { Building, Link as LinkIcon, RefreshCw, CheckCircle, AlertCircle, Shield, Loader2, Save } from 'lucide-react';
import { cn } from '../lib/utils';

const ProviderCard = ({ name, logoColor, isLinked, username, onLink, onSync, linking, syncing }) => {
    const [creds, setCreds] = useState({ username: '', password: '' });
    const [showForm, setShowForm] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        onLink(name, creds);
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
                                        <CheckCircle size={12} /> Connected
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-500 border border-slate-200">
                                        Not Connected
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {isLinked ? (
                    <div>
                        <div className="flex items-center gap-2 text-sm text-slate-600 mb-6 bg-slate-50 p-3 rounded-lg border border-slate-100">
                            <Shield size={16} className="text-teal-500" />
                            <span>Linked as <strong>{username}</strong></span>
                        </div>

                        <button
                            onClick={() => onSync(name)}
                            disabled={syncing}
                            className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-all shadow-md shadow-primary-500/20 active:scale-95 flex items-center justify-center gap-2"
                        >
                            {syncing ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
                            {syncing ? 'Syncing Documents...' : 'Sync Now'}
                        </button>
                        <p className="text-xs text-center text-slate-400 mt-2">This may take a few minutes.</p>
                    </div>
                ) : (
                    <div>
                        {!showForm ? (
                            <button
                                onClick={() => setShowForm(true)}
                                className="w-full py-2.5 bg-slate-900 text-white rounded-xl font-medium hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
                            >
                                <LinkIcon size={18} />
                                Connect Account
                            </button>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-4 animate-in slide-in-from-top-2">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Username / CNP</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                        value={creds.username}
                                        onChange={(e) => setCreds({ ...creds, username: e.target.value })}
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Password</label>
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
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={linking}
                                        className="flex-1 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center justify-center gap-2"
                                    >
                                        {linking ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                                        Save
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
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [linking, setLinking] = useState(null); // 'Regina Maria' or 'Synevo'
    const [syncing, setSyncing] = useState(null);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchAccounts();
    }, []);

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
            setMessage({ type: 'success', text: `Successfully linked ${provider}!` });
            fetchAccounts();
        } catch (e) {
            setMessage({ type: 'error', text: `Failed to link: ${e.response?.data?.detail || e.message}` });
        } finally {
            setLinking(null);
        }
    };

    const handleSync = async (provider) => {
        setSyncing(provider);
        setMessage({ type: 'info', text: `Starting sync for ${provider}. This may take a few minutes...` });
        try {
            const res = await api.post(`/users/sync/${provider}`);
            if (res.data.status === 'success') {
                setMessage({ type: 'success', text: res.data.message });
            } else {
                setMessage({ type: 'error', text: res.data.message });
            }
        } catch (e) {
            setMessage({ type: 'error', text: `Sync failed: ${e.response?.data?.detail || e.message}` });
        } finally {
            setSyncing(null);
        }
    };

    return (
        <div>
            <div className="mb-8">
                <p className="text-slate-500">Connect your medical providers to automatically import analysis history.</p>
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
                />
            </div>
        </div>
    );
};

export default LinkedAccounts;
