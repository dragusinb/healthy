import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, ArrowRight, Activity, FlaskConical, Heart, Droplets, Pill, Flame, TestTube } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import biomarkers from '../data/biomarkers-reference.json';

const CATEGORY_ICONS = {
  'Hematologie': Activity,
  'Biochimie': FlaskConical,
  'Enzime hepatice': TestTube,
  'Tiroidă': Droplets,
  'Vitamine': Pill,
  'Markeri inflamatori': Flame,
  'Coagulare': Heart,
  'Hormoni': Droplets,
  'Urină': Droplets,
};

export default function BiomarkerIndex() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';
  const [search, setSearch] = useState('');

  usePageTitle(null, null, {
    title: isRo
      ? 'Ghid Biomarkeri — Valori normale și interpretare | Analize.Online'
      : 'Biomarker Guide — Normal values and interpretation | Analize.Online',
    description: isRo
      ? 'Ghid complet pentru biomarkerii din analizele de sânge: hemoglobina, colesterol, glicemie, TGO, TGP, TSH și alții. Valori normale, cauze valori crescute/scăzute.'
      : 'Complete guide to blood test biomarkers: hemoglobin, cholesterol, glucose, AST, ALT, TSH and more. Normal values, causes of high/low values.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: isRo ? 'Ghid Biomarkeri' : 'Biomarker Guide',
    description: isRo
      ? 'Ghid complet pentru interpretarea analizelor de sânge'
      : 'Complete guide to interpreting blood tests',
    url: 'https://analize.online/biomarker',
    publisher: { '@type': 'Organization', name: 'Analize.Online' },
    numberOfItems: biomarkers.length,
  });

  // Group by category
  const categories = useMemo(() => {
    const catKey = isRo ? 'category_ro' : 'category_en';
    const map = {};
    biomarkers.forEach(b => {
      const cat = b[catKey] || 'Altele';
      if (!map[cat]) map[cat] = [];
      map[cat].push(b);
    });
    return Object.entries(map);
  }, [isRo]);

  // Filter
  const filtered = useMemo(() => {
    if (!search.trim()) return null;
    const q = search.toLowerCase();
    return biomarkers.filter(b =>
      b.name_ro.toLowerCase().includes(q) ||
      b.name_en.toLowerCase().includes(q) ||
      (b.aliases_ro || []).some(a => a.toLowerCase().includes(q)) ||
      b.slug.includes(q)
    );
  }, [search]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero */}
      <section className="bg-gradient-to-br from-teal-600 to-cyan-700 text-white py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            {isRo ? 'Ghid Biomarkeri' : 'Biomarker Guide'}
          </h1>
          <p className="text-lg text-teal-100 mb-8 max-w-2xl mx-auto">
            {isRo
              ? 'Înțelege ce înseamnă fiecare valoare din analizele tale de sânge. Valori normale, cauze pentru valori crescute sau scăzute.'
              : 'Understand what each value in your blood tests means. Normal ranges, causes for high or low values.'}
          </p>
          <div className="relative max-w-md mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={isRo ? 'Caută un biomarker (ex: hemoglobina, colesterol, TSH)...' : 'Search a biomarker (e.g., hemoglobin, cholesterol, TSH)...'}
              className="w-full pl-12 pr-4 py-3 rounded-xl text-slate-800 bg-white border-0 shadow-lg focus:ring-2 focus:ring-teal-300 outline-none"
            />
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Search results */}
        {filtered ? (
          <div>
            <h2 className="text-lg font-semibold text-slate-600 mb-4">
              {filtered.length} {isRo ? 'rezultate' : 'results'}
            </h2>
            {filtered.length === 0 ? (
              <p className="text-slate-500">{isRo ? 'Niciun biomarker găsit.' : 'No biomarkers found.'}</p>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map(b => <BiomarkerCard key={b.slug} b={b} isRo={isRo} />)}
              </div>
            )}
          </div>
        ) : (
          /* Category groups */
          categories.map(([cat, items]) => {
            const Icon = CATEGORY_ICONS[cat] || FlaskConical;
            return (
              <div key={cat} className="mb-12">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-teal-50 rounded-xl flex items-center justify-center">
                    <Icon className="text-teal-600" size={20} />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">{cat}</h2>
                  <span className="text-sm text-slate-400">({items.length})</span>
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map(b => <BiomarkerCard key={b.slug} b={b} isRo={isRo} />)}
                </div>
              </div>
            );
          })
        )}

        {/* CTA */}
        <section className="mt-16 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 md:p-12 text-white text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            {isRo
              ? 'Ai analize recente? Încarcă-le gratuit.'
              : 'Have recent lab results? Upload them for free.'}
          </h2>
          <p className="text-teal-100 mb-6 max-w-xl mx-auto">
            {isRo
              ? 'Conectează-ți contul de la Regina Maria, Synevo, MedLife sau Sanador. Primești interpretare personalizată de la specialiști AI, plan nutrițional și program de exerciții — bazate pe valorile tale reale.'
              : 'Connect your Regina Maria, Synevo, MedLife or Sanador account. Get personalized interpretation from AI specialists, nutrition plan and exercise program — based on your real values.'}
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

function BiomarkerCard({ b, isRo }) {
  return (
    <Link
      to={`/biomarker/${b.slug}`}
      className="block bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md hover:border-teal-200 transition-all group"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-bold text-slate-800 group-hover:text-teal-700 transition-colors">
            {isRo ? b.name_ro : b.name_en}
          </h3>
          {b.aliases_ro?.length > 0 && (
            <p className="text-xs text-slate-400 mt-0.5">{b.aliases_ro.join(' / ')}</p>
          )}
        </div>
        <span className="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded">{b.unit}</span>
      </div>
      <p className="text-sm text-slate-500 mt-2 line-clamp-2">
        {isRo ? b.what_ro : b.what_en}
      </p>
      <div className="flex items-center gap-1 mt-3 text-teal-600 text-sm font-medium group-hover:gap-2 transition-all">
        {isRo ? 'Vezi detalii' : 'View details'}
        <ArrowRight size={14} />
      </div>
    </Link>
  );
}
