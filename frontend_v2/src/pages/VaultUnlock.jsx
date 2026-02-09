import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Lock, Unlock, AlertTriangle, Shield, Key, LogOut, Info } from 'lucide-react';
import api from '../api/client';

const VaultUnlock = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [checkingStatus, setCheckingStatus] = useState(true);
    const [vaultStatus, setVaultStatus] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        checkVaultStatus();
    }, []);

    const checkVaultStatus = async () => {
        setCheckingStatus(true);
        try {
            // Check if user is logged in
            const token = localStorage.getItem('token');
            setIsLoggedIn(!!token);

            const res = await api.get('/admin/vault/status');
            setVaultStatus(res.data);
            // Don't redirect automatically - let user see the page
        } catch (e) {
            console.error('Failed to check vault status:', e);
        } finally {
            setCheckingStatus(false);
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
    const isAlreadyUnlocked = vaultStatus?.is_unlocked;

    // Show loading while checking status
    if (checkingStatus) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-slate-600 border-t-amber-500 rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    // If user is logged in and system vault is already unlocked, show helpful message
    if (isLoggedIn && isAlreadyUnlocked) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
                <div className="max-w-md w-full">
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 mb-4 shadow-lg shadow-teal-500/25">
                            <Unlock className="w-10 h-10 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            {t('vault.systemVaultUnlocked') || 'System Vault is Unlocked'}
                        </h1>
                    </div>

                    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 p-8 shadow-xl">
                        <div className="flex items-start gap-3 mb-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                            <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-blue-200 mb-2">
                                    {t('vault.personalVaultInfo') || 'Looking for your personal data?'}
                                </p>
                                <p className="text-xs text-blue-300/70">
                                    {t('vault.personalVaultDescription') || 'Your personal vault unlocks automatically when you log in. If you see "vault locked" errors, please log out and log back in.'}
                                </p>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <Link
                                to="/"
                                className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-semibold rounded-xl hover:from-teal-600 hover:to-emerald-700 transition-all"
                            >
                                {t('common.backToHome') || 'Back to Home'}
                            </Link>
                            <button
                                onClick={() => {
                                    localStorage.removeItem('token');
                                    navigate('/login');
                                }}
                                className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-slate-700 text-slate-200 font-semibold rounded-xl hover:bg-slate-600 transition-all"
                            >
                                <LogOut size={18} />
                                {t('nav.logout') || 'Log Out & Log Back In'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
            <div className="max-w-md w-full">
                {/* Admin notice */}
                <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-center">
                    <p className="text-xs text-amber-300">
                        {t('vault.adminOnly') || 'This page is for system administrators only'}
                    </p>
                </div>

                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 mb-4 shadow-lg shadow-orange-500/25">
                        <Shield className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {isInitMode ? t('vault.initialize') || 'Initialize System Vault' : t('vault.unlock') || 'Unlock System Vault'}
                    </h1>
                    <p className="text-slate-400">
                        {isInitMode
                            ? t('vault.initializeDescription') || 'Set up system encryption (admin only)'
                            : t('vault.unlockDescription') || 'Enter system master password'
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
                                {t('vault.locked') || 'System Vault Locked'}
                            </p>
                            <p className="text-xs text-amber-300/70">
                                {t('vault.lockedDescription') || 'System encryption keys not loaded'}
                            </p>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleUnlock} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {t('vault.masterPassword') || 'System Master Password'}
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
