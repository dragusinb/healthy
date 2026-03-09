import React from 'react';
import { useTranslation } from 'react-i18next';
import usePageTitle from '../hooks/usePageTitle';
import FamilyDashboard from '../components/FamilyDashboard';

export default function Family() {
  const { t, i18n } = useTranslation();
  usePageTitle('nav.family', 'My Family');
  const isRomanian = i18n.language === 'ro';

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800">
          {isRomanian ? 'Familia Mea' : 'My Family'}
        </h2>
        <p className="text-slate-600">
          {isRomanian
            ? 'Vezi starea de sănătate a membrilor familiei'
            : 'View your family members health status'}
        </p>
      </div>

      {/* Family dashboard */}
      <FamilyDashboard />
    </div>
  );
}
