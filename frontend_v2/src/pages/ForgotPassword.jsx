import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Mail, ArrowLeft, CheckCircle, Loader2 } from 'lucide-react';

const ForgotPassword = () => {
    const { t } = useTranslation();
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [sent, setSent] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await api.post('/auth/forgot-password', { email });
            setSent(true);
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error'));
        } finally {
            setLoading(false);
        }
    };

    if (sent) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
                    <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-8 h-8 text-teal-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 mb-2">
                        {t('auth.checkYourEmail') || 'Check your email'}
                    </h1>
                    <p className="text-slate-500 mb-6">
                        {t('auth.resetLinkSent') || 'If an account exists with this email, we\'ve sent a password reset link.'}
                    </p>
                    <p className="text-sm text-slate-400 mb-6">
                        {t('auth.checkSpam') || 'Don\'t see it? Check your spam folder.'}
                    </p>
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
                    >
                        <ArrowLeft size={18} />
                        {t('auth.backToLogin') || 'Back to login'}
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Mail className="w-8 h-8 text-primary-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800 mb-2">
                        {t('auth.forgotPassword') || 'Forgot password?'}
                    </h1>
                    <p className="text-slate-500">
                        {t('auth.forgotPasswordDesc') || 'Enter your email and we\'ll send you a reset link.'}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {t('auth.email')}
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            placeholder="email@example.com"
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
                            t('auth.sendResetLink') || 'Send reset link'
                        )}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
                    >
                        <ArrowLeft size={18} />
                        {t('auth.backToLogin') || 'Back to login'}
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
