import React from 'react';
import { useTranslation } from 'react-i18next';
import FamilyDashboard from '../components/FamilyDashboard';

export default function Family() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">
          {isRomanian ? 'Familia Mea' : 'My Family'}
        </h1>
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
