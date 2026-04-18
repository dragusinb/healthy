import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, Upload, Loader2, CheckCircle, AlertTriangle, ArrowRight, Lock, ChevronDown, HeartPulse } from 'lucide-react';
import PublicNav from '../components/PublicNav';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import api from '../api/client';

export default function Analyzer() {
  const { i18n, t } = useTranslation();
  const isRo = i18n.language === 'ro';
  const [tab, setTab] = useState('text');
  const [text, setText] = useState('');
  const [email, setEmail] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const fileRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  usePageTitle(null, null, {
    title: isRo
      ? 'Analizator Gratuit Analize Medicale | Analize.Online'
      : 'Free Lab Results Analyzer | Analize.Online',
    description: isRo
      ? 'Lipește textul analizelor sau încarcă un PDF. AI extrage biomarkerii instant. Gratuit, fără cont.'
      : 'Paste your lab results text or upload a PDF. AI extracts biomarkers instantly. Free, no account needed.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: isRo ? 'Analizator Analize Medicale' : 'Lab Results Analyzer',
    url: 'https://analize.online/analyzer',
    applicationCategory: 'HealthApplication',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'RON' },
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
  });

  const analyze = async () => {
    setError('');
    setLoading(true);
    setResults(null);
    try {
      let res;
      if (tab === 'text') {
        res = await api.post('/analyzer/parse-text', { text, email: email || undefined });
      } else {
        const formData = new FormData();
        formData.append('file', file);
        if (email) formData.append('email', email);
        res = await api.post('/analyzer/parse-pdf', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      setResults(res.data);
    } catch (e) {
      const detail = e.response?.data?.detail || '';
      if (e.response?.status === 429) {
        setError(isRo
          ? 'Limita zilnică atinsă. Creează un cont gratuit pentru acces nelimitat.'
          : 'Daily limit reached. Create a free account for unlimited access.');
      } else {
        setError(detail || (isRo ? 'A apărut o eroare. Încearcă din nou.' : 'An error occurred. Please try again.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = tab === 'text' ? text.trim().length > 20 : !!file;

  const flagColor = (flag) => {
    if (flag === 'HIGH') return 'bg-red-100 text-red-700 border-red-200';
    if (flag === 'LOW') return 'bg-amber-100 text-amber-700 border-amber-200';
    return 'bg-green-100 text-green-700 border-green-200';
  };

  const flagLabel = (flag) => {
    if (flag === 'HIGH') return isRo ? 'RIDICAT' : 'HIGH';
    if (flag === 'LOW') return isRo ? 'SCĂZUT' : 'LOW';
    return 'NORMAL';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && f.name.toLowerCase().endsWith('.pdf')) {
      setFile(f);
      setTab('pdf');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-cyan-50 via-white to-white">
      <PublicNav />

      {/* Hero */}
      <div className="pt-28 pb-8 px-6 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <CheckCircle size={16} />
            {isRo ? '100% gratuit — fără cont necesar' : '100% free — no account needed'}
          </div>
          <h1 className="text-3xl md:text-5xl font-bold text-slate-800 mb-4">
            {isRo ? 'Analizator Gratuit Analize Medicale' : 'Free Lab Results Analyzer'}
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            {isRo
              ? 'Lipește textul analizelor sau încarcă un PDF. AI-ul nostru extrage biomarkerii instant și îi compară cu valorile de referință.'
              : 'Paste your lab results text or upload a PDF. Our AI extracts biomarkers instantly and compares them to reference ranges.'}
          </p>
        </div>
      </div>

      {/* Input area */}
      <div className="max-w-3xl mx-auto px-6 mb-12">
        {/* Tabs */}
        <div className="flex bg-slate-100 rounded-xl p-1 mb-6">
          <button
            onClick={() => setTab('text')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-all ${
              tab === 'text' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText size={16} />
            {isRo ? 'Lipește Text' : 'Paste Text'}
          </button>
          <button
            onClick={() => setTab('pdf')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-all ${
              tab === 'pdf' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Upload size={16} />
            {isRo ? 'Încarcă PDF' : 'Upload PDF'}
          </button>
        </div>

        {/* Text input */}
        {tab === 'text' && (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={isRo
              ? 'Lipește aici textul analizelor tale medicale...\n\nExemplu:\nHemoglobina  14.2 g/dL  (12 - 16)\nGlicemie  105 mg/dL  (74 - 106)\nColesterol Total  245 mg/dL  (0 - 200)'
              : 'Paste your lab results text here...\n\nExample:\nHemoglobin  14.2 g/dL  (12 - 16)\nGlucose  105 mg/dL  (74 - 106)\nTotal Cholesterol  245 mg/dL  (0 - 200)'}
            className="w-full h-64 p-4 rounded-xl border-2 border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 outline-none resize-none text-slate-700 text-sm font-mono transition-colors"
          />
        )}

        {/* PDF upload */}
        {tab === 'pdf' && (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
              dragOver ? 'border-cyan-500 bg-cyan-50' : file ? 'border-green-400 bg-green-50' : 'border-slate-300 hover:border-slate-400 hover:bg-slate-50'
            }`}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText size={24} className="text-green-600" />
                <span className="font-medium text-green-700">{file.name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="text-sm text-slate-400 hover:text-red-500 ml-2"
                >
                  ✕
                </button>
              </div>
            ) : (
              <>
                <Upload size={40} className="mx-auto text-slate-400 mb-3" />
                <p className="font-medium text-slate-600">
                  {isRo ? 'Trage PDF-ul aici sau click pentru a selecta' : 'Drag your PDF here or click to select'}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  {isRo ? 'Maxim 20 MB' : 'Maximum 20 MB'}
                </p>
              </>
            )}
          </div>
        )}

        {/* Email capture (optional) */}
        <div className="mt-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={isRo ? 'Email (opțional — pentru a salva rezultatele)' : 'Email (optional — to save your results)'}
            className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm text-slate-700 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-colors"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-start gap-2">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={analyze}
          disabled={!canSubmit || loading}
          className="mt-6 w-full py-4 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold text-lg hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              {isRo ? 'Se analizează...' : 'Analyzing...'}
            </>
          ) : (
            <>
              <HeartPulse size={20} />
              {isRo ? 'Analizează Rezultatele' : 'Analyze Results'}
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div className="max-w-3xl mx-auto px-6 pb-16">
          {/* Metadata */}
          {results.metadata && (results.metadata.provider || results.metadata.date) && (
            <div className="flex items-center gap-4 mb-6 text-sm text-slate-500">
              {results.metadata.provider && (
                <span className="bg-slate-100 px-3 py-1 rounded-full">{results.metadata.provider}</span>
              )}
              {results.metadata.date && (
                <span className="bg-slate-100 px-3 py-1 rounded-full">{results.metadata.date}</span>
              )}
              <span className="bg-teal-100 text-teal-700 px-3 py-1 rounded-full font-medium">
                {results.total_count} {isRo ? 'biomarkeri găsiți' : 'biomarkers found'}
              </span>
            </div>
          )}

          {/* Full results */}
          <div className="space-y-3">
            {results.results.map((r, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-800 truncate">{r.test_name}</p>
                  <p className="text-sm text-slate-500">
                    {r.value} {r.unit} {r.reference_range && <span className="text-slate-400">({isRo ? 'ref' : 'ref'}: {r.reference_range})</span>}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${flagColor(r.flags)}`}>
                  {flagLabel(r.flags)}
                </span>
              </div>
            ))}
          </div>

          {/* Gated results */}
          {results.gated_count > 0 && (
            <div className="mt-6 relative">
              {/* Blurred preview */}
              <div className="space-y-3 opacity-40 blur-[2px] pointer-events-none select-none">
                {results.gated_results.slice(0, 4).map((r, i) => (
                  <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between gap-4">
                    <div className="flex-1">
                      <p className="font-semibold text-slate-800">{r.test_name}</p>
                      <p className="text-sm text-slate-400">••••• •••</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${flagColor(r.flags)}`}>
                      {flagLabel(r.flags)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Overlay CTA */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-8 text-center max-w-md mx-4">
                  <Lock size={32} className="mx-auto text-slate-400 mb-4" />
                  <h3 className="text-lg font-bold text-slate-800 mb-2">
                    {isRo
                      ? `Încă ${results.gated_count} biomarkeri descoperiți`
                      : `${results.gated_count} more biomarkers found`}
                  </h3>
                  <p className="text-sm text-slate-500 mb-6">
                    {isRo
                      ? 'Creează un cont gratuit pentru a vedea toți biomarkerii ȘI a primi un plan alimentar personalizat cu rețete românești și listă de cumpărături.'
                      : 'Create a free account to see all biomarkers AND get a personalized meal plan with Romanian recipes and shopping list.'}
                  </p>
                  <Link
                    to="/login?mode=register"
                    className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg"
                  >
                    {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
                    <ArrowRight size={18} />
                  </Link>
                  <p className="text-xs text-slate-400 mt-3">
                    {isRo ? 'Gratuit — fără card bancar' : 'Free — no credit card'}
                  </p>
                  <Link
                    to="/nutrition-preview"
                    className="inline-flex items-center gap-1 text-xs text-teal-500 hover:text-teal-700 mt-2 transition-colors"
                  >
                    {isRo ? 'Sau încearcă planul alimentar gratuit →' : 'Or try the free meal plan →'}
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* All results shown, still show CTA */}
          {results.gated_count === 0 && results.total_count > 0 && (
            <div className="mt-8 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 text-white text-center">
              <h3 className="text-xl font-bold mb-2">
                {isRo
                  ? 'Vrei interpretare AI de la specialiști?'
                  : 'Want AI specialist interpretation?'}
              </h3>
              <p className="text-teal-100 mb-6">
                {isRo
                  ? 'Creează un cont gratuit pentru analize AI de la specialiști ȘI un plan alimentar personalizat cu rețete românești, listă de cumpărături și program de exerciții.'
                  : 'Create a free account for AI specialist analyses AND a personalized meal plan with Romanian recipes, shopping list and exercise program.'}
              </p>
              <Link
                to="/login?mode=register"
                className="inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-bold hover:bg-teal-50 transition-colors shadow-lg"
              >
                {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
                <ArrowRight size={18} />
              </Link>
            </div>
          )}
        </div>
      )}

      {/* How it works section */}
      {!results && (
        <div className="max-w-3xl mx-auto px-6 pb-16">
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                step: '1',
                title: isRo ? 'Lipește sau încarcă' : 'Paste or upload',
                desc: isRo ? 'Lipește textul analizelor sau încarcă PDF-ul de la laborator.' : 'Paste your lab results text or upload the PDF from your lab.',
              },
              {
                step: '2',
                title: isRo ? 'AI extrage instant' : 'AI extracts instantly',
                desc: isRo ? 'AI-ul nostru identifică biomarkerii, valorile și intervalele de referință.' : 'Our AI identifies biomarkers, values and reference ranges.',
              },
              {
                step: '3',
                title: isRo ? 'Vezi rezultatele' : 'See your results',
                desc: isRo ? 'Primești rezultatele colorate: Normal, Ridicat sau Scăzut.' : 'Get color-coded results: Normal, High or Low.',
              },
            ].map((item) => (
              <div key={item.step} className="bg-white rounded-xl border border-slate-200 p-6 text-center">
                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-4 text-white font-bold">
                  {item.step}
                </div>
                <h3 className="font-bold text-slate-800 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
