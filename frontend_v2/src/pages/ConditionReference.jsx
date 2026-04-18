import React, { useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, Stethoscope, AlertTriangle, ChevronDown, ChevronUp, Upload, HelpCircle, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import conditions from '../data/conditions-reference.json';
import biomarkersData from '../data/biomarkers-reference.json';

const biomarkerMap = {};
biomarkersData.forEach(b => { biomarkerMap[b.slug] = b; });

export default function ConditionReference() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';

  const condition = conditions.find(c => c.slug === slug);
  if (!condition) return <Navigate to="/biomarker" replace />;

  const name = isRo ? condition.name_ro : condition.name_en;
  const description = isRo ? condition.description_ro : condition.description_en;
  const symptoms = isRo ? condition.symptoms_ro : condition.symptoms_en;
  const when = isRo ? condition.when_ro : condition.when_en;
  const faqs = isRo ? condition.faqs_ro : condition.faqs_en;
  const meta = isRo ? condition.meta_ro : condition.meta_en;

  usePageTitle(null, null, {
    title: `${name} | Analize.Online`,
    description: meta,
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'MedicalWebPage',
    name,
    description: meta,
    url: `https://analize.online/analize-pentru/${slug}`,
    inLanguage: isRo ? 'ro' : 'en',
    medicalAudience: { '@type': 'MedicalAudience', audienceType: 'Patient' },
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: isRo ? 'Acasă' : 'Home', item: 'https://analize.online' },
        { '@type': 'ListItem', position: 2, name: isRo ? 'Biomarkeri' : 'Biomarkers', item: 'https://analize.online/biomarker' },
        { '@type': 'ListItem', position: 3, name },
      ],
    },
  });

  useJsonLd(faqs?.length ? {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(f => ({
      '@type': 'Question', name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  } : null, 'condition-faq');

  const linkedBiomarkers = (condition.biomarkers || []).map(s => biomarkerMap[s]).filter(Boolean);

  const content = (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <Link to="/" className="hover:text-teal-600">{isRo ? 'Acasă' : 'Home'}</Link>
        <span>/</span>
        <Link to="/biomarker" className="hover:text-teal-600">{isRo ? 'Biomarkeri' : 'Biomarkers'}</Link>
        <span>/</span>
        <span className="text-slate-800 font-medium">{name}</span>
      </nav>

      {/* Hero */}
      <div className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 md:p-10 text-white mb-8">
        <div className="flex items-center gap-3 mb-3">
          <Stethoscope className="w-8 h-8" />
          <h1 className="text-2xl md:text-3xl font-bold">{name}</h1>
        </div>
        <p className="text-teal-100 text-lg leading-relaxed">{description}</p>
      </div>

      {/* Symptoms */}
      {symptoms.length > 0 && (
        <section className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-bold text-amber-800 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {isRo ? 'Simptome frecvente' : 'Common Symptoms'}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {symptoms.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-amber-700 text-sm">
                <div className="w-1.5 h-1.5 bg-amber-500 rounded-full flex-shrink-0" />
                {s}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Biomarkers Table */}
      <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
        <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-teal-500" />
          {isRo ? 'Ce biomarkeri se verifică' : 'Which biomarkers are checked'}
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-3 font-semibold text-slate-600">{isRo ? 'Biomarker' : 'Biomarker'}</th>
                <th className="text-left py-3 px-3 font-semibold text-slate-600">{isRo ? 'Ce măsoară' : 'What it measures'}</th>
                <th className="text-right py-3 px-3 font-semibold text-slate-600">{isRo ? 'Valori normale' : 'Normal values'}</th>
              </tr>
            </thead>
            <tbody>
              {linkedBiomarkers.map(b => (
                <tr key={b.slug} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="py-3 px-3">
                    <Link to={`/biomarker/${b.slug}`} className="text-teal-600 hover:underline font-medium">
                      {isRo ? b.name_ro : b.name_en}
                    </Link>
                  </td>
                  <td className="py-3 px-3 text-slate-600 text-xs leading-relaxed max-w-[300px]">
                    {(isRo ? b.what_ro : b.what_en)?.split('.')[0]}.
                  </td>
                  <td className="py-3 px-3 text-right text-slate-700 font-mono text-xs whitespace-nowrap">
                    {b.ranges?.[0]?.range || '–'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* When to test */}
      <section className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-6">
        <h2 className="text-lg font-bold text-blue-800 mb-2">
          {isRo ? 'Când se recomandă testarea' : 'When testing is recommended'}
        </h2>
        <p className="text-blue-700 leading-relaxed">{when}</p>
      </section>

      {/* FAQ */}
      {faqs?.length > 0 && (
        <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
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

      {/* CTA */}
      <section className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 text-white mb-6">
        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="flex-1">
            <h2 className="text-xl font-bold mb-2">
              {isRo
                ? 'Ai deja analizele? Încarcă-le și primești interpretare AI gratuită'
                : 'Have your results? Upload them for free AI interpretation'}
            </h2>
            <p className="text-teal-100">
              {isRo
                ? 'AI-ul nostru extrage toți biomarkerii instant și îi compară cu valorile de referință. 6 specialiști virtuali analizează rezultatele tale.'
                : 'Our AI extracts all biomarkers instantly and compares them to reference ranges. 6 virtual specialists analyze your results.'}
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

      {/* Other conditions */}
      <section className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
        <h3 className="text-lg font-bold text-slate-800 mb-4">
          {isRo ? 'Alte ghiduri de analize' : 'Other test guides'}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {conditions.filter(c => c.slug !== slug).map(c => (
            <Link
              key={c.slug}
              to={`/analize-pentru/${c.slug}`}
              className="flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 hover:border-teal-300 hover:bg-teal-50 transition-colors text-sm"
            >
              <ArrowRight size={14} className="text-teal-500 flex-shrink-0" />
              <span className="text-slate-700 font-medium">{isRo ? c.name_ro : c.name_en}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Back */}
      <div className="text-center pb-10">
        <Link to="/biomarker" className="inline-flex items-center gap-2 text-slate-500 hover:text-teal-600 font-medium">
          <ArrowLeft size={16} />
          {isRo ? 'Toți biomarkerii' : 'All biomarkers'}
        </Link>
      </div>
    </div>
  );

  if (user) return content;

  return (
    <>
      <PublicNav />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
        {content}
      </div>
    </>
  );
}

function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-slate-50 transition-colors">
        <span className="font-medium text-slate-800 pr-4">{question}</span>
        {open ? <ChevronUp size={18} className="text-slate-400 flex-shrink-0" /> : <ChevronDown size={18} className="text-slate-400 flex-shrink-0" />}
      </button>
      {open && (
        <div className="px-5 pb-4 text-slate-600 leading-relaxed text-sm border-t border-slate-100 pt-3">{answer}</div>
      )}
    </div>
  );
}
