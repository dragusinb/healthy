import React from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, TrendingUp, TrendingDown, Info, ArrowUpRight, Brain, Utensils, Dumbbell, ShoppingCart, BookOpen } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import biomarkers from '../data/biomarkers-reference.json';

const CATEGORY_IMAGES = {
  'Hematologie': 'photo-1579684385127-1ef15d508118',
  'Biochimie': 'photo-1582719508461-905c673771fd',
  'Enzime hepatice': 'photo-1559757148-5c350d0d3c56',
  'Tiroidă': 'photo-1576091160399-112ba8d25d1d',
  'Vitamine': 'photo-1512621776951-a57141f2eefd',
  'Markeri inflamatori': 'photo-1631549916768-4f7d9acf91c2',
  'Coagulare': 'photo-1579684385127-1ef15d508118',
  'Hormoni': 'photo-1576091160399-112ba8d25d1d',
  'Urină': 'photo-1582719508461-905c673771fd',
  // English
  'Hematology': 'photo-1579684385127-1ef15d508118',
  'Biochemistry': 'photo-1582719508461-905c673771fd',
  'Liver Enzymes': 'photo-1559757148-5c350d0d3c56',
  'Thyroid': 'photo-1576091160399-112ba8d25d1d',
  'Vitamins': 'photo-1512621776951-a57141f2eefd',
  'Inflammatory Markers': 'photo-1631549916768-4f7d9acf91c2',
  'Coagulation': 'photo-1579684385127-1ef15d508118',
  'Hormones': 'photo-1576091160399-112ba8d25d1d',
  'Urine': 'photo-1582719508461-905c673771fd',
};

export default function BiomarkerReference() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';

  const biomarker = biomarkers.find(b => b.slug === slug);
  if (!biomarker) return <Navigate to="/biomarker" replace />;

  const name = isRo ? biomarker.name_ro : biomarker.name_en;
  const category = isRo ? biomarker.category_ro : biomarker.category_en;
  const imgId = CATEGORY_IMAGES[category] || 'photo-1579684385127-1ef15d508118';

  usePageTitle(null, null, {
    title: isRo
      ? `${biomarker.name_ro} — Valori normale, cauze crescute/scăzute | Analize.Online`
      : `${biomarker.name_en} — Normal values, high/low causes | Analize.Online`,
    description: isRo ? biomarker.meta_ro : biomarker.meta_en,
  });

  useJsonLd({
    '@context': 'https://schema.org', '@type': 'MedicalWebPage',
    name: `${name} — ${isRo ? 'Valori normale și interpretare' : 'Normal values and interpretation'}`,
    about: { '@type': 'MedicalTest', name: biomarker.name_en },
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

  const related = (biomarker.related || []).map(s => biomarkers.find(b => b.slug === s)).filter(Boolean);

  return (
    <div className="min-h-screen bg-slate-50">
      {!user && <PublicNav />}

      {/* Hero header with image */}
      <header className={`${!user ? 'pt-24' : ''} relative overflow-hidden`}>
        <div className="absolute inset-0 z-0">
          <img
            src={`https://images.unsplash.com/${imgId}?w=1600&h=400&fit=crop&auto=format`}
            alt={`${name} - ${category}`}
            className="w-full h-full object-cover"
            loading="eager"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-900/95 via-slate-900/85 to-slate-900/70" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-6 py-12">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-white/50 mb-6">
            <Link to="/" className="hover:text-white/80">Analize.Online</Link>
            <span>/</span>
            <Link to="/biomarker" className="hover:text-white/80">{isRo ? 'Biomarkeri' : 'Biomarkers'}</Link>
            <span>/</span>
            <span className="text-white/80">{name}</span>
          </nav>

          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs font-semibold bg-white/20 px-3 py-1 rounded-full text-white">
              {category}
            </span>
            {biomarker.unit && (
              <span className="text-xs bg-white/10 px-3 py-1 rounded-full text-white/70 font-mono">
                {biomarker.unit}
              </span>
            )}
          </div>
          <h1 className="text-3xl md:text-5xl font-bold text-white mb-3">{name}</h1>
          {biomarker.aliases_ro?.length > 0 && (
            <p className="text-white/50 text-lg">
              {biomarker.aliases_ro.join(' / ')}
            </p>
          )}
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 -mt-4 relative z-20">
        {/* What it measures */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-teal-50 rounded-xl flex items-center justify-center">
              <Info size={20} className="text-teal-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-800">
              {isRo ? 'Ce măsoară?' : 'What does it measure?'}
            </h2>
          </div>
          <p className="text-slate-600 leading-relaxed text-lg">
            {isRo ? biomarker.what_ro : biomarker.what_en}
          </p>
        </section>

        {/* Reference ranges */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-6">
          <div className="p-8 pb-4">
            <h2 className="text-xl font-bold text-slate-800">
              {isRo ? 'Valori de referință' : 'Reference ranges'}
            </h2>
          </div>
          <div className="px-8 pb-8">
            <div className="rounded-xl overflow-hidden border border-slate-200">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-800 text-white">
                    <th className="text-left py-3 px-5 text-sm font-semibold">
                      {isRo ? 'Grup' : 'Group'}
                    </th>
                    <th className="text-left py-3 px-5 text-sm font-semibold">
                      {isRo ? 'Interval normal' : 'Normal range'}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {(biomarker.ranges || []).map((r, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                      <td className="py-3 px-5 text-slate-700">{isRo ? r.group_ro : r.group_en}</td>
                      <td className="py-3 px-5 font-mono font-bold text-teal-700 text-lg">{r.range}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* High and Low — side by side on desktop */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* High values */}
          <section className="bg-white rounded-2xl shadow-sm border border-red-100 overflow-hidden">
            <div className="bg-gradient-to-r from-red-500 to-rose-500 p-5 flex items-center gap-3">
              <TrendingUp size={24} className="text-white" />
              <h2 className="text-lg font-bold text-white">
                {isRo ? `${name} crescut` : `High ${name}`}
              </h2>
            </div>
            <div className="p-6">
              <p className="text-slate-600 leading-relaxed">
                {isRo ? biomarker.high_ro : biomarker.high_en}
              </p>
            </div>
          </section>

          {/* Low values */}
          <section className="bg-white rounded-2xl shadow-sm border border-blue-100 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-5 flex items-center gap-3">
              <TrendingDown size={24} className="text-white" />
              <h2 className="text-lg font-bold text-white">
                {isRo ? `${name} scăzut` : `Low ${name}`}
              </h2>
            </div>
            <div className="p-6">
              <p className="text-slate-600 leading-relaxed">
                {isRo ? biomarker.low_ro : biomarker.low_en}
              </p>
            </div>
          </section>
        </div>

        {/* Related biomarkers */}
        {related.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4">
              {isRo ? 'Biomarkeri asociați' : 'Related biomarkers'}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {related.map(r => (
                <Link
                  key={r.slug}
                  to={`/biomarker/${r.slug}`}
                  className="flex items-center gap-2 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-teal-300 hover:bg-teal-50 hover:text-teal-700 transition-all group"
                >
                  <BookOpen size={14} className="text-slate-400 group-hover:text-teal-500" />
                  {isRo ? r.name_ro : r.name_en}
                  <ArrowUpRight size={12} className="ml-auto text-slate-300 group-hover:text-teal-500" />
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* CTA */}
        <section className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 md:p-10 text-white mb-6">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-1">
              <h2 className="text-xl md:text-2xl font-bold mb-2">
                {isRo
                  ? `Vrei să știi exact cum stai cu ${biomarker.name_ro.toLowerCase()}?`
                  : `Want to know exactly where you stand with ${biomarker.name_en.toLowerCase()}?`}
              </h2>
              <p className="text-teal-100">
                {isRo
                  ? 'Încarcă analizele pe Analize.Online — primești interpretare de la specialiști AI, plan nutrițional cu rețete românești și program de exerciții, bazate pe valorile tale reale.'
                  : 'Upload your results on Analize.Online — get AI specialist interpretation, nutrition plan with Romanian recipes and exercise program, based on your real values.'}
              </p>
            </div>
            <Link
              to="/login"
              className="shrink-0 inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-bold hover:bg-teal-50 transition-colors shadow-lg"
            >
              {isRo ? 'Începe Gratuit' : 'Start Free'}
              <ArrowRight size={18} />
            </Link>
          </div>
        </section>

        {/* Feature grid */}
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-8">
          <h3 className="text-lg font-bold text-slate-800 mb-5 text-center">
            {isRo ? 'Ce primești pe Analize.Online' : 'What you get on Analize.Online'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: Brain, title: isRo ? 'Specialiști AI' : 'AI Specialists', desc: isRo ? 'Cardiolog, Endocrinolog...' : 'Cardiologist, Endocrinologist...' },
              { icon: Utensils, title: isRo ? 'Rețete românești' : 'Romanian recipes', desc: isRo ? 'Plan de 7 zile personalizat' : '7-day personalized plan' },
              { icon: Dumbbell, title: isRo ? 'Plan exerciții' : 'Exercise plan', desc: isRo ? 'Adaptat profilului medical' : 'Adapted to medical profile' },
              { icon: ShoppingCart, title: isRo ? 'Listă cumpărături' : 'Grocery list', desc: isRo ? 'Gata pentru magazin' : 'Ready for the store' },
            ].map((f, i) => (
              <div key={i} className="text-center p-3">
                <div className="w-11 h-11 bg-teal-50 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <f.icon size={20} className="text-teal-600" />
                </div>
                <h4 className="font-semibold text-slate-800 text-sm">{f.title}</h4>
                <p className="text-xs text-slate-500 mt-0.5">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Back */}
        <div className="text-center pb-10">
          <Link to="/biomarker" className="inline-flex items-center gap-2 text-slate-500 hover:text-teal-600 font-medium transition-colors">
            <ArrowLeft size={16} />
            {isRo ? 'Toți biomarkerii' : 'All biomarkers'}
          </Link>
        </div>
      </div>
    </div>
  );
}
