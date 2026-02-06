import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Cookie, X, Settings, Check } from 'lucide-react';

const COOKIE_CONSENT_KEY = 'cookie_consent';
const COOKIE_PREFERENCES_KEY = 'cookie_preferences';

const CookieConsent = () => {
    const { t, i18n } = useTranslation();
    const [showBanner, setShowBanner] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [preferences, setPreferences] = useState({
        essential: true, // Always required
        analytics: false,
        marketing: false
    });

    useEffect(() => {
        // Check if user has already made a choice
        const consent = localStorage.getItem(COOKIE_CONSENT_KEY);
        if (!consent) {
            // Small delay to avoid flash on page load
            const timer = setTimeout(() => setShowBanner(true), 500);
            return () => clearTimeout(timer);
        } else {
            // Load saved preferences
            const saved = localStorage.getItem(COOKIE_PREFERENCES_KEY);
            if (saved) {
                try {
                    setPreferences(JSON.parse(saved));
                } catch (e) {
                    // Ignore parse errors
                }
            }
        }
    }, []);

    const saveConsent = (prefs) => {
        localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
        localStorage.setItem(COOKIE_PREFERENCES_KEY, JSON.stringify(prefs));
        setPreferences(prefs);
        setShowBanner(false);
        setShowSettings(false);
    };

    const acceptAll = () => {
        saveConsent({
            essential: true,
            analytics: true,
            marketing: true
        });
    };

    const acceptEssential = () => {
        saveConsent({
            essential: true,
            analytics: false,
            marketing: false
        });
    };

    const savePreferences = () => {
        saveConsent(preferences);
    };

    if (!showBanner) return null;

    return (
        <>
            {/* Backdrop for settings modal */}
            {showSettings && (
                <div
                    className="fixed inset-0 bg-black/50 z-[9998]"
                    onClick={() => setShowSettings(false)}
                />
            )}

            {/* Settings Modal */}
            {showSettings && (
                <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-2xl shadow-2xl z-[9999] p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-slate-800">
                            {t('cookies.settings')}
                        </h3>
                        <button
                            onClick={() => setShowSettings(false)}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="space-y-4 mb-6">
                        {/* Essential cookies - always on */}
                        <div className="flex items-start justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                                <p className="font-medium text-slate-700">{t('cookies.essential')}</p>
                                <p className="text-sm text-slate-500">{t('cookies.essentialDesc')}</p>
                            </div>
                            <div className="flex items-center h-6">
                                <div className="w-10 h-5 bg-primary-500 rounded-full flex items-center justify-end px-0.5">
                                    <div className="w-4 h-4 bg-white rounded-full shadow"></div>
                                </div>
                            </div>
                        </div>

                        {/* Analytics cookies */}
                        <div className="flex items-start justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                                <p className="font-medium text-slate-700">{t('cookies.analytics')}</p>
                                <p className="text-sm text-slate-500">{t('cookies.analyticsDesc')}</p>
                            </div>
                            <button
                                onClick={() => setPreferences(p => ({ ...p, analytics: !p.analytics }))}
                                className={`w-10 h-5 rounded-full flex items-center px-0.5 transition-colors ${
                                    preferences.analytics ? 'bg-primary-500 justify-end' : 'bg-slate-300 justify-start'
                                }`}
                            >
                                <div className="w-4 h-4 bg-white rounded-full shadow"></div>
                            </button>
                        </div>

                        {/* Marketing cookies */}
                        <div className="flex items-start justify-between p-3 bg-slate-50 rounded-lg">
                            <div>
                                <p className="font-medium text-slate-700">{t('cookies.marketing')}</p>
                                <p className="text-sm text-slate-500">{t('cookies.marketingDesc')}</p>
                            </div>
                            <button
                                onClick={() => setPreferences(p => ({ ...p, marketing: !p.marketing }))}
                                className={`w-10 h-5 rounded-full flex items-center px-0.5 transition-colors ${
                                    preferences.marketing ? 'bg-primary-500 justify-end' : 'bg-slate-300 justify-start'
                                }`}
                            >
                                <div className="w-4 h-4 bg-white rounded-full shadow"></div>
                            </button>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={acceptEssential}
                            className="flex-1 px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                        >
                            {t('cookies.essentialOnly')}
                        </button>
                        <button
                            onClick={savePreferences}
                            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            <Check size={16} />
                            {t('cookies.savePreferences')}
                        </button>
                    </div>
                </div>
            )}

            {/* Cookie Banner */}
            <div className="fixed bottom-0 left-0 right-0 z-[9997] p-4 animate-in slide-in-from-bottom duration-300">
                <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 md:p-6">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                        <div className="flex items-start gap-3 flex-1">
                            <div className="p-2 bg-primary-50 rounded-lg shrink-0">
                                <Cookie size={24} className="text-primary-600" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800 mb-1">
                                    {t('cookies.title')}
                                </h3>
                                <p className="text-sm text-slate-600">
                                    {t('cookies.description')}{' '}
                                    <a
                                        href="/privacy"
                                        target="_blank"
                                        className="text-primary-600 hover:text-primary-700 underline"
                                    >
                                        {t('cookies.learnMore')}
                                    </a>
                                </p>
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-2 md:shrink-0">
                            <button
                                onClick={() => setShowSettings(true)}
                                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                            >
                                <Settings size={16} />
                                {t('cookies.customize')}
                            </button>
                            <button
                                onClick={acceptEssential}
                                className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                            >
                                {t('cookies.essentialOnly')}
                            </button>
                            <button
                                onClick={acceptAll}
                                className="px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors"
                            >
                                {t('cookies.acceptAll')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default CookieConsent;
