import React from 'react';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const PageLoader = () => {
    const { t } = useTranslation();
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800" role="status" aria-label={t('common.loading') || 'Loading'}>
            {/* Skeleton header */}
            <div className="h-14 bg-white/60 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 animate-pulse" />
            {/* Skeleton body */}
            <div className="max-w-4xl mx-auto p-6 space-y-6 mt-4">
                <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded-lg animate-pulse" />
                <div className="space-y-3">
                    <div className="h-4 w-full bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                    <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                    <div className="h-4 w-5/6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[1,2,3,4].map(i => (
                        <div key={i} className="h-24 bg-slate-200 dark:bg-slate-700 rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
            {/* Centered spinner overlay */}
            <div className="fixed inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
                    <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-3" />
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">{t('common.loading')}</p>
                </div>
            </div>
        </div>
    );
};

export default PageLoader;
