import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  UtensilsCrossed, Upload, Loader2, CheckCircle, AlertTriangle,
  ArrowRight, ShoppingCart, Dumbbell, Activity, Leaf, Calendar,
  FileText, ChevronDown, Crown
} from 'lucide-react';
import PublicNav from '../components/PublicNav';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import api from '../api/client';

export default function NutritionPreview() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';
  const [text, setText] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const resultsRef = useRef(null);

  usePageTitle(null, null, {
    title: isRo
      ? 'Preview Plan Alimentar Personalizat | Analize.Online'
      : 'Personalized Meal Plan Preview | Analize.Online',
    description: isRo
      ? 'Lipește analizele tale de sânge și primești un plan alimentar de 3 zile cu rețete românești, listă de cumpărături și program de exerciții. Gratuit, fără cont.'
      : 'Paste your blood test results and get a 3-day meal plan with Romanian recipes, shopping list and exercise program. Free, no account needed.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: isRo ? 'Preview Plan Alimentar' : 'Meal Plan Preview',
    url: 'https://analize.online/nutrition-preview',
    applicationCategory: 'HealthApplication',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'RON' },
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
  });

  const generate = async () => {
    setError('');
    setLoading(true);
    setResults(null);
    try {
      const res = await api.post('/analyzer/nutrition-preview', { text, email: email || undefined });
      setResults(res.data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || (isRo ? 'Eroare la generare. Încearcă din nou.' : 'Generation error. Try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white">
      <PublicNav />

      <div className="max-w-4xl mx-auto px-4 pt-28 pb-16">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <UtensilsCrossed size={16} />
            {isRo ? 'Gratuit • Fără cont' : 'Free • No account needed'}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800 mb-3">
            {isRo ? 'Previzualizare Plan Alimentar' : 'Meal Plan Preview'}
          </h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            {isRo
              ? 'Lipește rezultatele analizelor tale de sânge și primești instant un plan de 3 zile cu rețete românești, listă de cumpărături și program de exerciții.'
              : 'Paste your blood test results and instantly get a 3-day plan with Romanian recipes, shopping list and exercise program.'}
          </p>
        </div>

        {/* Input area */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6 mb-8">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            {isRo ? 'Lipește aici rezultatele analizelor tale:' : 'Paste your lab results here:'}
          </label>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={isRo
              ? 'Exemplu:\nColesterol total: 245 mg/dL (ref: <200)\nHDL: 42 mg/dL (ref: >40)\nLDL: 165 mg/dL (ref: <130)\nVitamina D: 18 ng/mL (ref: 30-100)\nGlicemie: 98 mg/dL (ref: 70-105)\nHemoglobina: 14.2 g/dL (ref: 12-17)'
              : 'Example:\nTotal cholesterol: 245 mg/dL (ref: <200)\nHDL: 42 mg/dL (ref: >40)\nLDL: 165 mg/dL (ref: <130)\nVitamin D: 18 ng/mL (ref: 30-100)\nGlucose: 98 mg/dL (ref: 70-105)\nHemoglobin: 14.2 g/dL (ref: 12-17)'}
            rows={8}
            className="w-full border border-slate-200 rounded-xl p-4 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent resize-none"
          />
          <div className="flex flex-col sm:flex-row gap-3 mt-4">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder={isRo ? 'Email (opțional, pentru planul complet)' : 'Email (optional, for full plan)'}
              className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              onClick={generate}
              disabled={loading || text.trim().length < 20}
              className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  {isRo ? 'Se generează...' : 'Generating...'}
                </>
              ) : (
                <>
                  <UtensilsCrossed size={18} />
                  {isRo ? 'Generează Plan' : 'Generate Plan'}
                </>
              )}
            </button>
          </div>
          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}
        </div>

        {/* Results */}
        {results && (
          <div ref={resultsRef} className="space-y-6">
            {/* Summary */}
            {results.summary && (
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-100">
                <p className="text-sm font-semibold text-amber-700 mb-1 flex items-center gap-2">
                  <Activity size={16} />
                  {isRo ? `${results.biomarker_count} biomarkeri detectați` : `${results.biomarker_count} biomarkers detected`}
                </p>
                <p className="text-slate-700">{results.summary}</p>
              </div>
            )}

            {/* Biomarker flags */}
            {results.biomarker_flags?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <FileText size={20} className="text-slate-400" />
                  {isRo ? 'Biomarkeri relevanți' : 'Relevant Biomarkers'}
                </h2>
                <div className="space-y-2">
                  {results.biomarker_flags.map((b, i) => (
                    <div key={i} className={`flex items-center justify-between p-3 rounded-lg ${
                      b.status === 'high' ? 'bg-red-50' : b.status === 'low' ? 'bg-amber-50' : 'bg-green-50'
                    }`}>
                      <div>
                        <span className="text-sm font-medium text-slate-700">{b.name}</span>
                        <span className="text-sm text-slate-500 ml-2">{b.value}</span>
                      </div>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        b.status === 'high' ? 'bg-red-100 text-red-600' :
                        b.status === 'low' ? 'bg-amber-100 text-amber-600' :
                        'bg-green-100 text-green-600'
                      }`}>
                        {b.status === 'high' ? (isRo ? 'CRESCUT' : 'HIGH') :
                         b.status === 'low' ? (isRo ? 'SCĂZUT' : 'LOW') :
                         (isRo ? 'NORMAL' : 'NORMAL')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3-Day Meal Plan */}
            {results.meal_plan?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <UtensilsCrossed size={20} className="text-amber-500" />
                  {isRo ? 'Plan alimentar — 3 zile' : '3-Day Meal Plan'}
                </h2>
                <div className="space-y-4">
                  {results.meal_plan.map((day, i) => (
                    <div key={i} className="border border-slate-100 rounded-xl p-4">
                      <p className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <Calendar size={16} className="text-amber-500" />
                        {day.day}
                      </p>
                      <div className="space-y-2">
                        {day.meals?.map((meal, j) => (
                          <div key={j} className="bg-slate-50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-semibold text-slate-700">{meal.meal}</span>
                              <span className="text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">{meal.calories}</span>
                            </div>
                            {meal.items?.map((item, k) => (
                              <p key={k} className="text-sm text-slate-500 ml-1">• {item}</p>
                            ))}
                            {meal.notes && (
                              <p className="text-xs text-teal-600 mt-1 italic">{meal.notes}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Blurred days 4-7 */}
                <div className="relative mt-4">
                  <div className="border border-slate-100 rounded-xl p-4 blur-[3px] select-none">
                    <p className="font-bold text-slate-400 mb-2">{isRo ? 'Ziua 4 — Joi' : 'Day 4 — Thursday'}</p>
                    <div className="space-y-2 text-sm text-slate-300">
                      <p>{isRo ? 'Mic dejun: Clătite cu brânză și miere de albine...' : 'Breakfast: Cheese pancakes with honey...'}</p>
                      <p>{isRo ? 'Prânz: Ghiveci de legume cu orez integral...' : 'Lunch: Vegetable stew with brown rice...'}</p>
                      <p>{isRo ? 'Cină: File de curcan cu ciuperci și smântână...' : 'Dinner: Turkey fillet with mushroom cream...'}</p>
                    </div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Link
                      to="/login?mode=register"
                      className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-semibold shadow-lg hover:from-amber-600 hover:to-orange-600 transition-all flex items-center gap-2"
                    >
                      <Crown size={14} />
                      {isRo ? 'Creează cont gratuit pentru zilele 4-7' : 'Create free account for days 4-7'}
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* Shopping List */}
            {results.shopping_list?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <ShoppingCart size={20} className="text-teal-500" />
                  {isRo ? 'Listă de cumpărături' : 'Shopping List'}
                </h2>
                <div className="grid sm:grid-cols-2 gap-4">
                  {results.shopping_list.map((cat, i) => (
                    <div key={i} className="bg-slate-50 rounded-xl p-4">
                      <p className="text-sm font-bold text-slate-700 mb-2">{cat.category}</p>
                      <ul className="space-y-1">
                        {cat.items?.map((item, j) => (
                          <li key={j} className="text-sm text-slate-500 flex items-center gap-2">
                            <CheckCircle size={12} className="text-teal-400 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Exercise */}
            {results.exercise?.sections?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Dumbbell size={20} className="text-violet-500" />
                  {results.exercise.title || (isRo ? 'Program exerciții' : 'Exercise Program')}
                </h2>
                <div className="space-y-4">
                  {results.exercise.sections.map((section, i) => (
                    <div key={i} className="bg-violet-50 rounded-xl p-4">
                      <p className="text-sm font-bold text-violet-700 mb-2 flex items-center gap-2">
                        {i === 0 ? <Activity size={14} /> : i === section.length - 1 ? <Leaf size={14} /> : <Dumbbell size={14} />}
                        {section.name} — {section.duration}
                      </p>
                      <ul className="space-y-1">
                        {section.exercises?.map((ex, j) => (
                          <li key={j} className="text-sm text-slate-600 flex justify-between">
                            <span>{ex.name}</span>
                            {ex.sets && <span className="text-violet-500 font-medium">{ex.sets}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Final CTA */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl p-8 text-center text-white">
              <h3 className="text-xl font-bold mb-2">
                {isRo ? 'Vrei planul complet de 7 zile?' : 'Want the full 7-day plan?'}
              </h3>
              <p className="text-amber-100 mb-5">
                {isRo
                  ? 'Creează un cont gratuit și primești 30 zile de acces Premium cu plan alimentar complet, rețete detaliate, listă de cumpărături și program de exerciții — regenerate săptămânal.'
                  : 'Create a free account and get 30 days of Premium access with a full meal plan, detailed recipes, shopping list and exercise program — regenerated weekly.'}
              </p>
              <Link
                to="/login?mode=register"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-amber-600 rounded-xl font-bold text-lg hover:bg-amber-50 transition-all shadow-lg"
              >
                {isRo ? 'Înregistrare Gratuită — 30 Zile Premium' : 'Free Signup — 30 Days Premium'}
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-slate-800 text-slate-400 py-8 px-4 text-center text-sm">
        <p>© {new Date().getFullYear()} Analize.Online. {isRo ? 'Toate drepturile rezervate.' : 'All rights reserved.'}</p>
        <p className="mt-1 text-xs text-slate-500">
          {isRo ? 'Acest instrument nu înlocuiește sfatul medical profesionist.' : 'This tool does not replace professional medical advice.'}
        </p>
      </footer>
    </div>
  );
}
