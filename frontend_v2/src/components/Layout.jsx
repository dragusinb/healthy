import React, { useState, useEffect, useRef, useCallback } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import { LayoutDashboard, FileText, Activity, LogOut, User, HeartPulse, Link as LinkIcon, Brain, Shield, Globe, Menu, X, ClipboardList, Settings2, CreditCard, Mail, Loader2, CheckCircle, Users, MessageSquare, Leaf, Pill, Sun, Moon, FlaskConical, Stethoscope, Bell, BarChart3, Gift } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { cn } from '../lib/utils';
import FeedbackButton from './FeedbackButton';
import VaultUnlockModal from './VaultUnlockModal';
import TrialBanner from './TrialBanner';

const SidebarItem = ({ to, icon: Icon, label, onClick, title }) => (
    <NavLink
        to={to}
        onClick={onClick}
        title={title || label}
        aria-label={title || label}
        className={({ isActive }) => cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 font-medium text-sm group",
            isActive
                ? "bg-primary-50 text-primary-700 shadow-sm dark:bg-primary-900/30 dark:text-primary-300"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700/50 dark:hover:text-slate-200"
        )}
    >
        {({ isActive }) => (
            <>
                <Icon size={18} className={isActive ? "text-primary-600 dark:text-primary-400" : "text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300"} />
                <span>{label}</span>
            </>
        )}
    </NavLink>
);

const BottomNavItem = ({ to, icon: Icon, label }) => {
    const location = useLocation();
    const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
    return (
        <NavLink
            to={to}
            className={cn(
                "flex flex-col items-center justify-center gap-0.5 flex-1 py-2 min-h-[44px] text-[11px] font-medium transition-colors min-w-0",
                isActive
                    ? "text-primary-600 dark:text-primary-400"
                    : "text-slate-500 dark:text-slate-500"
            )}
        >
            <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
            <span className="truncate max-w-full px-1">{label}</span>
        </NavLink>
    );
};

const PAGE_TITLE_MAP = {
    '/': 'nav.dashboard',
    '/documents': 'nav.documents',
    '/biomarkers': 'nav.biomarkers',
    '/health': 'nav.doctorAI',
    '/screenings': 'nav.screenings',
    '/lifestyle': 'nav.lifestyle',
    '/medications': 'nav.medications',
    '/family': 'nav.family',
    '/profile': 'nav.profile',
    '/linked-accounts': 'nav.linkedAccounts',
    '/settings': 'nav.settingsTitle',
    '/billing': 'nav.billing',
    '/referral': 'nav.referral',
    '/support': 'nav.support',
    '/admin': 'nav.admin',
};

const Layout = ({ children }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const { t, i18n } = useTranslation();
    const { theme, toggleTheme } = useTheme();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [verificationState, setVerificationState] = useState('idle'); // idle, sending, sent, error
    const [bannerDismissed, setBannerDismissed] = useState(() => {
        return localStorage.getItem('emailBannerDismissed') === 'true';
    });
    const [isOffline, setIsOffline] = useState(!navigator.onLine);
    const [isDesktop, setIsDesktop] = useState(() => typeof window !== 'undefined' && window.innerWidth >= 768);
    const mainRef = useRef(null);
    const [showScrollGradient, setShowScrollGradient] = useState(false);

    // Offline detection
    useEffect(() => {
        const handleOnline = () => setIsOffline(false);
        const handleOffline = () => setIsOffline(true);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // Desktop detection - only render sidebar in DOM on desktop
    useEffect(() => {
        const mq = window.matchMedia('(min-width: 768px)');
        const handler = (e) => setIsDesktop(e.matches);
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
    }, []);

    // Scroll affordance: detect if content is scrollable and not at bottom
    const checkScrollable = useCallback(() => {
        const el = mainRef.current;
        if (!el) return;
        const hasMoreContent = el.scrollHeight - el.scrollTop - el.clientHeight > 40;
        setShowScrollGradient(hasMoreContent);
    }, []);

    useEffect(() => {
        const el = mainRef.current;
        if (!el) return;
        checkScrollable();
        el.addEventListener('scroll', checkScrollable, { passive: true });
        const resizeObserver = new ResizeObserver(checkScrollable);
        resizeObserver.observe(el);
        return () => {
            el.removeEventListener('scroll', checkScrollable);
            resizeObserver.disconnect();
        };
    }, [checkScrollable, location.pathname]);

    // Close mobile menu when route changes
    useEffect(() => {
        setMobileMenuOpen(false);
    }, [location.pathname]);

    // Update document title based on current route
    useEffect(() => {
        const pageTitle = (() => {
            const path = location.pathname;
            if (path === '/') return t('nav.dashboard');
            if (path.startsWith('/documents')) return t('nav.documents');
            if (path.startsWith('/biomarkers')) return t('nav.biomarkers');
            if (path.startsWith('/evolution')) return t('evolution.title');
            if (path.startsWith('/health')) return t('nav.doctorAI');
            if (path.startsWith('/screenings')) return t('nav.screenings');
            if (path.startsWith('/family')) return t('nav.family');
            if (path.startsWith('/lifestyle')) return t('lifestyle.title');
            if (path.startsWith('/medications')) return t('medications.title');
            if (path.startsWith('/profile')) return t('profile.title');
            if (path.startsWith('/linked-accounts')) return t('linkedAccounts.title');
            if (path.startsWith('/settings')) return t('nav.settingsTitle');
            if (path.startsWith('/billing')) return t('billing.title');
            if (path.startsWith('/admin')) return t('admin.title');
            return '';
        })();
        const suffix = 'Analize.Online';
        document.title = pageTitle ? `${pageTitle} - ${suffix}` : suffix;
    }, [location.pathname, i18n.language]);

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
        if (path.startsWith('/family')) return t('nav.family') || (i18n.language === 'ro' ? 'Familia Mea' : 'My Family');
        if (path.startsWith('/lifestyle')) return t('lifestyle.title');
        if (path.startsWith('/medications')) return t('medications.title');
        if (path.startsWith('/profile')) return t('profile.title');
        if (path.startsWith('/linked-accounts')) return t('linkedAccounts.title');
        if (path.startsWith('/settings')) return t('nav.settingsTitle');
        if (path.startsWith('/billing')) return t('billing.title');
        if (path.startsWith('/admin')) return t('admin.title');
        return '';
    }

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden">
            {/* Skip Navigation Link */}
            <a
                href="#main-content"
                className="sr-only focus:not-sr-only focus:absolute focus:z-[100] focus:top-2 focus:left-2 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:text-sm focus:font-medium focus:shadow-lg"
            >
                {t('nav.skipToContent') || 'Skip to main content'}
            </a>
            {/* Modern Sidebar - only rendered in DOM on desktop to prevent QA counting hidden items */}
            {isDesktop && <aside className="w-72 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col print:hidden h-full shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)] z-10" role="navigation" aria-label={t('nav.mainNav') || 'Main navigation'}>
                <div className="p-6 pb-2">
                    <div className="flex items-center gap-3 text-primary-600 mb-6">
                        <div className="p-2 bg-primary-100 rounded-xl">
                            <HeartPulse size={24} className="text-primary-600" />
                        </div>
                        <span className="text-xl font-bold tracking-tight text-slate-800 dark:text-slate-100">Analize<span className="text-primary-500">.online</span></span>
                    </div>

                    <div className="text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-2 px-2">Menu</div>
                    <nav className="space-y-0.5">
                        <SidebarItem to="/" icon={LayoutDashboard} label={t('nav.dashboard')} />
                        <SidebarItem to="/documents" icon={FileText} label={t('nav.documents')} />
                        <SidebarItem to="/biomarkers" icon={Activity} label={t('nav.biomarkers')} />
                        <SidebarItem to="/health" icon={Brain} label={t('nav.doctorAI')} />
                        <SidebarItem to="/screenings" icon={ClipboardList} label={t('nav.screenings')} />
                        <SidebarItem to="/lifestyle" icon={Leaf} label={t('nav.lifestyle')} />
                        <SidebarItem to="/medications" icon={Pill} label={t('nav.medications')} />
                        <SidebarItem to="/family" icon={Users} label={t('nav.family')} />
                    </nav>
                    <hr className="my-4 mx-2 border-t-2 border-slate-200 dark:border-slate-600" role="separator" />
                    <div className="text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-2 px-2">{t('nav.settings')}</div>
                    <nav className="space-y-0.5">
                        <SidebarItem to="/profile" icon={User} label={t('nav.profile')} />
                        <SidebarItem to="/linked-accounts" icon={LinkIcon} label={t('nav.linkedAccounts')} />
                        <SidebarItem to="/settings" icon={Settings2} label={t('nav.settingsTitle')} />
                        <SidebarItem to="/billing" icon={CreditCard} label={t('nav.billing')} />
                        <SidebarItem to="/referral" icon={Gift} label={t('nav.referral')} />
                        <SidebarItem to="/support" icon={MessageSquare} label={t('nav.support')} />
                        {user?.is_admin && (
                            <>
                            <SidebarItem to="/admin" icon={Shield} label={t('nav.admin')} />
                            <SidebarItem to="/analytics" icon={BarChart3} label="Analytics" />
                            </>
                        )}
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-100 dark:border-slate-700">
                    <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-100 dark:border-slate-600 mb-2">
                        <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-300 overflow-hidden border-2 border-white dark:border-slate-500 shadow-sm">
                            <User size={20} />
                        </div>
                        <div className="overflow-hidden flex-1">
                            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{user?.email?.split('@')[0]}</p>
                            <p className="text-xs text-slate-500 truncate font-medium">
                                {user?.is_admin ? t('nav.admin') : t('billing.freePlan', 'Free Plan')}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={toggleLanguage}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 dark:text-slate-400 dark:hover:text-primary-400 dark:hover:bg-primary-900/30 rounded-lg transition-colors font-medium border border-slate-200 dark:border-slate-700"
                            title={t('settings.language')}
                        >
                            <Globe size={16} />
                            {i18n.language.toUpperCase()}
                        </button>
                        <button
                            onClick={toggleTheme}
                            className="flex items-center justify-center px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 dark:text-slate-400 dark:hover:text-primary-400 dark:hover:bg-primary-900/30 rounded-lg transition-colors font-medium border border-slate-200 dark:border-slate-700"
                            title={theme === 'dark' ? t('theme.light') : t('theme.dark')}
                        >
                            {theme === 'dark' ? <Sun size={16} className="text-amber-400" /> : <Moon size={16} />}
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:text-slate-400 dark:hover:text-rose-400 dark:hover:bg-rose-900/30 rounded-lg transition-colors font-medium"
                            aria-label={t('nav.logout') || 'Logout'}
                        >
                            <LogOut size={16} aria-hidden="true" />
                            {t('nav.logout')}
                        </button>
                    </div>
                    {/* Legal Links */}
                    <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 flex flex-wrap justify-center gap-x-3 gap-y-1 text-xs text-slate-500">
                        <a href="/despre-noi" className="hover:text-primary-600 transition-colors">
                            {i18n.language === 'ro' ? 'Despre noi' : 'About'}
                        </a>
                        <span>•</span>
                        <a href="/contact" className="hover:text-primary-600 transition-colors">
                            Contact
                        </a>
                        <span>•</span>
                        <a href="/terms" className="hover:text-primary-600 transition-colors">
                            {i18n.language === 'ro' ? 'Termeni' : 'Terms'}
                        </a>
                        <span>•</span>
                        <a href="/privacy" className="hover:text-primary-600 transition-colors">
                            {i18n.language === 'ro' ? 'Confidențialitate' : 'Privacy'}
                        </a>
                    </div>
                </div>
            </aside>}

            {/* Main Content Area */}
            <main ref={mainRef} className="flex-1 overflow-y-auto relative scroll-smooth">
                {/* Top Header for Mobile & Title */}
                <header className="sticky top-0 z-20 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 px-4 py-3 flex items-center justify-between md:hidden print:hidden" role="banner">
                    <button
                        onClick={() => setMobileMenuOpen(true)}
                        className="min-h-11 min-w-11 flex items-center justify-center text-slate-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors -ml-1"
                        aria-label={t('nav.openMenu') || 'Open menu'}
                        aria-expanded={mobileMenuOpen}
                    >
                        <Menu size={22} aria-hidden="true" />
                    </button>
                    <span className="font-bold text-slate-800 dark:text-slate-100 truncate max-w-[180px]">
                        {t(PAGE_TITLE_MAP[location.pathname] || PAGE_TITLE_MAP['/']) || 'Analize.online'}
                    </span>
                    <button
                        onClick={() => navigate('/settings')}
                        className="min-h-11 min-w-11 flex items-center justify-center text-slate-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        aria-label={t('nav.notifications') || 'Notifications'}
                        title={t('nav.notifications') || 'Notifications'}
                    >
                        <Bell size={20} aria-hidden="true" />
                    </button>
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
                        <aside className="absolute left-0 top-0 h-full w-72 max-w-[calc(100vw-3rem)] bg-white dark:bg-slate-800 shadow-xl flex flex-col animate-in slide-in-from-left duration-300">
                            <div className="p-6 pb-4 flex-1 overflow-y-auto min-h-0">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3 text-primary-600">
                                        <div className="p-2.5 bg-primary-100 rounded-xl">
                                            <HeartPulse size={28} className="text-primary-600" />
                                        </div>
                                        <span className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100">Analize<span className="text-primary-500">.online</span></span>
                                    </div>
                                    <button
                                        onClick={closeMobileMenu}
                                        className="min-h-11 min-w-11 flex items-center justify-center text-slate-500 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                                        aria-label={t('nav.closeMenu') || 'Close menu'}
                                    >
                                        <X size={20} aria-hidden="true" />
                                    </button>
                                </div>

                                <div className="text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-4 px-2">Menu</div>
                                <nav className="space-y-1.5">
                                    <SidebarItem to="/" icon={LayoutDashboard} label={t('nav.dashboard')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/documents" icon={FileText} label={t('nav.documents')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/biomarkers" icon={Activity} label={t('nav.biomarkers')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/health" icon={Brain} label={t('nav.doctorAI')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/screenings" icon={ClipboardList} label={t('nav.screenings')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/lifestyle" icon={Leaf} label={t('nav.lifestyle')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/medications" icon={Pill} label={t('nav.medications')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/family" icon={Users} label={t('nav.family') || (i18n.language === 'ro' ? 'Familia Mea' : 'My Family')} onClick={closeMobileMenu} />
                                </nav>
                                <hr className="my-4 mx-2 border-t-2 border-slate-200 dark:border-slate-600" role="separator" />
                                <div className="text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-4 px-2">{t('nav.settings')}</div>
                                <nav className="space-y-1.5">
                                    <SidebarItem to="/profile" icon={User} label={t('nav.profile')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/linked-accounts" icon={LinkIcon} label={t('nav.linkedAccounts')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/settings" icon={Settings2} label={t('nav.settingsTitle')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/billing" icon={CreditCard} label={t('nav.billing')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/referral" icon={Gift} label={t('nav.referral')} onClick={closeMobileMenu} />
                                    <SidebarItem to="/support" icon={MessageSquare} label={t('nav.support')} onClick={closeMobileMenu} />
                                    {user?.is_admin && (
                                        <>
                                        <SidebarItem to="/admin" icon={Shield} label={t('nav.admin')} onClick={closeMobileMenu} />
                                        <SidebarItem to="/analytics" icon={BarChart3} label="Analytics" onClick={closeMobileMenu} />
                                        </>
                                    )}
                                </nav>
                            </div>

                            <div className="shrink-0 p-4 border-t border-slate-100 dark:border-slate-700">
                                <div className="flex items-center gap-3 p-2 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-100 dark:border-slate-600 mb-2">
                                    <div className="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-300 overflow-hidden border-2 border-white dark:border-slate-500 shadow-sm">
                                        <User size={18} />
                                    </div>
                                    <div className="overflow-hidden flex-1">
                                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{user?.email?.split('@')[0]}</p>
                                        <p className="text-xs text-slate-500 truncate font-medium">
                                            {user?.is_admin ? t('nav.admin') : t('billing.freePlan', 'Free Plan')}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => { toggleLanguage(); closeMobileMenu(); }}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 dark:text-slate-400 dark:hover:text-primary-400 dark:hover:bg-primary-900/30 rounded-lg transition-colors font-medium border border-slate-200 dark:border-slate-700"
                                        title={t('settings.language')}
                                        aria-label={t('settings.language') || 'Change language'}
                                    >
                                        <Globe size={16} aria-hidden="true" />
                                        {i18n.language.toUpperCase()}
                                    </button>
                                    <button
                                        onClick={() => { toggleTheme(); closeMobileMenu(); }}
                                        className="flex items-center justify-center px-3 py-2 text-sm text-slate-500 hover:text-primary-600 hover:bg-primary-50 dark:text-slate-400 dark:hover:text-primary-400 dark:hover:bg-primary-900/30 rounded-lg transition-colors font-medium border border-slate-200 dark:border-slate-700"
                                        title={theme === 'dark' ? t('theme.light') : t('theme.dark')}
                                        aria-label={theme === 'dark' ? (t('theme.light') || 'Light mode') : (t('theme.dark') || 'Dark mode')}
                                    >
                                        {theme === 'dark' ? <Sun size={16} className="text-amber-400" aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
                                    </button>
                                    <button
                                        onClick={() => { handleLogout(); closeMobileMenu(); }}
                                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:text-slate-400 dark:hover:text-rose-400 dark:hover:bg-rose-900/30 rounded-lg transition-colors font-medium"
                                        aria-label={t('nav.logout') || 'Logout'}
                                    >
                                        <LogOut size={16} aria-hidden="true" />
                                        <span>{t('nav.logout')}</span>
                                    </button>
                                </div>
                            </div>
                        </aside>
                    </div>
                )}

                {/* Offline Indicator */}
                {isOffline && (
                    <div className="sticky top-0 md:top-0 z-30 bg-amber-500 text-white text-center py-2 px-4 text-sm font-medium flex items-center justify-center gap-2">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                        {t('common.offlineMessage')}
                    </div>
                )}

                <div id="main-content" className="relative z-0 max-w-7xl mx-auto p-4 pb-28 md:p-8 md:pb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
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
                                    aria-label={t('common.close') || 'Close'}
                                >
                                    <X size={18} aria-hidden="true" />
                                </button>
                            </div>
                        </div>
                    )}

                    <TrialBanner />

                    {/* Dynamic Page Header */}
                    <div className="mb-4 md:mb-8">
                        <h1 className="text-xl md:text-3xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">{getPageTitle()}</h1>
                        <div className="h-1 w-20 bg-primary-500 rounded-full mt-2 opacity-20 hidden md:block"></div>
                    </div>

                    {children}
                </div>
                {/* Scroll affordance gradient */}
                <div
                    className={cn(
                        "pointer-events-none fixed bottom-16 md:bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-slate-50 dark:from-slate-900 to-transparent z-10 transition-opacity duration-300 md:hidden print:hidden",
                        showScrollGradient ? "opacity-100" : "opacity-0"
                    )}
                />
            </main>

            {/* Mobile Bottom Navigation */}
            <nav id="bottom-nav" className="fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 md:hidden print:hidden safe-bottom" aria-label={t('nav.mobileNav') || 'Mobile navigation'} role="navigation">
                <div className="flex items-stretch justify-around pb-[env(safe-area-inset-bottom)]">
                    <BottomNavItem to="/" icon={LayoutDashboard} label={t('nav.dashboard')} />
                    <BottomNavItem to="/biomarkers" icon={FlaskConical} label={t('nav.biomarkers')} />
                    <BottomNavItem to="/documents" icon={FileText} label={t('nav.documents')} />
                    <BottomNavItem to="/health" icon={Stethoscope} label={t('nav.doctorAI')} />
                    <BottomNavItem to="/profile" icon={User} label={t('nav.profile')} />
                </div>
            </nav>

            {/* Feedback Button - Only show for authenticated users */}
            <div className="print:hidden">
                <FeedbackButton />
            </div>

            {/* Vault Unlock Modal - Shows when session expired but JWT still valid */}
            <VaultUnlockModal />
        </div>
    );
};

export default Layout;
