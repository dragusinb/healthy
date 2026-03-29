import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FileText, TrendingUp, AlertTriangle, CheckCircle, ArrowRight,
  HeartPulse, Brain, Activity, Stethoscope
} from 'lucide-react';
import PublicNav from '../components/PublicNav';
import usePageTitle from '../hooks/usePageTitle';

const SAMPLE_DOCUMENTS = [
  { id: 1, filename: 'Analize_Sange_Oct2025.pdf', provider: 'Regina Maria', date: '2025-10-15', biomarkers: 12 },
  { id: 2, filename: 'Profil_Lipidic_Aug2025.pdf', provider: 'Synevo', date: '2025-08-22', biomarkers: 8 },
  { id: 3, filename: 'Hemoleucograma_Jun2025.pdf', provider: 'Regina Maria', date: '2025-06-10', biomarkers: 15 },
  { id: 4, filename: 'Analize_Tiroidă_Mar2025.pdf', provider: 'Synevo', date: '2025-03-05', biomarkers: 4 },
  { id: 5, filename: 'Biochimie_Dec2024.pdf', provider: 'Regina Maria', date: '2024-12-18', biomarkers: 10 },
  { id: 6, filename: 'Profil_Hepatic_Sep2024.pdf', provider: 'Synevo', date: '2024-09-30', biomarkers: 6 },
];

const SAMPLE_BIOMARKERS = [
  { name: 'Hemoglobina', value: '14.2', unit: 'g/dL', range: '12 - 16', flag: 'NORMAL', category: 'Hematologie' },
  { name: 'Colesterol Total', value: '245', unit: 'mg/dL', range: '0 - 200', flag: 'HIGH', category: 'Biochimie' },
  { name: 'Glicemie', value: '92', unit: 'mg/dL', range: '74 - 106', flag: 'NORMAL', category: 'Biochimie' },
  { name: 'Vitamina D', value: '18', unit: 'ng/mL', range: '30 - 100', flag: 'LOW', category: 'Vitamine' },
  { name: 'TSH', value: '2.4', unit: 'mIU/L', range: '0.27 - 4.2', flag: 'NORMAL', category: 'Tiroidă' },
  { name: 'TGP (ALT)', value: '62', unit: 'U/L', range: '0 - 50', flag: 'HIGH', category: 'Enzime hepatice' },
  { name: 'Creatinina', value: '0.9', unit: 'mg/dL', range: '0.7 - 1.2', flag: 'NORMAL', category: 'Biochimie' },
  { name: 'Fier seric', value: '42', unit: 'µg/dL', range: '33 - 193', flag: 'LOW', category: 'Biochimie' },
  { name: 'LDL Colesterol', value: '165', unit: 'mg/dL', range: '0 - 130', flag: 'HIGH', category: 'Biochimie' },
  { name: 'Hemoglobina glicată', value: '5.2', unit: '%', range: '4 - 6', flag: 'NORMAL', category: 'Biochimie' },
  { name: 'Leucocite', value: '7.2', unit: '×10³/µL', range: '4 - 10', flag: 'NORMAL', category: 'Hematologie' },
  { name: 'Trombocite', value: '235', unit: '×10³/µL', range: '150 - 400', flag: 'NORMAL', category: 'Hematologie' },
];

const SAMPLE_EVOLUTION = [
  { date: 'Mar 2024', value: 13.8 },
  { date: 'Jun 2024', value: 14.0 },
  { date: 'Sep 2024', value: 13.5 },
  { date: 'Dec 2024', value: 14.1 },
  { date: 'Mar 2025', value: 13.9 },
  { date: 'Oct 2025', value: 14.2 },
];

export default function Demo() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';

  usePageTitle(null, null, {
    title: isRo ? 'Demo — Vezi cum funcționează | Analize.Online' : 'Demo — See how it works | Analize.Online',
    description: isRo ? 'Explorează platforma Analize.Online cu date demo.' : 'Explore the Analize.Online platform with sample data.',
  });

  const highCount = SAMPLE_BIOMARKERS.filter(b => b.flag === 'HIGH').length;
  const lowCount = SAMPLE_BIOMARKERS.filter(b => b.flag === 'LOW').length;
  const normalCount = SAMPLE_BIOMARKERS.filter(b => b.flag === 'NORMAL').length;

  const flagColor = (flag) => {
    if (flag === 'HIGH') return 'bg-red-100 text-red-700';
    if (flag === 'LOW') return 'bg-amber-100 text-amber-700';
    return 'bg-green-100 text-green-700';
  };

  // Simple sparkline using SVG
  const maxVal = Math.max(...SAMPLE_EVOLUTION.map(e => e.value));
  const minVal = Math.min(...SAMPLE_EVOLUTION.map(e => e.value));
  const range = maxVal - minVal || 1;
  const points = SAMPLE_EVOLUTION.map((e, i) => {
    const x = (i / (SAMPLE_EVOLUTION.length - 1)) * 280 + 10;
    const y = 80 - ((e.value - minVal) / range) * 60;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="min-h-screen bg-slate-50 relative">
      <PublicNav />

      {/* DEMO watermark */}
      <div className="fixed inset-0 pointer-events-none z-40 flex items-center justify-center opacity-[0.04]">
        <span className="text-[200px] font-black text-slate-900 rotate-[-30deg] select-none">DEMO</span>
      </div>

      {/* Top banner */}
      <div className="fixed top-[65px] left-0 right-0 z-30 bg-gradient-to-r from-violet-600 to-purple-600 text-white px-4 py-3 text-center">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-center gap-3">
          <span className="text-sm font-medium">
            {isRo
              ? '📊 Acestea sunt date demonstrative. Creează un cont gratuit pentru a vedea datele TALE.'
              : '📊 This is sample data. Create a free account to see YOUR dashboard.'}
          </span>
          <Link
            to="/login?mode=register"
            className="shrink-0 px-4 py-1.5 bg-white text-purple-700 rounded-lg text-sm font-bold hover:bg-purple-50 transition-colors"
          >
            {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
          </Link>
        </div>
      </div>

      {/* Dashboard content */}
      <div className="pt-36 pb-16 px-6 max-w-6xl mx-auto">
        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText size={20} className="text-blue-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-800">{SAMPLE_DOCUMENTS.length}</p>
            <p className="text-sm text-slate-500">{isRo ? 'Documente' : 'Documents'}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center">
                <Activity size={20} className="text-teal-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-800">{SAMPLE_BIOMARKERS.length}</p>
            <p className="text-sm text-slate-500">{isRo ? 'Biomarkeri' : 'Biomarkers'}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle size={20} className="text-red-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-800">{highCount + lowCount}</p>
            <p className="text-sm text-slate-500">{isRo ? 'Alerte Sănătate' : 'Health Alerts'}</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle size={20} className="text-green-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-800">{normalCount}</p>
            <p className="text-sm text-slate-500">{isRo ? 'Valori Normale' : 'Normal Values'}</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Biomarkers list */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="p-5 border-b border-slate-100">
                <h2 className="text-lg font-bold text-slate-800">{isRo ? 'Biomarkeri Recenți' : 'Recent Biomarkers'}</h2>
              </div>
              <div className="divide-y divide-slate-100">
                {SAMPLE_BIOMARKERS.map((b, i) => (
                  <div key={i} className="flex items-center justify-between px-5 py-3 hover:bg-slate-50">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 text-sm">{b.name}</p>
                      <p className="text-xs text-slate-400">{b.category}</p>
                    </div>
                    <div className="text-right mr-4">
                      <p className="font-mono text-sm font-semibold text-slate-800">{b.value} <span className="text-slate-400 font-normal">{b.unit}</span></p>
                      <p className="text-xs text-slate-400">{isRo ? 'ref' : 'ref'}: {b.range}</p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${flagColor(b.flag)}`}>
                      {b.flag === 'HIGH' ? (isRo ? 'RIDICAT' : 'HIGH') : b.flag === 'LOW' ? (isRo ? 'SCĂZUT' : 'LOW') : 'NORMAL'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* AI Summary */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
                  <Brain size={20} className="text-violet-600" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800">{isRo ? 'Rezumat AI' : 'AI Summary'}</h3>
                  <p className="text-xs text-slate-400">{isRo ? 'Ultima analiză' : 'Latest analysis'}</p>
                </div>
              </div>
              <div className="space-y-2 text-sm text-slate-600">
                <p>
                  {isRo
                    ? '• Colesterolul total și LDL sunt peste limita normală. Consultă un cardiolog.'
                    : '• Total and LDL cholesterol are above normal limits. Consider consulting a cardiologist.'}
                </p>
                <p>
                  {isRo
                    ? '• Vitamina D este scăzută (18 ng/mL). Recomandare: suplimentare 2000 UI/zi.'
                    : '• Vitamin D is low (18 ng/mL). Recommendation: supplement 2000 IU/day.'}
                </p>
                <p>
                  {isRo
                    ? '• TGP ușor crescut — monitorizare recomandată.'
                    : '• ALT slightly elevated — monitoring recommended.'}
                </p>
              </div>
            </div>

            {/* Evolution mini chart */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-bold text-slate-800 mb-1">{isRo ? 'Evoluție Hemoglobina' : 'Hemoglobin Evolution'}</h3>
              <p className="text-xs text-slate-400 mb-4">{isRo ? 'Ultimele 2 ani' : 'Last 2 years'}</p>
              <svg viewBox="0 0 300 100" className="w-full h-24">
                <polyline
                  fill="none"
                  stroke="#14b8a6"
                  strokeWidth="2.5"
                  points={points}
                />
                {SAMPLE_EVOLUTION.map((e, i) => {
                  const x = (i / (SAMPLE_EVOLUTION.length - 1)) * 280 + 10;
                  const y = 80 - ((e.value - minVal) / range) * 60;
                  return <circle key={i} cx={x} cy={y} r="4" fill="#14b8a6" />;
                })}
                {/* Reference range band */}
                <rect x="10" y={80 - ((16 - minVal) / range) * 60} width="280" height={((16 - 12) / range) * 60} fill="#14b8a6" opacity="0.08" rx="4" />
              </svg>
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>Mar 2024</span>
                <span>Oct 2025</span>
              </div>
            </div>

            {/* Documents */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-bold text-slate-800 mb-3">{isRo ? 'Documente Recente' : 'Recent Documents'}</h3>
              <div className="space-y-2">
                {SAMPLE_DOCUMENTS.slice(0, 4).map(d => (
                  <div key={d.id} className="flex items-center gap-3 py-1.5">
                    <FileText size={16} className="text-slate-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 truncate">{d.filename}</p>
                      <p className="text-xs text-slate-400">{d.provider} · {d.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl p-8 md:p-10 text-white text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-3">
            {isRo ? 'Pregătit să-ți vezi propriile date?' : 'Ready to see your own data?'}
          </h2>
          <p className="text-violet-200 mb-6 max-w-xl mx-auto">
            {isRo
              ? 'Conectează-ți conturile de la Regina Maria, Synevo sau încarcă PDF-uri. Primești analiză AI gratuită.'
              : 'Connect your Regina Maria, Synevo accounts or upload PDFs. Get free AI analysis.'}
          </p>
          <Link
            to="/login?mode=register"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-purple-700 rounded-xl font-bold text-lg hover:bg-purple-50 transition-colors shadow-lg"
          >
            {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
            <ArrowRight size={20} />
          </Link>
        </div>
      </div>
    </div>
  );
}
