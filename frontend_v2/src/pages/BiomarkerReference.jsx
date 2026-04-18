import React, { useState, useEffect } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, TrendingUp, TrendingDown, Info, ArrowUpRight, Brain, Utensils, Dumbbell, ShoppingCart, BookOpen, CheckCircle, AlertTriangle, ChevronDown, ChevronUp, Upload, HelpCircle, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import api from '../api/client';
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

function parseRange(rangeStr) {
  // Parse range strings like "13.5 – 17.5 g/dL", "0 - 200", "< 5.7 %", "> 30"
  const cleaned = rangeStr.replace(/[a-zA-Zµ/%°·×³]/g, '').trim();
  // "X – Y" or "X - Y"
  const dashMatch = cleaned.match(/([\d.,]+)\s*[–\-]\s*([\d.,]+)/);
  if (dashMatch) {
    return { min: parseFloat(dashMatch[1].replace(',', '.')), max: parseFloat(dashMatch[2].replace(',', '.')) };
  }
  // "< X"
  const ltMatch = cleaned.match(/<\s*([\d.,]+)/);
  if (ltMatch) return { min: null, max: parseFloat(ltMatch[1].replace(',', '.')) };
  // "> X"
  const gtMatch = cleaned.match(/>\s*([\d.,]+)/);
  if (gtMatch) return { min: parseFloat(gtMatch[1].replace(',', '.')), max: null };
  return null;
}

function QuickCheck({ biomarker, isRo }) {
  const [value, setValue] = useState('');
  const [selectedGroup, setSelectedGroup] = useState(0);
  const [result, setResult] = useState(null);

  const ranges = biomarker.ranges || [];
  if (ranges.length === 0) return null;

  const check = () => {
    const num = parseFloat(value.replace(',', '.'));
    if (isNaN(num)) return;

    const range = ranges[selectedGroup];
    const parsed = parseRange(range.range);
    if (!parsed) {
      setResult({ status: 'unknown', value: num });
      return;
    }

    let status = 'NORMAL';
    if (parsed.max !== null && num > parsed.max) status = 'HIGH';
    else if (parsed.min !== null && num < parsed.min) status = 'LOW';

    setResult({
      status,
      value: num,
      range: range.range,
      group: isRo ? range.group_ro : range.group_en,
      explanation: status === 'HIGH'
        ? (isRo ? biomarker.high_ro : biomarker.high_en)
        : status === 'LOW'
        ? (isRo ? biomarker.low_ro : biomarker.low_en)
        : null,
    });
  };

  const statusConfig = {
    NORMAL: { bg: 'bg-green-50 border-green-200', badge: 'bg-green-100 text-green-700', icon: CheckCircle, iconColor: 'text-green-500', label: 'NORMAL' },
    HIGH: { bg: 'bg-red-50 border-red-200', badge: 'bg-red-100 text-red-700', icon: TrendingUp, iconColor: 'text-red-500', label: isRo ? 'RIDICAT' : 'HIGH' },
    LOW: { bg: 'bg-amber-50 border-amber-200', badge: 'bg-amber-100 text-amber-700', icon: TrendingDown, iconColor: 'text-amber-500', label: isRo ? 'SCĂZUT' : 'LOW' },
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-6">
      <div className="bg-gradient-to-r from-cyan-500 to-teal-500 p-5 flex items-center gap-3">
        <CheckCircle size={22} className="text-white" />
        <h2 className="text-lg font-bold text-white">
          {isRo ? 'Verifică-ți valoarea' : 'Check your value'}
        </h2>
      </div>
      <div className="p-6">
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-slate-600 mb-1 block">
              {isRo ? 'Valoarea ta' : 'Your value'} ({biomarker.unit})
            </label>
            <input
              type="text"
              inputMode="decimal"
              value={value}
              onChange={(e) => { setValue(e.target.value); setResult(null); }}
              placeholder={isRo ? 'Ex: 14.2' : 'E.g. 14.2'}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 outline-none text-slate-700 font-mono"
              onKeyDown={(e) => e.key === 'Enter' && check()}
            />
          </div>
          {ranges.length > 1 && (
            <div className="flex-1">
              <label className="text-sm font-medium text-slate-600 mb-1 block">
                {isRo ? 'Grup' : 'Group'}
              </label>
              <div className="relative">
                <select
                  value={selectedGroup}
                  onChange={(e) => { setSelectedGroup(parseInt(e.target.value)); setResult(null); }}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:border-cyan-500 outline-none text-slate-700 appearance-none bg-white pr-10"
                >
                  {ranges.map((r, i) => (
                    <option key={i} value={i}>{isRo ? r.group_ro : r.group_en}</option>
                  ))}
                </select>
                <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
            </div>
          )}
          <div className="flex items-end">
            <button
              onClick={check}
              disabled={!value.trim()}
              className="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold hover:from-cyan-600 hover:to-teal-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRo ? 'Verifică' : 'Check'}
            </button>
          </div>
        </div>

        {result && result.status !== 'unknown' && (
          <div className={`rounded-xl border p-4 ${statusConfig[result.status].bg}`}>
            <div className="flex items-center gap-3 mb-2">
              {React.createElement(statusConfig[result.status].icon, { size: 20, className: statusConfig[result.status].iconColor })}
              <span className={`px-3 py-1 rounded-full text-sm font-bold ${statusConfig[result.status].badge}`}>
                {statusConfig[result.status].label}
              </span>
              <span className="text-sm text-slate-600">
                {isRo
                  ? `${biomarker.name_ro} de ${result.value} ${biomarker.unit} este ${statusConfig[result.status].label} pentru ${result.group}`
                  : `${biomarker.name_en} of ${result.value} ${biomarker.unit} is ${statusConfig[result.status].label} for ${result.group}`}
              </span>
            </div>
            {result.explanation && (
              <p className="text-sm text-slate-600 mt-2 pl-8">{result.explanation}</p>
            )}
            {result.status !== 'NORMAL' && (
              <div className="mt-3 pl-8">
                <Link
                  to="/analyzer"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-teal-700 hover:text-teal-800 transition-colors"
                >
                  {isRo ? 'Încarcă analizele complete pentru interpretare AI →' : 'Upload your full lab results for AI interpretation →'}
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

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

  // FAQ JSON-LD schema for rich snippets
  const faqs = isRo ? biomarker.faqs_ro : biomarker.faqs_en;
  useJsonLd(faqs?.length ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(f => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  } : null, 'biomarker-faq');

  // Fetch related blog articles
  const [relatedArticles, setRelatedArticles] = useState([]);
  useEffect(() => {
    api.get(`/blog/articles?biomarker=${encodeURIComponent(biomarker.name_ro)}&limit=3`)
      .then(res => setRelatedArticles(res.data.articles || []))
      .catch(() => {});
  }, [biomarker.name_ro]);

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
          <div className="px-4 sm:px-8 pb-8">
            <div className="rounded-xl overflow-hidden border border-slate-200 overflow-x-auto">
              <table className="w-full min-w-[320px]">
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

        {/* Quick-check widget */}
        <QuickCheck biomarker={biomarker} isRo={isRo} />

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

        {/* Related Blog Articles */}
        {relatedArticles.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-teal-500" />
              {isRo ? 'Articole despre' : 'Articles about'} {name}
            </h2>
            <div className="space-y-3">
              {relatedArticles.map(a => (
                <Link
                  key={a.slug}
                  to={`/blog/${a.slug}`}
                  className="block p-4 rounded-xl border border-slate-200 hover:border-teal-300 hover:bg-teal-50 transition-colors"
                >
                  <h3 className="font-semibold text-slate-800 mb-1">{isRo ? a.title : (a.title_en || a.title)}</h3>
                  <p className="text-sm text-slate-500 line-clamp-2">{isRo ? a.excerpt : (a.excerpt_en || a.excerpt)}</p>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* FAQ Section */}
        {faqs?.length > 0 && (
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-6">
            <h2 className="text-xl font-bold text-slate-800 mb-5 flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-teal-500" />
              {isRo ? 'Întrebări frecvente' : 'Frequently Asked Questions'}
            </h2>
            <div className="space-y-3">
              {faqs.map((faq, i) => (
                <FaqItem key={i} question={faq.q} answer={faq.a} />
              ))}
            </div>
          </section>
        )}

        {/* CTA — links to analyzer */}
        <section className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 md:p-10 text-white mb-6">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-1">
              <h2 className="text-xl md:text-2xl font-bold mb-2">
                {isRo
                  ? 'Ai analizele complete? Încarcă-le și primești interpretare AI gratuită'
                  : 'Have your full lab results? Upload them for free AI interpretation'}
              </h2>
              <p className="text-teal-100">
                {isRo
                  ? 'Lipește textul analizelor sau încarcă PDF-ul. AI-ul nostru extrage toți biomarkerii instant și îi compară cu valorile de referință.'
                  : 'Paste your lab results text or upload the PDF. Our AI extracts all biomarkers instantly and compares them to reference ranges.'}
              </p>
            </div>
            <Link
              to="/analyzer"
              className="shrink-0 inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-bold hover:bg-teal-50 transition-colors shadow-lg"
            >
              {isRo ? 'Analizator Gratuit' : 'Free Analyzer'}
              <Upload size={18} />
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

function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="font-medium text-slate-800 pr-4">{question}</span>
        {open ? <ChevronUp size={18} className="text-slate-400 flex-shrink-0" /> : <ChevronDown size={18} className="text-slate-400 flex-shrink-0" />}
      </button>
      {open && (
        <div className="px-5 pb-4 text-slate-600 leading-relaxed text-sm border-t border-slate-100 pt-3">
          {answer}
        </div>
      )}
    </div>
  );
}
