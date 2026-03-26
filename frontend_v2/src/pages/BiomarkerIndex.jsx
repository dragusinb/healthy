import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, ArrowRight, Activity, FlaskConical, Heart, Droplets, Pill, Flame, TestTube, BookOpen, Brain, Dumbbell, Utensils, ShoppingCart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import biomarkers from '../data/biomarkers-reference.json';

const CATEGORIES = {
  'Hematologie':        { icon: Activity,    color: 'from-red-500 to-rose-600',     bg: 'bg-red-50',    text: 'text-red-600',    img: 'photo-1579684385127-1ef15d508118' },
  'Biochimie':          { icon: FlaskConical, color: 'from-blue-500 to-indigo-600',  bg: 'bg-blue-50',   text: 'text-blue-600',   img: 'photo-1582719508461-905c673771fd' },
  'Enzime hepatice':    { icon: TestTube,     color: 'from-amber-500 to-orange-600', bg: 'bg-amber-50',  text: 'text-amber-600',  img: 'photo-1559757148-5c350d0d3c56' },
  'Tiroidă':            { icon: Droplets,     color: 'from-violet-500 to-purple-600',bg: 'bg-violet-50', text: 'text-violet-600', img: 'photo-1576091160399-112ba8d25d1d' },
  'Vitamine':           { icon: Pill,         color: 'from-green-500 to-emerald-600',bg: 'bg-green-50',  text: 'text-green-600',  img: 'photo-1512621776951-a57141f2eefd' },
  'Markeri inflamatori':{ icon: Flame,        color: 'from-orange-500 to-red-500',   bg: 'bg-orange-50', text: 'text-orange-600', img: 'photo-1631549916768-4f7d9acf91c2' },
  'Coagulare':          { icon: Heart,        color: 'from-pink-500 to-rose-600',    bg: 'bg-pink-50',   text: 'text-pink-600',   img: 'photo-1579684385127-1ef15d508118' },
  'Hormoni':            { icon: Droplets,     color: 'from-cyan-500 to-teal-600',    bg: 'bg-cyan-50',   text: 'text-cyan-600',   img: 'photo-1576091160399-112ba8d25d1d' },
  'Urină':              { icon: Droplets,     color: 'from-sky-500 to-blue-600',     bg: 'bg-sky-50',    text: 'text-sky-600',    img: 'photo-1582719508461-905c673771fd' },
};

// English category map
const CATEGORIES_EN = {
  'Hematology':           CATEGORIES['Hematologie'],
  'Biochemistry':         CATEGORIES['Biochimie'],
  'Liver Enzymes':        CATEGORIES['Enzime hepatice'],
  'Thyroid':              CATEGORIES['Tiroidă'],
  'Vitamins':             CATEGORIES['Vitamine'],
  'Inflammatory Markers': CATEGORIES['Markeri inflamatori'],
  'Coagulation':          CATEGORIES['Coagulare'],
  'Hormones':             CATEGORIES['Hormoni'],
  'Urine':                CATEGORIES['Urină'],
};

export default function BiomarkerIndex() {
  const { i18n } = useTranslation();
  const { user } = useAuth();
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
    '@context': 'https://schema.org', '@type': 'CollectionPage',
    name: isRo ? 'Ghid Biomarkeri' : 'Biomarker Guide',
    url: 'https://analize.online/biomarker',
    publisher: { '@type': 'Organization', name: 'Analize.Online' },
    numberOfItems: biomarkers.length,
  });

  const catKey = isRo ? 'category_ro' : 'category_en';
  const catLookup = isRo ? CATEGORIES : CATEGORIES_EN;

  const categories = useMemo(() => {
    const map = {};
    biomarkers.forEach(b => {
      const cat = b[catKey] || 'Altele';
      if (!map[cat]) map[cat] = [];
      map[cat].push(b);
    });
    return Object.entries(map);
  }, [isRo]);

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
    <div className="min-h-screen bg-slate-50">
      {!user && <PublicNav />}

      {/* Hero */}
      <section className={`bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white ${!user ? 'pt-28' : 'pt-8'} pb-16 px-6 relative overflow-hidden`}>
        <div className="absolute inset-0 opacity-5">
          <img src="https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1600&h=600&fit=crop&auto=format" alt="" className="w-full h-full object-cover" />
        </div>
        <div className="max-w-4xl mx-auto text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full text-sm mb-6">
            <BookOpen size={16} />
            {isRo ? `${biomarkers.length} biomarkeri documentați` : `${biomarkers.length} biomarkers documented`}
          </div>
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            {isRo ? 'Ghid Biomarkeri' : 'Biomarker Guide'}
          </h1>
          <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
            {isRo
              ? 'Înțelege ce înseamnă fiecare valoare din analizele tale de sânge. Valori normale pe vârstă și sex, cauze pentru valori crescute sau scăzute.'
              : 'Understand what each value in your blood tests means. Normal ranges by age and sex, causes for high or low values.'}
          </p>
          <div className="relative max-w-lg mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={isRo ? 'Caută: hemoglobina, colesterol, TSH, TGO...' : 'Search: hemoglobin, cholesterol, TSH, AST...'}
              className="w-full pl-12 pr-4 py-4 rounded-2xl text-slate-800 bg-white border-0 shadow-xl focus:ring-2 focus:ring-teal-400 outline-none text-lg"
            />
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-10">
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
                {filtered.map(b => <BiomarkerCard key={b.slug} b={b} isRo={isRo} catLookup={catLookup} catKey={catKey} />)}
              </div>
            )}
          </div>
        ) : (
          /* Categories */
          categories.map(([cat, items]) => {
            const meta = catLookup[cat] || { icon: FlaskConical, color: 'from-slate-500 to-slate-600', bg: 'bg-slate-50', text: 'text-slate-600', img: 'photo-1579684385127-1ef15d508118' };
            const Icon = meta.icon;
            return (
              <div key={cat} className="mb-12">
                {/* Category header with image */}
                <div className={`bg-gradient-to-r ${meta.color} rounded-2xl p-6 mb-6 flex items-center gap-4 relative overflow-hidden`}>
                  <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-20">
                    <img
                      src={`https://images.unsplash.com/${meta.img}?w=400&h=200&fit=crop&auto=format`}
                      alt="" className="w-full h-full object-cover" loading="lazy"
                    />
                  </div>
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <Icon className="text-white" size={24} />
                  </div>
                  <div className="relative">
                    <h2 className="text-2xl font-bold text-white">{cat}</h2>
                    <p className="text-white/70 text-sm">{items.length} {isRo ? 'biomarkeri' : 'biomarkers'}</p>
                  </div>
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map(b => <BiomarkerCard key={b.slug} b={b} isRo={isRo} catLookup={catLookup} catKey={catKey} />)}
                </div>
              </div>
            );
          })
        )}

        {/* CTA */}
        <section className="mt-12 mb-8 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 md:p-12 text-white">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-4">
                {isRo
                  ? 'Nu ghici ce înseamnă valorile tale. Lasă AI-ul să interpreteze.'
                  : "Don't guess what your values mean. Let AI interpret them."}
              </h2>
              <p className="text-slate-300 mb-6">
                {isRo
                  ? 'Încarcă analizele pe Analize.Online și primești interpretare de la specialiști AI — Cardiolog, Endocrinolog, Hematolog — plus plan nutrițional cu rețete românești și program de exerciții, totul bazat pe valorile tale reale.'
                  : 'Upload your results on Analize.Online and get interpretation from AI specialists — Cardiologist, Endocrinologist, Hematologist — plus nutrition plan with Romanian recipes and exercise program, all based on your real values.'}
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/20"
              >
                {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
                <ArrowRight size={18} />
              </Link>
            </div>
            <div className="hidden md:grid grid-cols-2 gap-3">
              {[
                { icon: Brain, label: isRo ? 'Specialiști AI' : 'AI Specialists' },
                { icon: Utensils, label: isRo ? 'Rețete românești' : 'Romanian recipes' },
                { icon: Dumbbell, label: isRo ? 'Plan exerciții' : 'Exercise plan' },
                { icon: ShoppingCart, label: isRo ? 'Listă cumpărături' : 'Grocery list' },
              ].map((f, i) => (
                <div key={i} className="flex items-center gap-2 bg-white/10 rounded-xl px-4 py-3">
                  <f.icon size={16} className="text-teal-400" />
                  <span className="text-white/90 text-sm">{f.label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function BiomarkerCard({ b, isRo, catLookup, catKey }) {
  const cat = b[catKey];
  const meta = catLookup[cat] || { bg: 'bg-slate-50', text: 'text-slate-600' };

  return (
    <Link
      to={`/biomarker/${b.slug}`}
      className="block bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-slate-300 transition-all group"
    >
      {/* Color bar at top */}
      <div className={`h-1.5 bg-gradient-to-r ${(catLookup[cat] || {}).color || 'from-slate-400 to-slate-500'}`} />
      <div className="p-5">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="font-bold text-slate-800 group-hover:text-teal-700 transition-colors text-lg">
              {isRo ? b.name_ro : b.name_en}
            </h3>
            {b.aliases_ro?.length > 0 && (
              <p className="text-xs text-slate-400 mt-0.5">{b.aliases_ro.join(' / ')}</p>
            )}
          </div>
          <span className="text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded font-mono">{b.unit}</span>
        </div>
        <p className="text-sm text-slate-500 line-clamp-2 mb-3">
          {isRo ? b.what_ro : b.what_en}
        </p>
        {/* Quick range preview */}
        {b.ranges?.[0] && (
          <div className="text-xs text-slate-400 bg-slate-50 rounded-lg px-3 py-2 mb-3">
            <span className="font-medium text-slate-500">{isRo ? b.ranges[0].group_ro : b.ranges[0].group_en}:</span>{' '}
            <span className="font-mono">{b.ranges[0].range}</span>
          </div>
        )}
        <div className="flex items-center gap-1 text-teal-600 text-sm font-semibold group-hover:gap-2 transition-all">
          {isRo ? 'Vezi detalii' : 'View details'}
          <ArrowRight size={14} />
        </div>
      </div>
    </Link>
  );
}
