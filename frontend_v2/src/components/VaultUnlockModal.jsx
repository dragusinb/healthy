import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Lock, Eye, EyeOff, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const VaultUnlockModal = () => {
    const { t } = useTranslation();
    const { vaultLocked, unlockVault, dismissVaultUnlock, logout } = useAuth();
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    if (!vaultLocked) return null;

    const handleUnlock = async (e) => {
        e.preventDefault();
        if (!password.trim()) {
            setError(t('auth.password') + ' ' + t('common.error').toLowerCase());
            return;
        }

        setLoading(true);
        setError('');

        try {
            await unlockVault(password);
            setSuccess(true);
            setPassword('');
            // Auto-close after success
            setTimeout(() => {
                setSuccess(false);
            }, 1500);
        } catch (err) {
            setError(err.response?.data?.detail || t('auth.invalidCredentials'));
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        dismissVaultUnlock();
        logout();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-5 text-white">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-white/20 rounded-lg">
                            <Lock size={24} />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold">
                                {t('vault.sessionExpired') || 'Session Expired'}
                            </h2>
                            <p className="text-sm text-white/80">
                                {t('vault.enterPasswordToUnlock') || 'Enter your password to unlock your data'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6">
                    {success ? (
                        <div className="flex flex-col items-center py-4">
                            <div className="p-3 bg-green-100 rounded-full mb-3">
                                <CheckCircle size={32} className="text-green-600" />
                            </div>
                            <p className="text-green-700 font-medium">
                                {t('vault.unlockSuccess') || 'Data unlocked successfully!'}
                            </p>
                        </div>
                    ) : (
                        <form onSubmit={handleUnlock}>
                            <p className="text-sm text-slate-600 mb-4">
                                {t('vault.sessionExpiredDesc') || 'Your session has expired. Please enter your password to continue accessing your encrypted medical data.'}
                            </p>

                            {error && (
                                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
                                    <AlertCircle size={16} />
                                    {error}
                                </div>
                            )}

                            <div className="mb-4">
                                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                    {t('auth.password')}
                                </label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10"
                                        placeholder="********"
                                        autoFocus
                                        disabled={loading}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex-1 bg-primary-600 hover:bg-primary-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 size={18} className="animate-spin" />
                                            {t('common.loading')}
                                        </>
                                    ) : (
                                        <>
                                            <Lock size={18} />
                                            {t('vault.unlock') || 'Unlock'}
                                        </>
                                    )}
                                </button>
                                <button
                                    type="button"
                                    onClick={handleLogout}
                                    disabled={loading}
                                    className="px-4 py-2.5 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                                >
                                    {t('nav.logout')}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VaultUnlockModal;
