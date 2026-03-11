import React, { Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Crown } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import { ListSkeleton } from '../components/Skeleton';
import FamilyDashboard from '../components/FamilyDashboard';

export default function Family() {
  const { t, i18n } = useTranslation();
  usePageTitle('nav.family', 'My Family');
  const isRomanian = i18n.language === 'ro';

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-slate-600" aria-label="Breadcrumb">
        <Link to="/dashboard" className="hover:text-primary-600 transition-colors">
          {t('nav.dashboard')}
        </Link>
        <span className="mx-2">&gt;</span>
        <span className="text-slate-800 font-medium">{t('nav.family')}</span>
      </nav>

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">
            {isRomanian ? 'Familia Mea' : 'My Family'}
          </h2>
          <p className="text-slate-600">
            {isRomanian
              ? 'Gestionează și partajează datele de sănătate ale familiei'
              : 'Manage and share health data with your family'}
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <Crown size={12} />
          {t('family.premiumFeature', 'Premium feature')}
        </span>
      </div>

      {/* Family dashboard */}
      <Suspense fallback={<ListSkeleton rows={3} />}>
        <FamilyDashboard />
      </Suspense>
    </div>
  );
}
