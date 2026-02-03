import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Mail, Lock, UserPlus, LogIn, Eye, EyeOff, Wifi, WifiOff, Globe, CheckSquare, Square, Key, Copy, CheckCircle, AlertTriangle, X, Shield } from 'lucide-react';
import api from '../api/client';

// Recovery Key Modal Component
const RecoveryKeyModal = ({ recoveryKey, onClose, t, i18n }) => {
    const [copied, setCopied] = useState(false);
    const [confirmed, setConfirmed] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(recoveryKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = recoveryKey;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 relative max-h-[90vh] overflow-y-auto">
                {/* Success Header */}
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full mb-4 shadow-lg shadow-amber-500/30">
                        <Key size={40} className="text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-800 mb-2">
                        {i18n.language === 'ro' ? 'Salvează Cheia de Recuperare!' : 'Save Your Recovery Key!'}
                    </h2>
                    <p className="text-slate-500">
                        {i18n.language === 'ro'
                            ? 'Contul tău este acum protejat prin criptare'
                            : 'Your account is now protected with encryption'}
                    </p>
                </div>

                {/* Critical Warning */}
                <div className="bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 rounded-xl p-4 mb-6">
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                            <AlertTriangle size={20} className="text-red-600" />
                        </div>
                        <div>
                            <h4 className="font-bold text-red-800 mb-1">
                                {i18n.language === 'ro' ? 'FOARTE IMPORTANT!' : 'VERY IMPORTANT!'}
                            </h4>
                            <p className="text-sm text-red-700">
                                {i18n.language === 'ro' ? (
                                    <>
                                        Aceasta este <strong>singura dată</strong> când vei vedea această cheie.
                                        Dacă îți uiți parola și nu ai cheia, <strong>toate datele tale medicale vor fi pierdute permanent</strong>.
                                        Nu le putem recupera pentru tine.
                                    </>
                                ) : (
                                    <>
                                        This is the <strong>only time</strong> you will see this key.
                                        If you forget your password and don't have the key, <strong>all your medical data will be permanently lost</strong>.
                                        We cannot recover it for you.
                                    </>
                                )}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Recovery Key Display */}
                <div className="bg-slate-900 rounded-xl p-4 mb-6">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-medium text-slate-400 uppercase tracking-wide flex items-center gap-2">
                            <Key size={12} />
                            {i18n.language === 'ro' ? 'Cheia ta de recuperare' : 'Your recovery key'}
                        </span>
                        <button
                            onClick={handleCopy}
                            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all ${
                                copied
                                    ? 'bg-teal-500 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                            }`}
                        >
                            {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
                            {copied ? (i18n.language === 'ro' ? 'Copiat!' : 'Copied!') : (i18n.language === 'ro' ? 'Copiază' : 'Copy')}
                        </button>
                    </div>
                    <div className="font-mono text-base bg-slate-800 text-amber-400 rounded-lg p-4 break-all select-all border border-slate-700">
                        {recoveryKey}
                    </div>
                </div>

                {/* Storage Suggestions */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
                    <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                        <Shield size={16} />
                        {i18n.language === 'ro' ? 'Unde să o salvezi:' : 'Where to save it:'}
                    </h4>
                    <div className="grid grid-cols-1 gap-2 text-sm">
                        <div className="flex items-center gap-2 text-blue-700">
                            <CheckCircle size={14} className="text-blue-500" />
                            {i18n.language === 'ro' ? 'Manager de parole (1Password, Bitwarden, LastPass)' : 'Password manager (1Password, Bitwarden, LastPass)'}
                        </div>
                        <div className="flex items-center gap-2 text-blue-700">
                            <CheckCircle size={14} className="text-blue-500" />
                            {i18n.language === 'ro' ? 'Printată și păstrată într-un seif sau loc sigur' : 'Printed and stored in a safe or secure location'}
                        </div>
                        <div className="flex items-center gap-2 text-blue-700">
                            <CheckCircle size={14} className="text-blue-500" />
                            {i18n.language === 'ro' ? 'Fișier criptat pe un dispozitiv de backup' : 'Encrypted file on a backup device'}
                        </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-blue-200">
                        <p className="text-xs text-blue-600 flex items-center gap-1">
                            <X size={12} />
                            {i18n.language === 'ro'
                                ? 'NU o salva în email sau note necriptate!'
                                : 'Do NOT save it in email or unencrypted notes!'}
                        </p>
                    </div>
                </div>

                {/* Confirmation Checkbox */}
                <div className="flex items-start gap-3 mb-4 p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <button
                        type="button"
                        onClick={() => setConfirmed(!confirmed)}
                        className={`mt-0.5 flex-shrink-0 transition-colors ${confirmed ? 'text-teal-600' : 'text-slate-400'}`}
                    >
                        {confirmed ? <CheckSquare size={24} /> : <Square size={24} />}
                    </button>
                    <label className="text-sm text-slate-700 font-medium cursor-pointer" onClick={() => setConfirmed(!confirmed)}>
                        {i18n.language === 'ro'
                            ? 'Confirm că am salvat cheia de recuperare într-un loc sigur și înțeleg că fără ea nu pot recupera datele dacă îmi uit parola.'
                            : 'I confirm that I have saved the recovery key in a safe place and understand that without it I cannot recover my data if I forget my password.'}
                    </label>
                </div>

                {/* Continue Button */}
                <button
                    onClick={onClose}
                    disabled={!confirmed}
                    className={`w-full py-4 px-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2 ${
                        confirmed
                            ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white hover:from-teal-600 hover:to-emerald-600 shadow-lg shadow-teal-500/30'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    }`}
                >
                    {confirmed ? <CheckCircle size={20} /> : <Lock size={20} />}
                    {i18n.language === 'ro' ? 'Am salvat cheia, continuă' : 'I saved the key, continue'}
                </button>
            </div>
        </div>
    );
};

// Setup Password Modal - For NEW Google users
const SetupPasswordModal = ({ onComplete, onCancel, t, i18n }) => {
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { setupPassword } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password.length < 6) {
            setError(i18n.language === 'ro' ? 'Parola trebuie sa aiba minim 6 caractere' : 'Password must be at least 6 characters');
            return;
        }
        if (password !== confirmPassword) {
            setError(i18n.language === 'ro' ? 'Parolele nu coincid' : 'Passwords do not match');
            return;
        }

        setLoading(true);
        try {
            const result = await setupPassword(password);
            onComplete(result.recovery_key);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to set up password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
                {/* Header with Icon */}
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-full mb-4 shadow-lg shadow-teal-500/30">
                        <Shield size={40} className="text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-800 mb-2">
                        {i18n.language === 'ro' ? 'Ultimul Pas: Securitate' : 'Final Step: Security'}
                    </h2>
                    <p className="text-slate-500">
                        {i18n.language === 'ro'
                            ? 'Creează o parolă pentru a-ți proteja datele medicale'
                            : 'Create a password to protect your medical data'}
                    </p>
                </div>

                {/* Why This Matters Box */}
                <div className="bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-200 rounded-xl p-4 mb-6">
                    <h4 className="font-bold text-teal-800 mb-3 flex items-center gap-2">
                        <Lock size={18} />
                        {i18n.language === 'ro' ? 'De ce am nevoie de o parolă?' : 'Why do I need a password?'}
                    </h4>
                    <div className="space-y-3 text-sm text-teal-700">
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 bg-teal-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-teal-700 font-bold text-xs">1</span>
                            </div>
                            <div>
                                <strong>{i18n.language === 'ro' ? 'Criptare End-to-End' : 'End-to-End Encryption'}</strong>
                                <p className="text-teal-600">
                                    {i18n.language === 'ro'
                                        ? 'Toate datele tale medicale sunt criptate cu această parolă. Nici măcar noi nu le putem vedea.'
                                        : 'All your medical data is encrypted with this password. Not even we can see it.'}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 bg-teal-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-teal-700 font-bold text-xs">2</span>
                            </div>
                            <div>
                                <strong>{i18n.language === 'ro' ? 'Login Backup' : 'Backup Login'}</strong>
                                <p className="text-teal-600">
                                    {i18n.language === 'ro'
                                        ? 'Poți folosi această parolă + email pentru a te loga dacă Google nu funcționează.'
                                        : 'You can use this password + email to login if Google is unavailable.'}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 bg-teal-200 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-teal-700 font-bold text-xs">3</span>
                            </div>
                            <div>
                                <strong>{i18n.language === 'ro' ? 'Tu deții controlul' : 'You\'re in control'}</strong>
                                <p className="text-teal-600">
                                    {i18n.language === 'ro'
                                        ? 'Datele tale îți aparțin. Fără parola ta, nimeni nu le poate accesa.'
                                        : 'Your data belongs to you. Without your password, no one can access it.'}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Important Note */}
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6">
                    <div className="flex gap-2">
                        <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-800">
                            {i18n.language === 'ro'
                                ? 'Vei primi o cheie de recuperare după acest pas. Salvează-o! Este singura modalitate de a-ți recupera datele dacă uiți parola.'
                                : 'You\'ll receive a recovery key after this step. Save it! It\'s the only way to recover your data if you forget your password.'}
                        </p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {i18n.language === 'ro' ? 'Creează Parola' : 'Create Password'}
                        </label>
                        <div className="relative">
                            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
                                placeholder="••••••••"
                                required
                                minLength={6}
                                autoFocus
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                            {i18n.language === 'ro' ? 'Minim 6 caractere' : 'Minimum 6 characters'}
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {i18n.language === 'ro' ? 'Confirmă Parola' : 'Confirm Password'}
                        </label>
                        <div className="relative">
                            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-xl font-semibold hover:from-teal-600 hover:to-emerald-600 transition-all flex items-center justify-center gap-2 disabled:opacity-70 shadow-lg shadow-teal-500/30"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Shield size={18} />
                                {i18n.language === 'ro' ? 'Activează Criptarea' : 'Enable Encryption'}
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

// Unlock Data Modal - For RETURNING Google users
const UnlockDataModal = ({ onComplete, onCancel, t, i18n }) => {
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { unlockData } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await unlockData(password);
            onComplete();
        } catch (err) {
            setError(err.response?.data?.detail || (i18n.language === 'ro' ? 'Parolă incorectă' : 'Incorrect password'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
                {/* Header */}
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full mb-4 shadow-lg shadow-primary-500/30">
                        <Lock size={32} className="text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-800 mb-2">
                        {i18n.language === 'ro' ? 'Bine ai revenit!' : 'Welcome back!'}
                    </h2>
                    <p className="text-slate-500 text-sm">
                        {i18n.language === 'ro'
                            ? 'Introdu parola pentru a-ți accesa datele criptate'
                            : 'Enter your password to access your encrypted data'}
                    </p>
                </div>

                {/* Explanation Box */}
                <div className="bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 rounded-xl p-4 mb-6">
                    <div className="flex gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                            <Shield size={16} className="text-slate-600" />
                        </div>
                        <div className="text-sm text-slate-600">
                            <p className="font-medium text-slate-700 mb-1">
                                {i18n.language === 'ro' ? 'De ce trebuie să introduc parola?' : 'Why do I need to enter my password?'}
                            </p>
                            <p>
                                {i18n.language === 'ro'
                                    ? 'Datele tale medicale sunt criptate. Google verifică identitatea ta, dar doar parola ta poate decripta datele.'
                                    : 'Your medical data is encrypted. Google verifies your identity, but only your password can decrypt the data.'}
                            </p>
                        </div>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm flex items-center gap-2">
                            <AlertTriangle size={16} />
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            {i18n.language === 'ro' ? 'Parola de securitate' : 'Security Password'}
                        </label>
                        <div className="relative">
                            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                                placeholder={i18n.language === 'ro' ? 'Parola creată la înregistrare' : 'Password created at registration'}
                                required
                                autoFocus
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                            {i18n.language === 'ro'
                                ? 'Aceasta este parola pe care ai creat-o prima dată când ai folosit aplicația'
                                : 'This is the password you created when you first used the app'}
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 shadow-md shadow-primary-500/30"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <CheckCircle size={18} />
                                {i18n.language === 'ro' ? 'Accesează Datele' : 'Access Data'}
                            </>
                        )}
                    </button>

                    <div className="text-center pt-2 border-t border-slate-100">
                        <Link to="/forgot-password" className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center gap-1">
                            <Key size={14} />
                            {i18n.language === 'ro' ? 'Am uitat parola (am nevoie de cheia de recuperare)' : 'Forgot password (need recovery key)'}
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
};

const Login = () => {
    const { t, i18n } = useTranslation();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isRegisterMode, setIsRegisterMode] = useState(false);
    const [acceptedTerms, setAcceptedTerms] = useState(false);
    const { login, register, loginWithGoogle, pendingGoogleSetup, clearPendingSetup } = useAuth();
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [serverStatus, setServerStatus] = useState('checking'); // 'online', 'offline', 'checking'
    const [recoveryKey, setRecoveryKey] = useState(null); // For showing recovery key modal

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
            if (!acceptedTerms) {
                setError(t('auth.mustAcceptTerms'));
                setLoading(false);
                return;
            }
            try {
                const result = await register(email, password, acceptedTerms);
                // Check if registration returned a recovery key
                if (result?.recovery_key) {
                    setRecoveryKey(result.recovery_key);
                    // Don't navigate yet - wait for user to save recovery key
                } else {
                    navigate('/');
                }
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
            const result = await loginWithGoogle();
            // Don't navigate yet if user needs to complete setup or unlock
            if (!result?.needsSetup && !result?.needsUnlock) {
                navigate('/');
            }
            // If needsSetup or needsUnlock, pendingGoogleSetup state is set
            // and the appropriate modal will be shown
        } catch (err) {
            setError(err.message || 'Google authentication failed');
        } finally {
            setLoading(false);
        }
    };

    // Handlers for Google OAuth setup/unlock modals
    const handleSetupComplete = (newRecoveryKey) => {
        setRecoveryKey(newRecoveryKey);
        // Recovery key modal will be shown, then navigate on close
    };

    const handleUnlockComplete = () => {
        navigate('/');
    };

    const toggleMode = () => {
        setIsRegisterMode(!isRegisterMode);
        setError('');
        setConfirmPassword('');
        setAcceptedTerms(false);
    };

    const toggleLanguage = () => {
        const newLang = i18n.language === 'ro' ? 'en' : 'ro';
        i18n.changeLanguage(newLang);
    };

    const handleRecoveryKeyClose = () => {
        setRecoveryKey(null);
        navigate('/');
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 via-white to-teal-50">
            {/* Recovery Key Modal */}
            {recoveryKey && (
                <RecoveryKeyModal
                    recoveryKey={recoveryKey}
                    onClose={handleRecoveryKeyClose}
                    t={t}
                    i18n={i18n}
                />
            )}

            {/* Google OAuth: Setup Password Modal (new users) */}
            {pendingGoogleSetup?.type === 'setup_password' && !recoveryKey && (
                <SetupPasswordModal
                    onComplete={handleSetupComplete}
                    onCancel={() => clearPendingSetup()}
                    t={t}
                    i18n={i18n}
                />
            )}

            {/* Google OAuth: Unlock Data Modal (returning users) */}
            {pendingGoogleSetup?.type === 'unlock_data' && (
                <UnlockDataModal
                    onComplete={handleUnlockComplete}
                    onCancel={() => clearPendingSetup()}
                    t={t}
                    i18n={i18n}
                />
            )}

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
                            {!isRegisterMode && (
                                <div className="text-right mt-1">
                                    <Link
                                        to="/forgot-password"
                                        className="text-sm text-primary-600 hover:text-primary-700"
                                    >
                                        {t('auth.forgotPassword')}
                                    </Link>
                                </div>
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

                        {/* Encryption Info Box - Show during registration */}
                        {isRegisterMode && (
                            <div className="bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-200 rounded-xl p-4">
                                <div className="flex gap-3">
                                    <div className="flex-shrink-0 w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                                        <Shield size={20} className="text-teal-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-teal-800 text-sm mb-1">
                                            {i18n.language === 'ro' ? 'Datele tale sunt criptate' : 'Your data is encrypted'}
                                        </h4>
                                        <p className="text-xs text-teal-700 leading-relaxed">
                                            {i18n.language === 'ro' ? (
                                                <>
                                                    Parola ta este și <strong>cheia de criptare</strong>. Toate datele medicale sunt criptate astfel încât <strong>doar tu le poți accesa</strong>. Nici măcar noi nu le putem vedea.
                                                </>
                                            ) : (
                                                <>
                                                    Your password is also your <strong>encryption key</strong>. All medical data is encrypted so <strong>only you can access it</strong>. Not even we can see it.
                                                </>
                                            )}
                                        </p>
                                        <p className="text-xs text-teal-600 mt-2 flex items-center gap-1">
                                            <Key size={12} />
                                            {i18n.language === 'ro'
                                                ? 'Vei primi o cheie de recuperare după înregistrare'
                                                : 'You\'ll receive a recovery key after registration'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Terms & Privacy Consent */}
                        {isRegisterMode && (
                            <div className="flex items-start gap-3">
                                <button
                                    type="button"
                                    onClick={() => setAcceptedTerms(!acceptedTerms)}
                                    className={`mt-0.5 flex-shrink-0 ${acceptedTerms ? 'text-primary-600' : 'text-slate-400'}`}
                                >
                                    {acceptedTerms ? <CheckSquare size={20} /> : <Square size={20} />}
                                </button>
                                <label className="text-sm text-slate-600 leading-relaxed">
                                    {i18n.language === 'ro' ? (
                                        <>
                                            Accept{' '}
                                            <Link to="/terms" target="_blank" className="text-primary-600 hover:underline font-medium">
                                                Termenii și Condițiile
                                            </Link>
                                            {' '}și{' '}
                                            <Link to="/privacy" target="_blank" className="text-primary-600 hover:underline font-medium">
                                                Politica de Confidențialitate
                                            </Link>
                                        </>
                                    ) : (
                                        <>
                                            I accept the{' '}
                                            <Link to="/terms" target="_blank" className="text-primary-600 hover:underline font-medium">
                                                Terms and Conditions
                                            </Link>
                                            {' '}and{' '}
                                            <Link to="/privacy" target="_blank" className="text-primary-600 hover:underline font-medium">
                                                Privacy Policy
                                            </Link>
                                        </>
                                    )}
                                </label>
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
                <div className="text-center text-sm text-slate-400 mt-6">
                    <p>{t('auth.dataSecure')}</p>
                    <div className="mt-2 space-x-3">
                        <Link to="/terms" target="_blank" className="text-primary-600 hover:underline">
                            {i18n.language === 'ro' ? 'Termeni' : 'Terms'}
                        </Link>
                        <span>•</span>
                        <Link to="/privacy" target="_blank" className="text-primary-600 hover:underline">
                            {i18n.language === 'ro' ? 'Confidențialitate' : 'Privacy'}
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
