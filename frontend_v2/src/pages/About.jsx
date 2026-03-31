import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { HeartPulse, Target, Shield, Cpu, Users, Sparkles, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';

export default function About() {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';

  usePageTitle(null, null, {
    title: isRo ? 'Despre noi — Echipa Analize.Online' : 'About Us — Analize.Online Team',
    description: isRo
      ? 'Misiunea Analize.Online: digitalizarea sănătății în România. Agregare analize medicale, interpretare AI, criptare per utilizator.'
      : 'Analize.Online mission: digitalizing healthcare in Romania. Medical test aggregation, AI interpretation, per-user encryption.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'AboutPage',
    name: isRo ? 'Despre Analize.Online' : 'About Analize.Online',
    url: 'https://analize.online/despre-noi',
    mainEntity: {
      '@type': 'Organization',
      name: 'Analize.Online',
      url: 'https://analize.online',
      foundingDate: '2025',
      areaServed: { '@type': 'Country', name: 'Romania' },
      description: isRo
        ? 'Prima platformă din România care agregă automat analizele medicale de la mai multe laboratoare și oferă interpretare AI.'
        : 'Romania\'s first platform that automatically aggregates lab results from multiple laboratories and offers AI interpretation.',
    },
  });

  const values = [
    {
      icon: Target,
      title: isRo ? 'Misiunea noastră' : 'Our Mission',
      description: isRo
        ? 'Să oferim fiecărui român acces simplu și sigur la toate analizele medicale într-un singur loc, cu interpretare inteligentă care ajută la prevenție și monitorizare.'
        : 'To give every Romanian simple and secure access to all their medical tests in one place, with intelligent interpretation that helps with prevention and monitoring.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Shield,
      title: isRo ? 'Securitate maximă' : 'Maximum Security',
      description: isRo
        ? 'Datele medicale sunt cele mai sensibile informații personale. Folosim criptare AES-256-GCM per utilizator — nici măcar administratorii platformei nu pot accesa datele tale.'
        : 'Medical data is the most sensitive personal information. We use per-user AES-256-GCM encryption — not even platform administrators can access your data.',
      color: 'from-emerald-500 to-green-500',
    },
    {
      icon: Cpu,
      title: isRo ? 'Inteligență artificială' : 'Artificial Intelligence',
      description: isRo
        ? '6 specialiști virtuali AI (generalist, cardiolog, endocrinolog, hematolog, hepatolog, nefrolog) analizează rezultatele tale și identifică potențiale probleme înainte să devină grave.'
        : '6 virtual AI specialists (generalist, cardiologist, endocrinologist, hematologist, hepatologist, nephrologist) analyze your results and identify potential issues before they become serious.',
      color: 'from-violet-500 to-purple-500',
    },
    {
      icon: Users,
      title: isRo ? 'Centrat pe pacient' : 'Patient-Centered',
      description: isRo
        ? 'Platforma este construită pentru pacienți, nu pentru laboratoare. Tu deții datele tale și poți să le descarci sau ștergi oricând.'
        : 'The platform is built for patients, not laboratories. You own your data and can download or delete it anytime.',
      color: 'from-orange-500 to-amber-500',
    },
  ];

  const milestones = [
    { year: '2025', title: isRo ? 'Lansare platformă' : 'Platform Launch', desc: isRo ? 'Prima versiune cu suport Regina Maria și Synevo' : 'First version with Regina Maria and Synevo support' },
    { year: '2025', title: isRo ? 'AI Specialiști' : 'AI Specialists', desc: isRo ? '6 specialiști virtuali care analizează biomarkerii' : '6 virtual specialists analyzing biomarkers' },
    { year: '2026', title: isRo ? 'MedLife & Sanador' : 'MedLife & Sanador', desc: isRo ? 'Suport extins pentru 4 rețele majore de laboratoare' : 'Extended support for 4 major lab networks' },
    { year: '2026', title: isRo ? 'Analizator gratuit' : 'Free Analyzer', desc: isRo ? 'Instrument public pentru interpretarea analizelor' : 'Public tool for lab result interpretation' },
  ];

  const content = (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-gradient-to-br from-cyan-100 to-teal-100 rounded-xl">
            <HeartPulse className="w-8 h-8 text-teal-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              {isRo ? 'Despre Analize.Online' : 'About Analize.Online'}
            </h1>
            <p className="text-slate-500">
              {isRo ? 'Digitalizăm sănătatea în România' : 'Digitalizing healthcare in Romania'}
            </p>
          </div>
        </div>
      </div>

      {/* Vision */}
      <div className="bg-gradient-to-br from-teal-50 to-cyan-50 border border-teal-200 rounded-2xl p-8 mb-10">
        <h2 className="text-xl font-bold text-slate-800 mb-3">
          <Sparkles className="inline w-5 h-5 text-teal-500 mr-2 -mt-0.5" />
          {isRo ? 'De ce existăm' : 'Why We Exist'}
        </h2>
        <p className="text-slate-700 leading-relaxed text-lg">
          {isRo
            ? 'Milioane de români fac analize medicale în fiecare an la Regina Maria, Synevo, MedLife sau Sanador. Rezultatele ajung în PDF-uri izolate, greu de comparat între ele. Analize.Online reunește toate rezultatele într-un singur loc și le dă sens cu ajutorul inteligenței artificiale.'
            : 'Millions of Romanians take medical tests every year at Regina Maria, Synevo, MedLife, or Sanador. Results end up in isolated PDFs, hard to compare. Analize.Online brings all results together in one place and gives them meaning with artificial intelligence.'}
        </p>
      </div>

      {/* Values Grid */}
      <div className="grid md:grid-cols-2 gap-6 mb-10">
        {values.map((v, i) => (
          <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <div className={`w-12 h-12 bg-gradient-to-br ${v.color} rounded-xl flex items-center justify-center mb-4`}>
              <v.icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-2">{v.title}</h3>
            <p className="text-slate-600 leading-relaxed">{v.description}</p>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <div className="mb-10">
        <h2 className="text-xl font-bold text-slate-800 mb-6">
          {isRo ? 'Parcursul nostru' : 'Our Journey'}
        </h2>
        <div className="space-y-4">
          {milestones.map((m, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="flex-shrink-0 w-16 h-8 bg-teal-100 rounded-lg flex items-center justify-center">
                <span className="text-sm font-bold text-teal-700">{m.year}</span>
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">{m.title}</h3>
                <p className="text-slate-500 text-sm">{m.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Medical Disclaimer Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-10">
        <h3 className="font-bold text-amber-800 mb-2">
          {isRo ? 'Informare importantă' : 'Important Notice'}
        </h3>
        <p className="text-amber-700 text-sm leading-relaxed">
          {isRo
            ? 'Analize.Online oferă informații orientative bazate pe inteligență artificială, nu diagnostic medical. Rezultatele și recomandările nu înlocuiesc consultul cu un medic specialist. Consultă întotdeauna un profesionist medical calificat pentru interpretarea analizelor tale.'
            : 'Analize.Online provides AI-based informational guidance, not medical diagnosis. Results and recommendations do not replace consultation with a medical specialist. Always consult a qualified medical professional for interpretation of your test results.'}
        </p>
        <Link to="/disclaimer-medical" className="inline-flex items-center gap-1 text-sm font-medium text-amber-800 hover:text-amber-900 mt-2">
          {isRo ? 'Citește disclaimer-ul medical complet' : 'Read the full medical disclaimer'}
          <ArrowRight size={14} />
        </Link>
      </div>

      {/* CTA */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 text-center">
        <h2 className="text-2xl font-bold text-white mb-3">
          {isRo ? 'Începe gratuit azi' : 'Start Free Today'}
        </h2>
        <p className="text-slate-300 mb-6 max-w-md mx-auto">
          {isRo
            ? 'Conectează-ți contul de laborator și vezi toate analizele tale într-un singur loc.'
            : 'Connect your lab account and see all your tests in one place.'}
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold rounded-xl hover:shadow-lg transition-all"
        >
          {isRo ? 'Creează cont gratuit' : 'Create free account'}
          <ArrowRight size={18} />
        </Link>
      </div>

      {/* Footer links */}
      <div className="mt-8 pt-6 border-t border-slate-200 flex flex-wrap gap-4 text-sm text-slate-500">
        <Link to="/contact" className="hover:text-teal-600">{isRo ? 'Contact' : 'Contact'}</Link>
        <Link to="/terms" className="hover:text-teal-600">{isRo ? 'Termeni' : 'Terms'}</Link>
        <Link to="/privacy" className="hover:text-teal-600">{isRo ? 'Confidențialitate' : 'Privacy'}</Link>
        <Link to="/disclaimer-medical" className="hover:text-teal-600">{isRo ? 'Disclaimer medical' : 'Medical Disclaimer'}</Link>
      </div>
    </div>
  );

  if (user) return content;

  return (
    <>
      <PublicNav />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4">
        {content}
      </div>
    </>
  );
}
