import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  UtensilsCrossed, Upload, Loader2, CheckCircle, AlertTriangle,
  ArrowRight, ShoppingCart, Dumbbell, Activity, Leaf, Calendar,
  FileText, ChevronDown, Crown, Heart, Droplets, Sun, Flame, Brain,
  TrendingDown, Shield, Zap, ChefHat, Apple
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

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: isRo ? 'Ce include planul alimentar personalizat?' : 'What does the personalized meal plan include?',
        acceptedAnswer: { '@type': 'Answer', text: isRo
          ? 'Planul include un meniu pe 7 zile cu rețete românești (ciorbă, sarmale, tocăniță), lista de cumpărături organizată pe categorii, și un program de exerciții fizice — totul personalizat pe baza biomarkerilor din analizele de sânge.'
          : 'The plan includes a 7-day menu with Romanian recipes, a shopping list organized by category, and an exercise program — all personalized based on biomarkers from blood tests.' },
      },
      {
        '@type': 'Question',
        name: isRo ? 'Este gratuit planul alimentar?' : 'Is the meal plan free?',
        acceptedAnswer: { '@type': 'Answer', text: isRo
          ? 'Da, preview-ul de 3 zile este complet gratuit, fără cont și fără card bancar. Pentru planul complet de 7 zile cu rețete detaliate, poți crea un cont gratuit cu 30 zile de acces Premium.'
          : 'Yes, the 3-day preview is completely free, no account or credit card needed. For the full 7-day plan, create a free account with 30 days of Premium access.' },
      },
      {
        '@type': 'Question',
        name: isRo ? 'Ce analize de sânge pot folosi?' : 'What blood tests can I use?',
        acceptedAnswer: { '@type': 'Answer', text: isRo
          ? 'Orice analize de sânge de la Regina Maria, Synevo, MedLife, Sanador sau alt laborator. Copiezi valorile din PDF și le lipești. AI-ul recunoaște automat biomarkerii.'
          : 'Any blood tests from Regina Maria, Synevo, MedLife, Sanador or any other lab. Copy the values from the PDF and paste them. AI automatically recognizes biomarkers.' },
      },
      {
        '@type': 'Question',
        name: isRo ? 'De ce rețete românești?' : 'Why Romanian recipes?',
        acceptedAnswer: { '@type': 'Answer', text: isRo
          ? 'Un plan alimentar pe care nu-l poți găti nu ajută. Folosim ingrediente din supermarketurile românești și rețete tradiționale adaptate sănătos: ciorbă, sarmale, tocăniță, grătar.'
          : 'A meal plan you can\'t cook is useless. We use ingredients from Romanian supermarkets and traditional recipes adapted healthily: soups, sarmale, stews, grilled dishes.' },
      },
    ],
  }, 'nutrition-preview-faq');

  const isValidEmail = (e) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

  const generate = async () => {
    if (!isValidEmail(email)) {
      setError(isRo ? 'Te rugăm introdu adresa de email pentru a primi planul.' : 'Please enter your email to receive the plan.');
      return;
    }
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
              placeholder={isRo ? 'Adresa ta de email *' : 'Your email address *'}
              required
              className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              onClick={generate}
              disabled={loading || text.trim().length < 20 || !email.trim()}
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

      {/* What You Get Section */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-800 text-center mb-3">
            {isRo ? 'Ce primești din planul alimentar?' : 'What do you get from the meal plan?'}
          </h2>
          <p className="text-slate-500 text-center mb-10 max-w-2xl mx-auto">
            {isRo
              ? 'AI-ul analizează fiecare biomarker din analizele tale și creează un plan complet adaptat nevoilor tale specifice.'
              : 'The AI analyzes every biomarker from your tests and creates a plan fully adapted to your specific needs.'}
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: UtensilsCrossed,
                color: 'from-amber-500 to-orange-500',
                bg: 'bg-amber-50',
                title: isRo ? 'Plan alimentar 7 zile' : '7-Day Meal Plan',
                desc: isRo
                  ? '21 de mese complete cu rețete românești — ciorbă de legume, sarmale, tocăniță de pui, somon la cuptor. Fiecare masă cu porții exacte în grame și calorii calculate.'
                  : '21 complete meals with Romanian recipes — vegetable soup, sarmale, chicken stew, baked salmon. Each meal with exact portions in grams and calculated calories.',
              },
              {
                icon: ShoppingCart,
                color: 'from-teal-500 to-emerald-500',
                bg: 'bg-teal-50',
                title: isRo ? 'Listă de cumpărături' : 'Shopping List',
                desc: isRo
                  ? 'Organizată pe categorii (lactate, legume, carne, cereale) cu cantități exacte. Mergi la Carrefour, Mega Image sau Lidl cu lista gata făcută.'
                  : 'Organized by category (dairy, vegetables, meat, grains) with exact quantities. Go to the supermarket with a ready-made list.',
              },
              {
                icon: Dumbbell,
                color: 'from-violet-500 to-purple-500',
                bg: 'bg-violet-50',
                title: isRo ? 'Program de exerciții' : 'Exercise Program',
                desc: isRo
                  ? 'Adaptat stării tale de sănătate. Dacă ai colesterol crescut, primești exerciții cardio. Dacă ai deficiențe, program de rezistență. Cu încălzire și revenire.'
                  : 'Adapted to your health status. High cholesterol gets cardio exercises. Deficiencies get resistance training. With warm-up and cool-down.',
              },
            ].map((item, i) => (
              <div key={i} className={`${item.bg} rounded-2xl p-6 border border-slate-100`}>
                <div className={`w-12 h-12 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center mb-4 shadow-lg`}>
                  <item.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Nutrition by Biomarker Section */}
      <section className="py-16 px-4 bg-gradient-to-b from-white to-amber-50/30">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-800 text-center mb-3">
            {isRo ? 'Ce mănânci în funcție de analizele tale?' : 'What to eat based on your blood tests?'}
          </h2>
          <p className="text-slate-500 text-center mb-10 max-w-2xl mx-auto">
            {isRo
              ? 'Fiecare problemă din analize cere o abordare nutrițională diferită. Iată câteva exemple:'
              : 'Each issue in your blood tests requires a different nutritional approach. Here are some examples:'}
          </p>
          <div className="grid md:grid-cols-2 gap-5">
            {[
              {
                icon: Heart, color: 'text-red-500', bg: 'bg-red-50',
                condition: isRo ? 'Colesterol LDL crescut' : 'High LDL Cholesterol',
                foods: isRo
                  ? 'Ovăz, nuci, somon, ulei de măsline, fasole, avocado. Reduce: carne roșie grasă, unt, brânzeturi grase, mezeluri.'
                  : 'Oats, walnuts, salmon, olive oil, beans, avocado. Reduce: fatty red meat, butter, fatty cheese, cold cuts.',
                why: isRo
                  ? 'Beta-glucanul din ovăz și omega-3 din pește scad LDL-ul și cresc HDL-ul.'
                  : 'Beta-glucan from oats and omega-3 from fish lower LDL and raise HDL.',
              },
              {
                icon: Sun, color: 'text-amber-500', bg: 'bg-amber-50',
                condition: isRo ? 'Vitamina D scăzută' : 'Low Vitamin D',
                foods: isRo
                  ? 'Somon, sardine, ouă (gălbenuș), ciuperci, iaurt fortificat. Plus: 15-20 min soare/zi.'
                  : 'Salmon, sardines, eggs (yolk), mushrooms, fortified yogurt. Plus: 15-20 min sun/day.',
                why: isRo
                  ? 'Peștele gras și gălbenușul sunt cele mai bogate surse alimentare de vitamina D3.'
                  : 'Fatty fish and egg yolk are the richest dietary sources of vitamin D3.',
              },
              {
                icon: Droplets, color: 'text-rose-500', bg: 'bg-rose-50',
                condition: isRo ? 'Hemoglobină / Fier scăzut' : 'Low Hemoglobin / Iron',
                foods: isRo
                  ? 'Ficăței de pui, carne roșie, spanac, linte, sfeclă roșie. Combină cu vitamina C (lămâie, ardei) pentru absorbție.'
                  : 'Chicken liver, red meat, spinach, lentils, beetroot. Combine with vitamin C (lemon, peppers) for absorption.',
                why: isRo
                  ? 'Fierul hem (din carne) se absoarbe de 2-3x mai bine decât cel non-hem (din plante).'
                  : 'Heme iron (from meat) absorbs 2-3x better than non-heme iron (from plants).',
              },
              {
                icon: Flame, color: 'text-orange-500', bg: 'bg-orange-50',
                condition: isRo ? 'Glicemie crescută / Pre-diabet' : 'High Blood Sugar / Pre-diabetes',
                foods: isRo
                  ? 'Legume verzi, quinoa, orez brun, pește, nuci, scorțișoară. Evită: zahăr, pâine albă, sucuri, dulciuri.'
                  : 'Green vegetables, quinoa, brown rice, fish, nuts, cinnamon. Avoid: sugar, white bread, juices, sweets.',
                why: isRo
                  ? 'Fibrele și proteinele încetinesc absorbția glucozei. Scorțișoara poate îmbunătăți sensibilitatea la insulină.'
                  : 'Fiber and protein slow glucose absorption. Cinnamon may improve insulin sensitivity.',
              },
              {
                icon: Zap, color: 'text-yellow-500', bg: 'bg-yellow-50',
                condition: isRo ? 'Trigliceride crescute' : 'High Triglycerides',
                foods: isRo
                  ? 'Pește gras (somon, macrou), nuci, semințe de in, avocado. Elimină: alcool, zahăr, carbo rafinați.'
                  : 'Fatty fish (salmon, mackerel), walnuts, flax seeds, avocado. Eliminate: alcohol, sugar, refined carbs.',
                why: isRo
                  ? 'Omega-3 reduce trigliceridele cu 15-30%. Zahărul și alcoolul le cresc direct.'
                  : 'Omega-3 reduces triglycerides by 15-30%. Sugar and alcohol directly increase them.',
              },
              {
                icon: Shield, color: 'text-emerald-500', bg: 'bg-emerald-50',
                condition: isRo ? 'Transaminaze crescute (ficat)' : 'High Transaminases (liver)',
                foods: isRo
                  ? 'Broccoli, usturoi, ceai verde, curcuma, grapefruit. Evită complet: alcool, alimente prăjite, zahăr adăugat.'
                  : 'Broccoli, garlic, green tea, turmeric, grapefruit. Completely avoid: alcohol, fried foods, added sugar.',
                why: isRo
                  ? 'Antioxidanții din legumele crucifere protejează hepatocitele. Alcoolul e toxic direct pentru ficat.'
                  : 'Antioxidants from cruciferous vegetables protect liver cells. Alcohol is directly toxic to the liver.',
              },
            ].map((item, i) => (
              <div key={i} className={`${item.bg} rounded-xl p-5 border border-slate-100`}>
                <div className="flex items-center gap-3 mb-3">
                  <item.icon size={22} className={item.color} />
                  <h3 className="font-bold text-slate-800">{item.condition}</h3>
                </div>
                <p className="text-sm text-slate-700 mb-2">
                  <span className="font-semibold">{isRo ? 'Mănâncă: ' : 'Eat: '}</span>
                  {item.foods}
                </p>
                <p className="text-xs text-slate-500 italic">{item.why}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <p className="text-slate-500 mb-4">
              {isRo
                ? 'Dar fiecare persoană e diferită. Planul tău trebuie să țină cont de TOATE valorile, nu doar de una.'
                : "But everyone is different. Your plan needs to consider ALL your values, not just one."}
            </p>
            <a
              href="#top"
              onClick={e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/20"
            >
              {isRo ? 'Lipește analizele tale mai sus' : 'Paste your results above'}
              <ArrowRight size={18} />
            </a>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-800 text-center mb-10">
            {isRo ? 'Cum funcționează?' : 'How does it work?'}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                icon: FileText,
                title: isRo ? 'Lipești analizele' : 'Paste your results',
                desc: isRo
                  ? 'Copiezi valorile din PDF-ul de analize (de la Regina Maria, Synevo, MedLife sau Sanador) și le lipești în caseta de mai sus.'
                  : 'Copy the values from your lab results PDF (from Regina Maria, Synevo, MedLife or Sanador) and paste them above.',
              },
              {
                step: '2',
                icon: Brain,
                title: isRo ? 'AI analizează' : 'AI analyzes',
                desc: isRo
                  ? 'Inteligența artificială identifică biomarkerii, verifică valorile și determină ce nutrienți ai nevoie și ce trebuie evitat.'
                  : 'AI identifies biomarkers, checks values and determines what nutrients you need and what to avoid.',
              },
              {
                step: '3',
                icon: ChefHat,
                title: isRo ? 'Primești planul' : 'Get your plan',
                desc: isRo
                  ? 'În 30 de secunde primești un plan alimentar cu rețete românești, listă de cumpărături și program de exerciții — personalizat pe analizele tale.'
                  : 'In 30 seconds you get a meal plan with Romanian recipes, shopping list and exercise program — personalized to your results.',
              },
            ].map((item, i) => (
              <div key={i} className="text-center">
                <div className="relative inline-flex">
                  <div className="w-16 h-16 bg-gradient-to-br from-amber-100 to-orange-100 rounded-2xl flex items-center justify-center mb-4 mx-auto">
                    <item.icon size={28} className="text-amber-600" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-7 h-7 bg-amber-500 text-white rounded-full flex items-center justify-center text-sm font-bold">{item.step}</span>
                </div>
                <h3 className="font-bold text-slate-800 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-800 text-center mb-8">
            {isRo ? 'Întrebări frecvente' : 'Frequently Asked Questions'}
          </h2>
          <div className="space-y-3">
            {[
              {
                q: isRo ? 'Este gratuit?' : 'Is it free?',
                a: isRo
                  ? 'Da, preview-ul de 3 zile este complet gratuit, fără cont și fără card bancar. Pentru planul complet de 7 zile cu rețete detaliate, poți crea un cont gratuit cu 30 zile de acces Premium.'
                  : 'Yes, the 3-day preview is completely free, no account and no credit card needed. For the full 7-day plan with detailed recipes, you can create a free account with 30 days of Premium access.',
              },
              {
                q: isRo ? 'Ce analize pot folosi?' : 'What lab results can I use?',
                a: isRo
                  ? 'Orice analize de sânge de la orice laborator din România (Regina Maria, Synevo, MedLife, Sanador) sau din afara țării. Copiezi valorile din PDF și le lipești. AI-ul recunoaște automat biomarkerii.'
                  : 'Any blood tests from any lab in Romania (Regina Maria, Synevo, MedLife, Sanador) or abroad. Copy the values from the PDF and paste them. AI automatically recognizes biomarkers.',
              },
              {
                q: isRo ? 'Cât de precise sunt recomandările?' : 'How accurate are the recommendations?',
                a: isRo
                  ? 'Planul alimentar este generat de AI bazat pe cercetări nutriționale validate științific. Nu înlocuiește sfatul unui medic sau nutriționist, dar oferă o direcție clară bazată pe valorile tale reale.'
                  : 'The meal plan is AI-generated based on scientifically validated nutritional research. It doesn\'t replace a doctor or nutritionist, but provides clear direction based on your real values.',
              },
              {
                q: isRo ? 'Datele mele sunt în siguranță?' : 'Is my data safe?',
                a: isRo
                  ? 'Da. Textul analizelor este procesat de AI și nu este stocat permanent. Nu cerem date personale, iar dacă creezi cont, toate datele sunt criptate end-to-end cu cheie derivată din parola ta.'
                  : 'Yes. The test text is processed by AI and not permanently stored. We don\'t ask for personal data, and if you create an account, all data is encrypted end-to-end with a key derived from your password.',
              },
              {
                q: isRo ? 'De ce rețete românești?' : 'Why Romanian recipes?',
                a: isRo
                  ? 'Pentru că un plan alimentar pe care nu-l poți găti nu ajută la nimic. Folosim ingrediente disponibile în supermarketurile din România și rețete tradiționale adaptate: ciorbă, sarmale, tocăniță, grătar — preparate în mod sănătos.'
                  : 'Because a meal plan you can\'t cook is useless. We use ingredients available in Romanian supermarkets and adapted traditional recipes: soups, sarmale, stews, grilled dishes — prepared in a healthy way.',
              },
            ].map((item, i) => (
              <details key={i} className="group bg-white rounded-xl border border-slate-100 shadow-sm">
                <summary className="flex items-center justify-between p-4 cursor-pointer text-slate-800 font-medium hover:text-amber-600 transition-colors">
                  {item.q}
                  <ChevronDown size={18} className="text-slate-400 group-open:rotate-180 transition-transform" />
                </summary>
                <p className="px-4 pb-4 text-sm text-slate-500 leading-relaxed">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 px-4 bg-gradient-to-r from-amber-500 to-orange-500">
        <div className="max-w-3xl mx-auto text-center text-white">
          <h2 className="text-2xl md:text-3xl font-bold mb-3">
            {isRo ? 'Planul tău alimentar personalizat te așteaptă' : 'Your personalized meal plan is waiting'}
          </h2>
          <p className="text-amber-100 mb-6">
            {isRo
              ? 'Lipește analizele de sânge și primești în 30 de secunde un plan cu rețete românești, listă de cumpărături și exerciții — totul bazat pe valorile tale reale.'
              : 'Paste your blood tests and in 30 seconds get a plan with Romanian recipes, shopping list and exercises — all based on your real values.'}
          </p>
          <a
            href="#top"
            onClick={e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-amber-600 rounded-xl font-bold text-lg hover:bg-amber-50 transition-all shadow-lg"
          >
            {isRo ? 'Încearcă Acum — Gratuit' : 'Try Now — Free'}
            <ArrowRight size={20} />
          </a>
        </div>
      </section>

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
