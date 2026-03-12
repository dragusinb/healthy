import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Download, X } from 'lucide-react';

export default function InstallBanner() {
  const { t } = useTranslation();
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Don't show if already installed or dismissed recently
    const dismissed = localStorage.getItem('pwaInstallDismissed');
    if (dismissed) {
      const dismissedAt = parseInt(dismissed, 10);
      // Don't show for 7 days after dismissal
      if (Date.now() - dismissedAt < 7 * 24 * 60 * 60 * 1000) return;
    }

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) return;

    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Show banner after 2nd visit
      const visits = parseInt(localStorage.getItem('pwaVisitCount') || '0', 10) + 1;
      localStorage.setItem('pwaVisitCount', String(visits));
      if (visits >= 2) {
        setShowBanner(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShowBanner(false);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShowBanner(false);
    localStorage.setItem('pwaInstallDismissed', String(Date.now()));
  };

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 bg-white border border-slate-200 rounded-2xl shadow-2xl p-4 flex items-center gap-3 animate-in slide-in-from-bottom-8 duration-500">
      <div className="p-2.5 bg-emerald-100 rounded-xl shrink-0">
        <Download size={22} className="text-emerald-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-800 text-sm">{t('pwa.installTitle')}</p>
        <p className="text-xs text-slate-500 mt-0.5">{t('pwa.installDescription')}</p>
      </div>
      <button
        onClick={handleInstall}
        className="px-3 py-1.5 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors shrink-0"
      >
        {t('pwa.install')}
      </button>
      <button
        onClick={handleDismiss}
        className="p-1.5 text-slate-500 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors shrink-0"
        aria-label={t('common.close') || 'Dismiss'}
      >
        <X size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
