import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import { LayoutDashboard, FileText, Activity, LogOut, User, HeartPulse, Link as LinkIcon, Brain, Shield, Globe, Menu, X, ClipboardList, Bell, CreditCard, Mail, Loader2, CheckCircle } from 'lucide-react';
import { cn } from '../lib/utils';

const SidebarItem = ({ to, icon: Icon, label, onClick }) => (
    <NavLink
        to={to}
        onClick={onClick}
        className={({ isActive }) => cn(
            "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium text-sm group",
            isActive
                ? "bg-primary-50 text-primary-700 shadow-sm"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
        )}
    >
        {({ isActive }) => (
            <>
                <Icon size={20} className={isActive ? "text-primary-600" : "text-slate-400 group-hover:text-slate-600"} />
                <span>{label}</span>
            </>
        )}
    </NavLink>
);

const Layout = ({ children }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const { t, i18n } = useTranslation();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [verificationState, setVerificationState] = useState('idle'); // idle, sending, sent, error
    const [bannerDismissed, setBannerDismissed] = useState(() => {
        return localStorage.getItem('emailBannerDismissed') === 'true';
    });

    // Close mobile menu when route changes
    useEffect(() => {
        setMobileMenuOpen(false);
    }, [location.pathname]);

    const handleResendVerification = async () => {
        setVerificationState('sending');
        try {
            await api.post('/auth/resend-verification', { email: user?.email });
            setVerificationState('sent');
        } catch (error) {
            setVerificationState('error');
            setTimeout(() => setVerificationState('idle'), 3000);
        }
    };

    const dismissBanner = () => {
        setBannerDismissed(true);
        localStorage.setItem('emailBannerDismissed', 'true');
    };

    const showVerificationBanner = user && user.email_verified === false && !bannerDismissed;

    const closeMobileMenu = () => setMobileMenuOpen(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const toggleLanguage = () => {
        const newLang = i18n.language === 'ro' ? 'en' : 'ro';
        i18n.changeLanguage(newLang);
    };

    // Page Title mapping based on path
    const getPageTitle = () => {
        const path = location.pathname;
        if (path === '/') return t('nav.dashboard');
        if (path.startsWith('/documents')) return t('nav.documents');
        if (path.startsWith('/biomarkers')) return t('nav.biomarkers');
        if (path.startsWith('/evolution')) return t('evolution.title');
        if (path.startsWith('/health')) return t('nav.doctorAI');
        if (path.startsWith('/screenings')) return t('nav.screenings');
        if (path.startsWith('/profile')) return t('profile.title');
        if (path.startsWith('/linked-accounts')) return t('linkedAccounts.title');
        if (path.startsWith('/settings')) return t('notifications.preferences');
        if (path.startsWith('/billing')) return t('billing.title');
        if (path.startsWith('/admin')) return t('admin.title');
        return '';
    }

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            {/* Modern Sidebar */}
            <aside className="w-72 bg-white border-r border-slate-200 flex flex-col hidden md:flex h-full shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)] z-10">
                <div className="p-8 pb-4">
                    <div className="flex items-center gap-3 text-primary-600 mb-8">
                        <div className="p-2.5 bg-primary-100 rounded-xl">
                            <HeartPulse size={28} className="text-primary-600" />
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Analize<span className="text-primary-500">.online</span></h1>
                    </div>

                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">Menu</div>
                    <nav className="space-y-1.5">
                        <SidebarItem to="/" icon={LayoutDashboard} label={t('nav.dashboard')} />
                        <SidebarItem to="/documents" icon={FileText} label={t('nav.documents')} />
                        <SidebarItem to="/biomarkers" icon={Activity} label={t('nav.biomarkers')} />
                        <SidebarItem to="/health" icon={Brain} label={t('nav.doctorAI')} />
                        <SidebarItem to="/screenings" icon={ClipboardList} label={t('nav.screenings')} />
                        <div className="pt-4 mt-4 border-t border-slate-100"></div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">{t('nav.settings')}</div>
                        <SidebarItem to="/profile" icon={User} label={t('nav.profile')} />
                        <SidebarItem to="/linked-accounts" icon={LinkIcon} label={t('nav.linkedAccounts')} />
                        <SidebarItem to="/settings" icon={Bell} label={t('notifications.preferences')} />
                        <SidebarItem to="/billing" icon={CreditCard} label={t('nav.billing')} />
                        {user?.is_admin && (
                            <SidebarItem to="/admin" icon={Shield} label={t('nav.admin')} />
                        )}
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-100">
                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 mb-2">
                        <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 overflow-hidden border-2 border-white shadow-sm">
                            <User size={20} />
                        </div>
                        <div className="overflow-hidden flex-1">
                            <p className="text-sm font-semibold text-slate-700 truncate">{user?.email?.split('@')[0]}</p>
                            <p className="text-xs text-slate-400 truncate font-medium">
                                {user?.is_admin ? 'Admin' : 'Free Plan'}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={toggleLanguage}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors font-medium border border-slate-200"
                            title={t('settings.language')}
                        >
                            <Globe size={16} />
                            {i18n.language.toUpperCase()}
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors font-medium"
                        >
                            <LogOut size={16} />
                            {t('nav.logout')}
                        </button>
                    </div>
                    {/* Legal Links */}
                    <div className="mt-3 pt-3 border-t border-slate-100 flex justify-center gap-3 text-xs text-slate-400">
                        <a href="/terms" target="_blank" className="hover:text-primary-600 transition-colors">
                            {i18n.language === 'ro' ? 'Termeni' : 'Terms'}
                        </a>
                        <span>•</span>
                        <a href="/privacy" target="_blank" className="hover:text-primary-600 transition-colors">
                            {i18n.language === 'ro' ? 'Confidențialitate' : 'Privacy'}
                        </a>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto relative scroll-smooth">
                {/* Top Header for Mobile & Title */}
                <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-slate-200 px-4 py-3 flex items-center justify-between md:hidden">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setMobileMenuOpen(true)}
                            className="min-h-11 min-w-11 flex items-center justify-center text-slate-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors -ml-1"
                        >
                            <Menu size={22} />
                        </button>
                        <div className="p-2 bg-primary-50 rounded-lg">
                            <HeartPulse size={20} className="text-primary-600" />
                        </div>
                        <span className="font-bold text-slate-800">Analize.online</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <button
                            onClick={toggleLanguage}
                            className="min-h-11 min-w-11 flex items-center justify-center text-slate-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        >
                            <Globe size={18} />
                            <span className="text-xs font-medium ml-1">{i18n.language.toUpperCase()}</span>
                        </button>
                        <button onClick={handleLogout} className="min-h-11 min-w-11 flex items-center justify-center text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors">
                            <LogOut size={18} />
                        </button>
                    </div>
                </header>

                {/* Mobile Menu Drawer */}
                {mobileMenuOpen && (
                    <div className="fixed inset-0 z-50 md:hidden">
                        {/* Backdrop */}
                        <div
                            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                            onClick={closeMobileMenu}
                        />
                        {/* Drawer */}
                        <aside className="absolute left-0 top-0 h-full w-72 max-w-[calc(100vw-3rem)] bg-white shadow-xl flex flex-col animate-in slide-in-from-left duration-300">
                            <div className="p-6 pb-4">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3 text-primary-600">
                                        <div className="p-2.5 bg-primary-100 rounded-xl">
                                            <HeartPulse size={28} className="text-primary-600" />
                                        </div>
                                        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Analize<span className="text-primary-500">.online</span></h1>
                                    </div>
                                    <button
                                        onClick={closeMobileMenu}
                                        className="min-h-11 min-w-11 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>

                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">Menu</div>
                                <nav className="space-y-1.5">
                                    <SidebarItem to="/" icon={LayoutDashboard} label={t('nav.dashboard')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/documents" icon={FileText} label={t('nav.documents')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/biomarkers" icon={Activity} label={t('nav.biomarkers')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/health" icon={Brain} label={t('nav.doctorAI')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/screenings" icon={ClipboardList} label={t('nav.screenings')} onClick={closeMobileMenu} />
                                    <div className="pt-4 mt-4 border-t border-slate-100"></div>
                                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">{t('nav.settings')}</div>
                                    <SidebarItem to="/profile" icon={User} label={t('nav.profile')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/linked-accounts" icon={LinkIcon} label={t('nav.linkedAccounts')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/settings" icon={Bell} label={t('notifications.preferences')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/billing" icon={CreditCard} label={t('nav.billing')} onClick={closeMobileMenu} />
                                    {user?.is_admin && (
                                        <SidebarItem to="/admin" icon={Shield} label={t('nav.admin')} onClick={closeMobileMenu} />
                                    )}
                                </nav>
                            </div>

                            <div className="mt-auto p-6 border-t border-slate-100">
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 mb-2">
                                    <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 overflow-hidden border-2 border-white shadow-sm">
                                        <User size={20} />
                                    </div>
                                    <div className="overflow-hidden flex-1">
                                        <p className="text-sm font-semibold text-slate-700 truncate">{user?.email?.split('@')[0]}</p>
                                        <p className="text-xs text-slate-400 truncate font-medium">
                                            {user?.is_admin ? 'Admin' : 'Free Plan'}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => { toggleLanguage(); closeMobileMenu(); }}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors font-medium border border-slate-200"
                                        title={t('settings.language')}
                                    >
                                        <Globe size={16} />
                                        {i18n.language.toUpperCase()}
                                    </button>
                                    <button
                                        onClick={() => { handleLogout(); closeMobileMenu(); }}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors font-medium"
                                    >
                                        <LogOut size={16} />
                                        {t('nav.logout')}
                                    </button>
                                </div>
                                {/* Legal Links */}
                                <div className="mt-3 pt-3 border-t border-slate-100 flex justify-center gap-3 text-xs text-slate-400">
                                    <a href="/terms" target="_blank" className="hover:text-primary-600 transition-colors">
                                        {i18n.language === 'ro' ? 'Termeni' : 'Terms'}
                                    </a>
                                    <span>•</span>
                                    <a href="/privacy" target="_blank" className="hover:text-primary-600 transition-colors">
                                        {i18n.language === 'ro' ? 'Confidențialitate' : 'Privacy'}
                                    </a>
                                </div>
                            </div>
                        </aside>
                    </div>
                )}

                <div className="max-w-7xl mx-auto p-6 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Email Verification Banner */}
                    {showVerificationBanner && (
                        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between gap-4 flex-wrap">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-amber-100 rounded-lg">
                                    <Mail size={20} className="text-amber-600" />
                                </div>
                                <div>
                                    <p className="font-medium text-amber-800">
                                        {t('auth.verifyEmailBanner') || 'Please verify your email address'}
                                    </p>
                                    <p className="text-sm text-amber-600">
                                        {t('auth.verifyEmailBannerDesc') || 'Check your inbox for a verification link'}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                {verificationState === 'sent' ? (
                                    <span className="flex items-center gap-2 text-sm text-teal-600 font-medium">
                                        <CheckCircle size={16} />
                                        {t('auth.verificationSent') || 'Sent!'}
                                    </span>
                                ) : (
                                    <button
                                        onClick={handleResendVerification}
                                        disabled={verificationState === 'sending'}
                                        className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium disabled:opacity-50"
                                    >
                                        {verificationState === 'sending' ? (
                                            <Loader2 size={16} className="animate-spin" />
                                        ) : (
                                            <Mail size={16} />
                                        )}
                                        {t('auth.resendVerification') || 'Resend'}
                                    </button>
                                )}
                                <button
                                    onClick={dismissBanner}
                                    className="min-h-11 min-w-11 flex items-center justify-center text-amber-500 hover:text-amber-700 hover:bg-amber-100 rounded-lg transition-colors"
                                    title={t('common.close')}
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Dynamic Page Header */}
                    <div className="mb-8 hidden md:block">
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">{getPageTitle()}</h2>
                        <div className="h-1 w-20 bg-primary-500 rounded-full mt-2 opacity-20"></div>
                    </div>

                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
