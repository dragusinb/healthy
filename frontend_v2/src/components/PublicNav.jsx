import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HeartPulse, Globe, Menu, X } from 'lucide-react';

/**
 * Public navigation bar for unauthenticated pages (blog, biomarker, etc.)
 * Matches the Home page navbar style.
 */
export default function PublicNav() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';
  const [mobileOpen, setMobileOpen] = useState(false);

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
          <Link to="/pricing" className="text-slate-600 hover:text-slate-800 font-medium hidden md:block">
            {isRo ? 'Prețuri' : 'Pricing'}
          </Link>
          <Link
            to="/login"
            className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md shadow-cyan-500/20 hidden sm:block"
          >
            {isRo ? 'Înregistrare' : 'Sign Up'}
          </Link>
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center text-slate-600 hover:text-slate-800"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>
      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-slate-100 px-6 py-4 space-y-3">
          <Link to="/biomarker" onClick={() => setMobileOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
            {isRo ? 'Biomarkeri' : 'Biomarkers'}
          </Link>
          <Link to="/blog" onClick={() => setMobileOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
            Blog
          </Link>
          <Link to="/pricing" onClick={() => setMobileOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
            {isRo ? 'Prețuri' : 'Pricing'}
          </Link>
          <Link
            to="/login"
            onClick={() => setMobileOpen(false)}
            className="block w-full text-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md shadow-cyan-500/20"
          >
            {isRo ? 'Înregistrare' : 'Sign Up'}
          </Link>
        </div>
      )}
    </nav>
  );
}
