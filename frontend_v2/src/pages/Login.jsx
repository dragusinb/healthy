import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Activity, Mail, Lock, UserPlus, LogIn, Eye, EyeOff, Wifi, WifiOff, Globe } from 'lucide-react';
import api from '../api/client';

const Login = () => {
    const { t, i18n } = useTranslation();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isRegisterMode, setIsRegisterMode] = useState(false);
    const { login, register, loginWithGoogle } = useAuth();
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [serverStatus, setServerStatus] = useState('checking'); // 'online', 'offline', 'checking'

    // Check server status on mount
    useEffect(() => {
        checkServerStatus();
        const interval = setInterval(checkServerStatus, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const checkServerStatus = async () => {
        try {
            await api.get('/health', { timeout: 5000 });
            setServerStatus('online');
        } catch (e) {
            setServerStatus('offline');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (serverStatus === 'offline') {
            setError(t('auth.serverOffline') || 'Server is offline. Please try again later.');
            return;
        }

        setLoading(true);
        setError('');

        if (isRegisterMode) {
            if (password.length < 6) {
                setError(t('auth.passwordMinLength'));
                setLoading(false);
                return;
            }
            if (password !== confirmPassword) {
                setError(t('auth.passwordsNoMatch'));
                setLoading(false);
                return;
            }
            try {
                await register(email, password);
                navigate('/');
            } catch (err) {
                setError(err.response?.data?.detail || t('auth.emailRegistered'));
            } finally {
                setLoading(false);
            }
        } else {
            try {
                await login(email, password);
                navigate('/');
            } catch (err) {
                setError(t('auth.invalidCredentials'));
            } finally {
                setLoading(false);
            }
        }
    };

    const handleGoogleLogin = async () => {
        if (serverStatus === 'offline') {
            setError(t('auth.serverOffline') || 'Server is offline. Please try again later.');
            return;
        }

        setLoading(true);
        setError('');
        try {
            await loginWithGoogle();
            navigate('/');
        } catch (err) {
            setError(err.message || 'Google authentication failed');
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsRegisterMode(!isRegisterMode);
        setError('');
        setConfirmPassword('');
    };

    const toggleLanguage = () => {
        const newLang = i18n.language === 'ro' ? 'en' : 'ro';
        i18n.changeLanguage(newLang);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 via-white to-teal-50">
            <div className="w-full max-w-md">
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl shadow-lg shadow-primary-500/30 mb-4">
                        <Activity size={32} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-slate-800">{t('auth.appName')}</h1>
                    <p className="text-slate-500 mt-1">{t('auth.trackHealthJourney')}</p>
                </div>

                {/* Login/Register Card */}
                <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
                    {/* Top Bar: Language Toggle & Server Status */}
                    <div className="flex justify-between items-center mb-4">
                        <button
                            onClick={toggleLanguage}
                            className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-full bg-slate-50 text-slate-600 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                            title={t('settings.language')}
                        >
                            <Globe size={12} />
                            <span className="font-medium">{i18n.language.toUpperCase()}</span>
                        </button>
                        <div className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full ${
                            serverStatus === 'online'
                                ? 'bg-teal-50 text-teal-600'
                                : serverStatus === 'offline'
                                    ? 'bg-rose-50 text-rose-600'
                                    : 'bg-slate-50 text-slate-400'
                        }`}>
                            {serverStatus === 'online' ? (
                                <>
                                    <Wifi size={12} />
                                    <span>Online</span>
                                </>
                            ) : serverStatus === 'offline' ? (
                                <>
                                    <WifiOff size={12} />
                                    <span>Offline</span>
                                </>
                            ) : (
                                <>
                                    <div className="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
                                    <span>Checking...</span>
                                </>
                            )}
                        </div>
                    </div>

                    <h2 className="text-xl font-semibold text-slate-800 mb-6 text-center">
                        {isRegisterMode ? t('auth.signUp') : t('auth.signIn')}
                    </h2>

                    {error && (
                        <div className="bg-rose-50 text-rose-600 p-3 rounded-xl mb-4 text-sm border border-rose-100">
                            {error}
                        </div>
                    )}

                    {/* Google Sign In Button */}
                    <button
                        onClick={handleGoogleLogin}
                        disabled={loading || serverStatus === 'offline'}
                        className="w-full flex items-center justify-center gap-3 bg-white border-2 border-slate-200 text-slate-700 py-3 px-4 rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed mb-6"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        {t('auth.continueWithGoogle')}
                    </button>

                    {/* Divider */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-200"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-white text-slate-400">{t('auth.orContinueWithEmail')}</span>
                        </div>
                    </div>

                    {/* Email/Password Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">{t('auth.email')}</label>
                            <div className="relative">
                                <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">{t('auth.password')}</label>
                            <div className="relative">
                                <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
                                    placeholder="••••••••"
                                    required
                                    minLength={isRegisterMode ? 6 : undefined}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {isRegisterMode && (
                                <p className="text-xs text-slate-400 mt-1">{t('auth.passwordMinLength')}</p>
                            )}
                        </div>

                        {isRegisterMode && (
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">{t('auth.confirmPassword')}</label>
                                <div className="relative">
                                    <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type={showConfirmPassword ? "text" : "password"}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
                                        placeholder="••••••••"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                                    >
                                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || serverStatus === 'offline'}
                            className="w-full bg-primary-600 text-white py-3 px-4 rounded-xl hover:bg-primary-700 transition-all font-semibold shadow-md shadow-primary-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                isRegisterMode ? t('auth.creatingAccount') : t('auth.signingIn')
                            ) : (
                                <>
                                    {isRegisterMode ? <UserPlus size={18} /> : <LogIn size={18} />}
                                    {isRegisterMode ? t('auth.signUp') : t('auth.signIn')}
                                </>
                            )}
                        </button>
                    </form>

                    {/* Toggle Login/Register */}
                    <div className="mt-6 text-center">
                        <p className="text-sm text-slate-500">
                            {isRegisterMode ? t('auth.hasAccount') : t('auth.noAccount')}
                            <button
                                onClick={toggleMode}
                                className="ml-1 text-primary-600 hover:text-primary-700 font-semibold"
                            >
                                {isRegisterMode ? t('auth.signIn') : t('auth.signUp')}
                            </button>
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-sm text-slate-400 mt-6">
                    {t('auth.dataSecure')}
                </p>
            </div>
        </div>
    );
};

export default Login;
