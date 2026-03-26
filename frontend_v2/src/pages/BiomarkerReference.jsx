import React from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, TrendingUp, TrendingDown, Info, ArrowUpRight } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import biomarkers from '../data/biomarkers-reference.json';

export default function BiomarkerReference() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';

  const biomarker = biomarkers.find(b => b.slug === slug);

  if (!biomarker) {
    return <Navigate to="/biomarker" replace />;
  }

  const name = isRo ? biomarker.name_ro : biomarker.name_en;
  const category = isRo ? biomarker.category_ro : biomarker.category_en;

  usePageTitle(null, null, {
    title: isRo
      ? `${biomarker.name_ro} — Valori normale, cauze crescute/scăzute | Analize.Online`
      : `${biomarker.name_en} — Normal values, high/low causes | Analize.Online`,
    description: isRo ? biomarker.meta_ro : biomarker.meta_en,
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'MedicalWebPage',
    name: isRo
      ? `${biomarker.name_ro} — Valori normale și interpretare`
      : `${biomarker.name_en} — Normal values and interpretation`,
    about: {
      '@type': 'MedicalTest',
      name: biomarker.name_en,
    },
    url: `https://analize.online/biomarker/${biomarker.slug}`,
    inLanguage: isRo ? 'ro' : 'en',
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: isRo ? 'Acasă' : 'Home', item: 'https://analize.online' },
        { '@type': 'ListItem', position: 2, name: isRo ? 'Biomarkeri' : 'Biomarkers', item: 'https://analize.online/biomarker' },
        { '@type': 'ListItem', position: 3, name: name },
      ],
    },
  });

  const related = (biomarker.related || [])
    .map(slug => biomarkers.find(b => b.slug === slug))
    .filter(Boolean);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Breadcrumb */}
      <div className="bg-white border-b border-slate-100">
        <div className="max-w-4xl mx-auto px-6 py-3">
          <nav className="flex items-center gap-2 text-sm text-slate-500">
            <Link to="/" className="hover:text-teal-600">Analize.Online</Link>
            <span>/</span>
            <Link to="/biomarker" className="hover:text-teal-600">
              {isRo ? 'Biomarkeri' : 'Biomarkers'}
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">{name}</span>
          </nav>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Back link */}
        <Link to="/biomarker" className="inline-flex items-center gap-2 text-sm text-teal-600 hover:text-teal-800 mb-6">
          <ArrowLeft size={16} />
          {isRo ? 'Toți biomarkerii' : 'All biomarkers'}
        </Link>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-sm text-teal-600 bg-teal-50 px-3 py-1 rounded-full font-medium">{category}</span>
            {biomarker.unit && <span className="text-sm text-slate-400">({biomarker.unit})</span>}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800 mb-2">{name}</h1>
          {biomarker.aliases_ro?.length > 0 && (
            <p className="text-slate-400">
              {isRo ? 'Cunoscut și ca:' : 'Also known as:'} {biomarker.aliases_ro.join(', ')}
            </p>
          )}
        </div>

        {/* What it measures */}
        <section className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Info size={20} className="text-teal-600" />
            <h2 className="text-xl font-bold text-slate-800">
              {isRo ? 'Ce măsoară?' : 'What does it measure?'}
            </h2>
          </div>
          <p className="text-slate-600 leading-relaxed">
            {isRo ? biomarker.what_ro : biomarker.what_en}
          </p>
        </section>

        {/* Reference ranges */}
        <section className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
          <h2 className="text-xl font-bold text-slate-800 mb-4">
            {isRo ? 'Valori de referință' : 'Reference ranges'}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 pr-4 text-sm font-semibold text-slate-500">
                    {isRo ? 'Grup' : 'Group'}
                  </th>
                  <th className="text-left py-2 text-sm font-semibold text-slate-500">
                    {isRo ? 'Interval normal' : 'Normal range'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {(biomarker.ranges || []).map((r, i) => (
                  <tr key={i} className="border-b border-slate-50">
                    <td className="py-3 pr-4 text-slate-600">{isRo ? r.group_ro : r.group_en}</td>
                    <td className="py-3 font-mono font-semibold text-slate-800">{r.range}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* High values */}
        <section className="bg-red-50 rounded-2xl border border-red-100 p-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={20} className="text-red-600" />
            <h2 className="text-xl font-bold text-red-800">
              {isRo ? `${name} crescut — ce înseamnă?` : `High ${name} — what does it mean?`}
            </h2>
          </div>
          <p className="text-red-900/80 leading-relaxed">
            {isRo ? biomarker.high_ro : biomarker.high_en}
          </p>
        </section>

        {/* Low values */}
        <section className="bg-blue-50 rounded-2xl border border-blue-100 p-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown size={20} className="text-blue-600" />
            <h2 className="text-xl font-bold text-blue-800">
              {isRo ? `${name} scăzut — ce înseamnă?` : `Low ${name} — what does it mean?`}
            </h2>
          </div>
          <p className="text-blue-900/80 leading-relaxed">
            {isRo ? biomarker.low_ro : biomarker.low_en}
          </p>
        </section>

        {/* Related biomarkers */}
        {related.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl font-bold text-slate-800 mb-4">
              {isRo ? 'Biomarkeri asociați' : 'Related biomarkers'}
            </h2>
            <div className="flex flex-wrap gap-3">
              {related.map(r => (
                <Link
                  key={r.slug}
                  to={`/biomarker/${r.slug}`}
                  className="inline-flex items-center gap-1 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-teal-300 hover:text-teal-700 transition-colors"
                >
                  {isRo ? r.name_ro : r.name_en}
                  <ArrowUpRight size={14} />
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* CTA */}
        <section className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-3">
            {isRo
              ? `Vrei să știi exact cum stai cu ${biomarker.name_ro.toLowerCase()}?`
              : `Want to know exactly where you stand with ${biomarker.name_en.toLowerCase()}?`}
          </h2>
          <p className="text-teal-100 mb-6 max-w-lg mx-auto">
            {isRo
              ? 'Încarcă analizele tale gratuit pe Analize.Online. Primești interpretare personalizată de la specialiști AI, plan nutrițional cu rețete românești și program de exerciții.'
              : 'Upload your lab results for free on Analize.Online. Get personalized interpretation from AI specialists, nutrition plan with Romanian recipes and exercise program.'}
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-semibold hover:bg-teal-50 transition-colors"
          >
            {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
            <ArrowRight size={18} />
          </Link>
        </section>
      </div>
    </div>
  );
}
