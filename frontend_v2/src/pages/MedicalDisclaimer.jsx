import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { AlertTriangle, Stethoscope, Shield, Brain, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';

export default function MedicalDisclaimer() {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';

  usePageTitle(null, null, {
    title: isRo ? 'Disclaimer Medical — Analize.Online' : 'Medical Disclaimer — Analize.Online',
    description: isRo
      ? 'Analize.Online oferă informații orientative bazate pe AI, nu diagnostic medical. Consultă întotdeauna un medic specialist.'
      : 'Analize.Online provides AI-based informational guidance, not medical diagnosis. Always consult a medical specialist.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: isRo ? 'Disclaimer Medical' : 'Medical Disclaimer',
    url: 'https://analize.online/disclaimer-medical',
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
  });

  const sections = isRo ? [
    {
      icon: Stethoscope,
      title: 'Nu este consiliere medicală',
      content: 'Analize.Online este o platformă tehnologică de agregare și vizualizare a rezultatelor analizelor medicale. Interpretările oferite de specialiștii virtuali AI sunt orientative și informative. Ele NU constituie diagnostic medical, consiliere medicală sau recomandare de tratament.',
    },
    {
      icon: Brain,
      title: 'Limitările inteligenței artificiale',
      content: 'Specialiștii noștri virtuali AI (generalist, cardiolog, endocrinolog, hematolog, hepatolog, nefrolog) sunt modele de limbaj antrenate pe literatură medicală. Aceștia pot identifica tiparele și valorile anormale, dar nu pot lua în considerare contextul clinic complet: simptome, istoric medical, medicamente curente, sau alți factori pe care un medic specialist îi evaluează în persoană.',
    },
    {
      icon: AlertTriangle,
      title: 'Consultă întotdeauna un medic',
      content: 'Pentru orice valoare anormală sau îngrijorare legată de sănătate, consultă un medic specialist. Nu modifica, întrerupe sau începe niciun tratament medical pe baza informațiilor din platformă fără a consulta mai întâi un medic calificat.',
    },
    {
      icon: Shield,
      title: 'Situații de urgență',
      content: 'Analize.Online NU este conceput pentru situații de urgență medicală. În caz de urgență, sună imediat la 112 sau mergi la cel mai apropiat serviciu de urgență.',
    },
    {
      icon: FileText,
      title: 'Acuratețea datelor',
      content: 'Platforma extrage automat biomarkeri din PDF-urile de analize folosind inteligență artificială. Deși algoritmii au o acuratețe ridicată, pot apărea erori de extracție. Verifică întotdeauna valorile afișate cu documentul original (PDF-ul sursă, disponibil în secțiunea Documente).',
    },
  ] : [
    {
      icon: Stethoscope,
      title: 'Not Medical Advice',
      content: 'Analize.Online is a technology platform for aggregating and visualizing lab test results. The interpretations provided by virtual AI specialists are informational and orientative. They do NOT constitute medical diagnosis, medical advice, or treatment recommendations.',
    },
    {
      icon: Brain,
      title: 'Limitations of Artificial Intelligence',
      content: 'Our virtual AI specialists (generalist, cardiologist, endocrinologist, hematologist, hepatologist, nephrologist) are language models trained on medical literature. They can identify patterns and abnormal values, but cannot consider the full clinical context: symptoms, medical history, current medications, or other factors that a specialist doctor evaluates in person.',
    },
    {
      icon: AlertTriangle,
      title: 'Always Consult a Doctor',
      content: 'For any abnormal value or health concern, consult a medical specialist. Do not modify, interrupt, or start any medical treatment based on information from the platform without first consulting a qualified physician.',
    },
    {
      icon: Shield,
      title: 'Emergency Situations',
      content: 'Analize.Online is NOT designed for medical emergencies. In case of emergency, immediately call 112 or go to the nearest emergency department.',
    },
    {
      icon: FileText,
      title: 'Data Accuracy',
      content: 'The platform automatically extracts biomarkers from lab test PDFs using artificial intelligence. While the algorithms have high accuracy, extraction errors may occur. Always verify displayed values against the original document (source PDF, available in the Documents section).',
    },
  ];

  const content = (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-xl">
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              {isRo ? 'Disclaimer Medical' : 'Medical Disclaimer'}
            </h1>
            <p className="text-slate-500">
              {isRo ? 'Informații importante despre utilizarea platformei' : 'Important information about platform usage'}
            </p>
          </div>
        </div>
      </div>

      {/* Important Banner */}
      <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6 mb-8">
        <p className="text-red-800 font-semibold text-lg leading-relaxed">
          {isRo
            ? 'Analize.Online este un instrument informativ. Interpretările AI sunt orientative și NU înlocuiesc consultul medical profesionist. Pentru orice decizie legată de sănătatea ta, consultă un medic specialist.'
            : 'Analize.Online is an informational tool. AI interpretations are orientative and do NOT replace professional medical consultation. For any decision regarding your health, consult a medical specialist.'}
        </p>
      </div>

      {/* Sections */}
      <div className="space-y-6">
        {sections.map((s, i) => (
          <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center">
                <s.icon className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-800 mb-2">{s.title}</h2>
                <p className="text-slate-600 leading-relaxed">{s.content}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Acceptance */}
      <div className="mt-8 bg-slate-50 rounded-2xl border border-slate-200 p-6 text-center">
        <p className="text-slate-600 text-sm">
          {isRo
            ? 'Prin utilizarea platformei Analize.Online, confirmi că ai citit și înțeles acest disclaimer medical. Utilizarea platformei implică acceptarea acestor termeni.'
            : 'By using the Analize.Online platform, you confirm that you have read and understood this medical disclaimer. Use of the platform implies acceptance of these terms.'}
        </p>
        <p className="text-slate-400 text-xs mt-3">
          {isRo ? 'Ultima actualizare: Martie 2026' : 'Last updated: March 2026'}
        </p>
      </div>

      {/* Footer links */}
      <div className="mt-8 pt-6 border-t border-slate-200 flex flex-wrap gap-4 text-sm text-slate-500">
        <Link to="/despre-noi" className="hover:text-teal-600">{isRo ? 'Despre noi' : 'About Us'}</Link>
        <Link to="/contact" className="hover:text-teal-600">{isRo ? 'Contact' : 'Contact'}</Link>
        <Link to="/terms" className="hover:text-teal-600">{isRo ? 'Termeni' : 'Terms'}</Link>
        <Link to="/privacy" className="hover:text-teal-600">{isRo ? 'Confidențialitate' : 'Privacy'}</Link>
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
