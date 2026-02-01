import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Lock, Unlock, AlertTriangle, Shield, Key } from 'lucide-react';
import api from '../api/client';

const VaultUnlock = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [vaultStatus, setVaultStatus] = useState(null);
    const [isInitializing, setIsInitializing] = useState(false);

    useEffect(() => {
        checkVaultStatus();
    }, []);

    const checkVaultStatus = async () => {
        try {
            const res = await api.get('/admin/vault/status');
            setVaultStatus(res.data);
            if (res.data.is_unlocked) {
                navigate('/');
            }
        } catch (e) {
            console.error('Failed to check vault status:', e);
        }
    };

    const handleUnlock = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const endpoint = vaultStatus?.is_configured
                ? '/admin/vault/unlock'
                : '/admin/vault/initialize';

            await api.post(endpoint, { master_password: password });
            navigate('/');
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to unlock vault');
        } finally {
            setLoading(false);
        }
    };

    const isInitMode = vaultStatus && !vaultStatus.is_configured;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
            <div className="max-w-md w-full">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 mb-4 shadow-lg shadow-orange-500/25">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {isInitMode ? t('vault.initialize') || 'Initialize Vault' : t('vault.unlock') || 'Unlock Vault'}
                    </h1>
                    <p className="text-slate-400">
                        {isInitMode
                            ? t('vault.initializeDescription') || 'Set up encryption to protect sensitive data'
                            : t('vault.unlockDescription') || 'Enter master password to access the system'
                        }
                    </p>
                </div>

                {/* Card */}
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 shadow-xl">
                    {/* Status indicator */}
                    <div className="flex items-center gap-3 mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                        <Lock className="w-5 h-5 text-amber-400" />
                        <div>
                            <p className="text-sm font-medium text-amber-200">
                                {t('vault.locked') || 'Vault Locked'}
                            </p>
                            <p className="text-xs text-amber-300/70">
                                {t('vault.lockedDescription') || 'Encrypted data is inaccessible'}
                            </p>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleUnlock} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {t('vault.masterPassword') || 'Master Password'}
                            </label>
                            <div className="relative">
                                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder={isInitMode
                                        ? t('vault.createPassword') || 'Create master password (min 16 chars)'
                                        : t('vault.enterPassword') || 'Enter master password'
                                    }
                                    className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                                    required
                                    minLength={16}
                                    autoFocus
                                />
                            </div>
                            {isInitMode && (
                                <p className="mt-2 text-xs text-slate-400">
                                    {t('vault.passwordRequirement') || 'Minimum 16 characters. This password cannot be recovered.'}
                                </p>
                            )}
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
                                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || password.length < 16}
                            className="w-full py-3 px-4 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-orange-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    {isInitMode ? t('vault.initializing') || 'Initializing...' : t('vault.unlocking') || 'Unlocking...'}
                                </>
                            ) : (
                                <>
                                    <Unlock className="w-5 h-5" />
                                    {isInitMode ? t('vault.initializeButton') || 'Initialize Vault' : t('vault.unlockButton') || 'Unlock Vault'}
                                </>
                            )}
                        </button>
                    </form>

                    {/* Warning */}
                    {isInitMode && (
                        <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-red-300 mb-1">
                                        {t('vault.warning') || 'Important Warning'}
                                    </p>
                                    <p className="text-xs text-red-300/70">
                                        {t('vault.warningText') || 'If you forget this password, all encrypted data will be permanently lost. There is no recovery mechanism.'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <p className="text-center text-slate-500 text-sm mt-6">
                    {t('vault.footer') || 'Vault encryption protects sensitive medical data'}
                </p>
            </div>
        </div>
    );
};

export default VaultUnlock;
