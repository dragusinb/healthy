import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Lock, CheckCircle, XCircle, Loader2, Eye, EyeOff, Key, AlertTriangle } from 'lucide-react';

const ResetPassword = () => {
    const { t, i18n } = useTranslation();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [recoveryKey, setRecoveryKey] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [checkingToken, setCheckingToken] = useState(true);
    const [requiresRecoveryKey, setRequiresRecoveryKey] = useState(false);
    const [status, setStatus] = useState('form'); // form, success, error
    const [error, setError] = useState('');

    const token = searchParams.get('token');

    useEffect(() => {
        if (!token) {
            setStatus('error');
            setError(t('auth.invalidResetLink') || 'Invalid password reset link');
            setCheckingToken(false);
            return;
        }
        checkToken();
    }, [token]);

    const checkToken = async () => {
        try {
            const res = await api.get(`/auth/check-reset-token/${token}`);
            setRequiresRecoveryKey(res.data.requires_recovery_key);
            setCheckingToken(false);
        } catch (err) {
            setStatus('error');
            setError(err.response?.data?.detail || t('auth.invalidResetLink') || 'Invalid or expired reset link');
            setCheckingToken(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setError(t('auth.passwordsNoMatch'));
            return;
        }

        if (password.length < 6) {
            setError(t('auth.passwordMinLength'));
            return;
        }

        if (requiresRecoveryKey && !recoveryKey.trim()) {
            setError(i18n.language === 'ro' ? 'Cheia de recuperare este obligatorie' : 'Recovery key is required');
            return;
        }

        setLoading(true);
        setError('');

        try {
            if (requiresRecoveryKey) {
                await api.post('/auth/reset-password-with-recovery', {
                    token,
                    new_password: password,
                    recovery_key: recoveryKey.trim()
                });
            } else {
                await api.post('/auth/reset-password', {
                    token,
                    new_password: password
                });
            }
            setStatus('success');
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error'));
        } finally {
            setLoading(false);
        }
    };

    if (status === 'success') {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-8 h-8 text-teal-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 mb-2">
                        {t('auth.passwordResetSuccess') || 'Password Reset!'}
                    </h1>
                    <p className="text-slate-500 mb-6">
                        {t('auth.passwordResetSuccessDesc') || 'Your password has been reset successfully. You can now login with your new password.'}
                    </p>
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
                    >
                        {t('auth.goToLogin') || 'Go to Login'}
                    </Link>
                </div>
            </div>
        );
    }

    if (status === 'error' && !token) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <XCircle className="w-8 h-8 text-rose-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 mb-2">
                        {t('auth.invalidLink') || 'Invalid Link'}
                    </h1>
                    <p className="text-slate-500 mb-6">{error}</p>
                    <Link
                        to="/forgot-password"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
                    >
                        {t('auth.requestNewLink') || 'Request new link'}
                    </Link>
                </div>
            </div>
        );
    }

    // Show loading while checking token
    if (checkingToken) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
                    <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
                    <p className="text-slate-600">
                        {i18n.language === 'ro' ? 'Se verifica linkul...' : 'Verifying link...'}
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Lock className="w-8 h-8 text-primary-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 mb-2">
                        {t('auth.setNewPassword') || 'Set new password'}
                    </h1>
                    <p className="text-slate-500">
                        {t('auth.setNewPasswordDesc') || 'Enter your new password below.'}
                    </p>
                </div>

                {/* Recovery Key Warning */}
                {requiresRecoveryKey && (
                    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                        <div className="flex gap-3">
                            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-amber-800 mb-1">
                                    {i18n.language === 'ro' ? 'Cont cu date criptate' : 'Account with encrypted data'}
                                </p>
                                <p className="text-xs text-amber-700">
                                    {i18n.language === 'ro'
                                        ? 'Contul tau are date criptate. Pentru a reseta parola, ai nevoie de cheia de recuperare pe care ai primit-o la inregistrare.'
                                        : 'Your account has encrypted data. To reset your password, you need the recovery key you received when you registered.'}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    {/* Recovery Key Field */}
                    {requiresRecoveryKey && (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                <Key className="w-4 h-4 inline mr-1" />
                                {i18n.language === 'ro' ? 'Cheia de recuperare' : 'Recovery key'}
                            </label>
                            <input
                                type="text"
                                value={recoveryKey}
                                onChange={(e) => setRecoveryKey(e.target.value.toUpperCase())}
                                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent font-mono text-sm"
                                placeholder="XXXX-XXXX-XXXX-XXXX-..."
                                required
                            />
                            <p className="text-xs text-slate-400 mt-1">
                                {i18n.language === 'ro'
                                    ? 'Cheia pe care ai salvat-o la inregistrare'
                                    : 'The key you saved when registering'}
                            </p>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {t('auth.newPassword') || 'New password'}
                        </label>
                        <div className="relative">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-12"
                                placeholder="******"
                                required
                                minLength={6}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">{t('auth.passwordMinLength')}</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {t('auth.confirmPassword')}
                        </label>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            placeholder="******"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-70"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                {t('common.loading')}
                            </>
                        ) : (
                            t('auth.resetPassword') || 'Reset password'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ResetPassword;
