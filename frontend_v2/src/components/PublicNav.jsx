import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HeartPulse, Globe } from 'lucide-react';

/**
 * Public navigation bar for unauthenticated pages (blog, biomarker, etc.)
 * Matches the Home page navbar style.
 */
export default function PublicNav() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'ro' ? 'en' : 'ro');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-lg z-50 border-b border-slate-100">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center">
            <HeartPulse className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-800">Analize.Online</span>
        </Link>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <Globe size={14} />
            {i18n.language.toUpperCase()}
          </button>
          <Link to="/biomarker" className="text-slate-600 hover:text-slate-800 font-medium hidden md:block">
            {isRo ? 'Biomarkeri' : 'Biomarkers'}
          </Link>
          <Link to="/blog" className="text-slate-600 hover:text-slate-800 font-medium hidden md:block">
            Blog
          </Link>
          <Link to="/pricing" className="text-slate-600 hover:text-slate-800 font-medium hidden sm:block">
            {isRo ? 'Prețuri' : 'Pricing'}
          </Link>
          <Link
            to="/login"
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md shadow-cyan-500/20"
          >
            {isRo ? 'Înregistrare' : 'Sign Up'}
          </Link>
        </div>
      </div>
    </nav>
  );
}
