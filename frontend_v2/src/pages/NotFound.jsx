import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, AlertTriangle } from 'lucide-react';

const NotFound = () => {
    const { t } = useTranslation();

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
            <div className="text-center max-w-md">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full mb-6">
                    <AlertTriangle className="w-10 h-10 text-red-500" />
                </div>
                <h1 className="text-6xl font-bold text-slate-800 mb-4">404</h1>
                <h2 className="text-2xl font-semibold text-slate-700 mb-4">
                    {t('errors.pageNotFound') || 'Page Not Found'}
                </h2>
                <p className="text-slate-500 mb-8">
                    {t('errors.pageNotFoundDescription') || 'The page you are looking for does not exist or has been moved.'}
                </p>
                <Link
                    to="/"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors font-medium"
                >
                    <Home size={18} />
                    {t('common.backToHome') || 'Back to Home'}
                </Link>
            </div>
        </div>
    );
};

export default NotFound;
