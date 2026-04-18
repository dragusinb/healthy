import React, { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HeartPulse, Shield, Brain, Zap, FileText, TrendingUp,
  CheckCircle, ArrowRight, Lock, Users, Clock, Smartphone,
  Globe, Star, ChevronRight, Activity, Stethoscope,
  UtensilsCrossed, Dumbbell, ShoppingCart, ChefHat, Leaf, Apple, BookOpen, FlaskConical, Calendar,
  Menu, X, Eye
} from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import api from '../api/client';

function AnimatedCounter({ end, duration = 2000 }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const start = Date.now();
          const tick = () => {
            const elapsed = Date.now() - start;
            const progress = Math.min(elapsed / duration, 1);
            setCount(Math.floor(progress * end));
            if (progress < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration]);

  return <span ref={ref}>{count}+</span>;
}

export default function Home() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const isRomanian = i18n.language === 'ro';
  const [blogArticles, setBlogArticles] = useState([]);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [publicStats, setPublicStats] = useState(null);

  usePageTitle(null, isRomanian
    ? 'Plan Alimentar Personalizat din Analize de Sânge'
    : 'Personalized Meal Plan from Blood Tests');

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: isRomanian ? 'Ce include planul alimentar personalizat?' : 'What does the personalized meal plan include?',
        acceptedAnswer: { '@type': 'Answer', text: isRomanian
          ? 'Planul include un meniu pe 7 zile cu rețete românești (ciorbă, sarmale, tocăniță), lista de cumpărături organizată pe categorii pentru Carrefour, și un program de exerciții fizice — totul personalizat pe baza biomarkerilor din analizele tale de sânge.'
          : 'The plan includes a 7-day menu with Romanian recipes (soups, sarmale, stews), a shopping list organized by category for Carrefour, and an exercise program — all personalized based on biomarkers from your blood tests.' },
      },
      {
        '@type': 'Question',
        name: isRomanian ? 'Cum funcționează generarea planului alimentar?' : 'How does meal plan generation work?',
        acceptedAnswer: { '@type': 'Answer', text: isRomanian
          ? 'Conectezi contul tău de la Regina Maria, Synevo, MedLife sau Sanador. AI extrage biomarkerii din analizele tale și generează un plan alimentar personalizat cu rețete românești adaptate nevoilor tale nutriționale specifice.'
          : 'You connect your account from Regina Maria, Synevo, MedLife or Sanador. AI extracts biomarkers from your tests and generates a personalized meal plan with Romanian recipes adapted to your specific nutritional needs.' },
      },
      {
        '@type': 'Question',
        name: isRomanian ? 'Este gratuit?' : 'Is it free?',
        acceptedAnswer: { '@type': 'Answer', text: isRomanian
          ? 'Da, primești 30 de zile de acces Premium gratuit la înregistrare, fără card bancar. Include plan alimentar complet, rețete, listă de cumpărături și program de exerciții.'
          : 'Yes, you get 30 days of free Premium access when you sign up, no credit card needed. Includes full meal plan, recipes, shopping list and exercise program.' },
      },
    ],
  }, 'home-faq');

  useEffect(() => {
    api.get('/blog/articles?limit=3').then(res => setBlogArticles(res.data.articles || [])).catch(() => {});
    api.get('/public/stats').then(res => setPublicStats(res.data)).catch(() => {});
  }, []);

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'ro' ? 'en' : 'ro');
  };

  return (
    <div className="min-h-screen bg-white">
      <a href="#hero" className="absolute z-[100] top-2 left-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium shadow-lg opacity-0 focus:opacity-100 pointer-events-none focus:pointer-events-auto transition-opacity -translate-y-full focus:translate-y-0" tabIndex={0}>
        {isRomanian ? 'Sari la conținut' : 'Skip to main content'}
      </a>
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-lg z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center">
              <HeartPulse className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-800">Analize.Online</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
            >
              <Globe size={14} />
              {i18n.language.toUpperCase()}
            </button>
            <Link
              to="/biomarker"
              className="text-slate-600 hover:text-slate-800 font-medium hidden md:block"
            >
              {isRomanian ? 'Biomarkeri' : 'Biomarkers'}
            </Link>
            <Link
              to="/blog"
              className="text-slate-600 hover:text-slate-800 font-medium hidden md:block"
            >
              Blog
            </Link>
            <Link
              to="/pricing"
              className="text-slate-600 hover:text-slate-800 font-medium hidden md:block"
            >
              {isRomanian ? 'Prețuri' : 'Pricing'}
            </Link>
            <Link
              to="/nutrition-preview"
              className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg text-sm font-medium hover:from-amber-600 hover:to-orange-600 transition-all shadow-sm"
            >
              {isRomanian ? 'Plan Nutrițional Gratuit' : 'Free Nutrition Plan'}
            </Link>
            <Link
              to="/login"
              className="text-slate-600 hover:text-slate-800 font-medium hidden md:block"
            >
              {isRomanian ? 'Autentificare' : 'Login'}
            </Link>
            <Link
              to="/login?mode=register"
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md shadow-cyan-500/20 hidden sm:block"
            >
              {isRomanian ? 'Înregistrare' : 'Sign Up'}
            </Link>
            <button
              onClick={() => setMobileNavOpen(!mobileNavOpen)}
              className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center text-slate-600 hover:text-slate-800"
              aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'}
            >
              {mobileNavOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
        {mobileNavOpen && (
          <div className="md:hidden bg-white border-t border-slate-100 px-6 py-4 space-y-3">
            <Link to="/biomarker" onClick={() => setMobileNavOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
              {isRomanian ? 'Biomarkeri' : 'Biomarkers'}
            </Link>
            <Link to="/blog" onClick={() => setMobileNavOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
              Blog
            </Link>
            <Link to="/pricing" onClick={() => setMobileNavOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
              {isRomanian ? 'Prețuri' : 'Pricing'}
            </Link>
            <Link to="/nutrition-preview" onClick={() => setMobileNavOpen(false)} className="block text-amber-600 hover:text-amber-800 font-medium py-2">
              {isRomanian ? 'Plan Nutrițional Gratuit' : 'Free Nutrition Plan'}
            </Link>
            <Link to="/login" onClick={() => setMobileNavOpen(false)} className="block text-slate-600 hover:text-slate-800 font-medium py-2">
              {isRomanian ? 'Autentificare' : 'Login'}
            </Link>
            <Link
              to="/login?mode=register"
              onClick={() => setMobileNavOpen(false)}
              className="block w-full text-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium"
            >
              {isRomanian ? 'Înregistrare' : 'Sign Up'}
            </Link>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section id="hero" className="pt-32 pb-20 px-6 bg-gradient-to-b from-cyan-50 via-white to-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <UtensilsCrossed size={16} />
                {isRomanian ? 'Rețete românești bazate pe analizele tale' : 'Romanian recipes based on your lab results'}
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-800 leading-tight mb-6">
                {isRomanian ? (
                  <>Plan alimentar personalizat, bazat pe <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500">analizele tale de sânge</span></>
                ) : (
                  <>Personalized meal plan, based on <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500">your real blood tests</span></>
                )}
              </h1>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed">
                {isRomanian
                  ? 'Primești un plan de 7 zile cu rețete românești (ciorbă, sarmale, tocăniță), lista de cumpărături pentru Carrefour și program de exerciții — totul generat de AI, bazat pe analizele tale reale de la Regina Maria, Synevo, MedLife sau Sanador.'
                  : 'Get a 7-day meal plan with Romanian recipes, a Carrefour shopping list and an exercise program — all AI-generated from your real lab results from Regina Maria, Synevo, MedLife or Sanador.'}
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/login"
                  className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold text-lg hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/30 flex items-center justify-center gap-2"
                >
                  {isRomanian ? 'Încearcă 30 Zile Gratuit' : 'Try 30 Days Free'}
                  <ArrowRight size={20} />
                </Link>
                <a
                  href="#sample-plan"
                  className="px-8 py-4 bg-white border-2 border-slate-200 text-slate-700 rounded-xl font-semibold text-lg hover:border-teal-300 hover:text-teal-600 transition-all flex items-center justify-center gap-2"
                >
                  {isRomanian ? 'Vezi un Exemplu' : 'See an Example'}
                  <Eye size={20} />
                </a>
              </div>
              <div className="mt-3">
                <Link
                  to="/demo"
                  className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-teal-600 transition-colors font-medium"
                >
                  <Eye size={16} />
                  {isRomanian ? 'Vezi Demo →' : 'See Demo →'}
                </Link>
              </div>
              <div className="flex flex-wrap items-center gap-6 mt-8 text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <UtensilsCrossed size={16} className="text-amber-500" />
                  {isRomanian ? 'Rețete românești' : 'Romanian recipes'}
                </div>
                <div className="flex items-center gap-2">
                  <ShoppingCart size={16} className="text-teal-500" />
                  {isRomanian ? 'Listă cumpărături Carrefour' : 'Carrefour shopping list'}
                </div>
                <div className="flex items-center gap-2">
                  <Shield size={16} className="text-cyan-500" />
                  {isRomanian ? 'Fără card bancar' : 'No credit card'}
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-3xl p-8 shadow-2xl shadow-amber-500/10">
                <div className="bg-white rounded-2xl p-6 shadow-lg mb-4">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center">
                      <Calendar className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">
                        {isRomanian ? 'Ziua 1 — Luni' : 'Day 1 — Monday'}
                      </p>
                      <p className="text-xs text-slate-400">
                        {isRomanian ? 'Plan personalizat' : 'Personalized plan'}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2.5 bg-amber-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-base">🌅</span>
                        <div>
                          <p className="text-sm font-medium text-slate-700">{isRomanian ? 'Mic dejun' : 'Breakfast'}</p>
                          <p className="text-xs text-slate-500">{isRomanian ? 'Ouă cu brânză și roșii' : 'Eggs with cheese & tomatoes'}</p>
                        </div>
                      </div>
                      <span className="text-xs font-medium text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">350 kcal</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-green-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-base">☀️</span>
                        <div>
                          <p className="text-sm font-medium text-slate-700">{isRomanian ? 'Prânz' : 'Lunch'}</p>
                          <p className="text-xs text-slate-500">{isRomanian ? 'Ciorbă de legume + pui la grătar' : 'Vegetable soup + grilled chicken'}</p>
                        </div>
                      </div>
                      <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-0.5 rounded-full">550 kcal</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 bg-violet-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className="text-base">🌙</span>
                        <div>
                          <p className="text-sm font-medium text-slate-700">{isRomanian ? 'Cină' : 'Dinner'}</p>
                          <p className="text-xs text-slate-500">{isRomanian ? 'Somon cu legume la cuptor' : 'Baked salmon with vegetables'}</p>
                        </div>
                      </div>
                      <span className="text-xs font-medium text-violet-600 bg-violet-100 px-2 py-0.5 rounded-full">450 kcal</span>
                    </div>
                  </div>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-md">
                  <div className="flex items-center gap-2 mb-2">
                    <ShoppingCart className="w-4 h-4 text-teal-500" />
                    <p className="text-sm font-semibold text-slate-700">{isRomanian ? 'Listă cumpărături' : 'Shopping list'}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {['Somon', 'Brânză', 'Ouă', 'Roșii', 'Pui', 'Legume'].map(item => (
                      <span key={item} className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{item}</span>
                    ))}
                    <span className="text-xs text-teal-500 font-medium px-2 py-1">+12</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trusted Providers */}
      <section className="py-12 px-6 border-y border-slate-100 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-slate-500 mb-8">
            {isRomanian ? 'Se conectează cu furnizorii medicali din România' : 'Connects with medical providers in Romania'}
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60">
            <span className="text-2xl font-bold text-slate-600">Regina Maria</span>
            <span className="text-2xl font-bold text-slate-600">Synevo</span>
            <span className="text-2xl font-bold text-slate-600">MedLife</span>
            <span className="text-2xl font-bold text-slate-600">Sanador</span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
              {isRomanian ? 'Cum funcționează?' : 'How does it work?'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {isRomanian
                ? 'În 3 pași simpli, ai toate analizele și interpretarea AI'
                : 'In 3 simple steps, you have all your tests and AI interpretation'}
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                icon: Users,
                title: isRomanian ? 'Conectează conturile' : 'Connect accounts',
                description: isRomanian
                  ? 'Adaugă credențialele de la Regina Maria, Synevo sau alți provideri. Sunt criptate și securizate.'
                  : 'Add credentials from Regina Maria, Synevo or other providers. They are encrypted and secure.',
                color: 'from-cyan-500 to-cyan-600',
              },
              {
                step: '2',
                icon: Zap,
                title: isRomanian ? 'Sincronizare automată' : 'Auto sync',
                description: isRomanian
                  ? 'Aplicația descarcă automat toate analizele tale, extrage valorile și le organizează.'
                  : 'The app automatically downloads all your tests, extracts values and organizes them.',
                color: 'from-violet-500 to-violet-600',
              },
              {
                step: '3',
                icon: Brain,
                title: isRomanian ? 'Analiză AI' : 'AI Analysis',
                description: isRomanian
                  ? 'Specialiști AI (cardiolog, endocrinolog, etc.) îți analizează rezultatele și îți dau recomandări.'
                  : 'AI specialists (cardiologist, endocrinologist, etc.) analyze your results and give recommendations.',
                color: 'from-teal-500 to-teal-600',
              },
            ].map((item, index) => (
              <div key={index} className="relative">
                <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-sm hover:shadow-lg transition-shadow h-full">
                  <div className={`w-14 h-14 bg-gradient-to-br ${item.color} rounded-2xl flex items-center justify-center mb-6 shadow-lg`}>
                    <item.icon className="w-7 h-7 text-white" />
                  </div>
                  <div className="absolute -top-3 -left-3 w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-bold text-slate-800 mb-3">{item.title}</h3>
                  <p className="text-slate-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sample Plan Preview */}
      <section id="sample-plan" className="py-20 px-6 bg-gradient-to-b from-white to-amber-50/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-4">
            <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
              <FlaskConical size={16} />
              {isRomanian ? 'Exemplu real generat de AI' : 'Real AI-generated example'}
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-3">
              {isRomanian ? 'Ce primești exact?' : 'What exactly do you get?'}
            </h2>
            <p className="text-slate-500 max-w-2xl mx-auto">
              {isRomanian
                ? 'Exemplu generat pentru un utilizator cu colesterol crescut și vitamina D scăzută'
                : 'Example generated for a user with high cholesterol and low vitamin D'}
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mt-12">
            {/* Column 1 — 3-Day Meal Plan */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <UtensilsCrossed size={20} className="text-amber-500" />
                {isRomanian ? 'Plan alimentar 3 zile' : '3-Day Meal Plan'}
              </h3>
              {[
                {
                  day: isRomanian ? 'Ziua 1 — Luni' : 'Day 1 — Monday',
                  meals: [
                    { time: isRomanian ? 'Mic dejun' : 'Breakfast', dish: isRomanian ? 'Ovăz cu nuci, semințe de in și afine' : 'Oats with walnuts, flax seeds & blueberries', cal: 380 },
                    { time: isRomanian ? 'Prânz' : 'Lunch', dish: isRomanian ? 'Ciorbă de legume + piept de pui la grătar' : 'Vegetable soup + grilled chicken breast', cal: 520 },
                    { time: isRomanian ? 'Cină' : 'Dinner', dish: isRomanian ? 'Somon la cuptor cu broccoli și cartofi dulci' : 'Baked salmon with broccoli & sweet potatoes', cal: 480 },
                  ]
                },
                {
                  day: isRomanian ? 'Ziua 2 — Marți' : 'Day 2 — Tuesday',
                  meals: [
                    { time: isRomanian ? 'Mic dejun' : 'Breakfast', dish: isRomanian ? 'Omletă cu spanac și brânză de capră' : 'Spinach & goat cheese omelette', cal: 350 },
                    { time: isRomanian ? 'Prânz' : 'Lunch', dish: isRomanian ? 'Tocăniță de pui cu legume de sezon' : 'Chicken stew with seasonal vegetables', cal: 550 },
                    { time: isRomanian ? 'Cină' : 'Dinner', dish: isRomanian ? 'Salată cu ton, avocado și semințe' : 'Tuna salad with avocado & seeds', cal: 420 },
                  ]
                },
                {
                  day: isRomanian ? 'Ziua 3 — Miercuri' : 'Day 3 — Wednesday',
                  meals: [
                    { time: isRomanian ? 'Mic dejun' : 'Breakfast', dish: isRomanian ? 'Smoothie cu spanac, banană și unt de arahide' : 'Spinach, banana & peanut butter smoothie', cal: 340 },
                    { time: isRomanian ? 'Prânz' : 'Lunch', dish: isRomanian ? 'Sarmale în foi de viță cu mămăligă' : 'Vine leaf sarmale with polenta', cal: 580 },
                    { time: isRomanian ? 'Cină' : 'Dinner', dish: isRomanian ? 'Păstrăv la grătar cu salată verde' : 'Grilled trout with green salad', cal: 430 },
                  ]
                },
              ].map((day, i) => (
                <div key={i} className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                  <p className="text-sm font-bold text-slate-700 mb-2">{day.day}</p>
                  <div className="space-y-1.5">
                    {day.meals.map((meal, j) => (
                      <div key={j} className="flex items-center justify-between text-sm">
                        <div>
                          <span className="font-medium text-slate-600">{meal.time}: </span>
                          <span className="text-slate-500">{meal.dish}</span>
                        </div>
                        <span className="text-xs text-amber-600 font-medium whitespace-nowrap ml-2">{meal.cal} kcal</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {/* Blurred days 4-7 */}
              <div className="relative">
                <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm blur-[3px] select-none">
                  <p className="text-sm font-bold text-slate-700 mb-2">{isRomanian ? 'Ziua 4 — Joi' : 'Day 4 — Thursday'}</p>
                  <div className="space-y-1.5 text-sm text-slate-400">
                    <p>{isRomanian ? 'Mic dejun: Clătite cu brânză și miere...' : 'Breakfast: Cheese pancakes with honey...'}</p>
                    <p>{isRomanian ? 'Prânz: Ghiveci de legume cu orez...' : 'Lunch: Vegetable stew with rice...'}</p>
                    <p>{isRomanian ? 'Cină: File de curcan cu ciuperci...' : 'Dinner: Turkey fillet with mushrooms...'}</p>
                  </div>
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Link
                    to="/login"
                    className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full text-sm font-semibold shadow-lg hover:from-amber-600 hover:to-orange-600 transition-all flex items-center gap-1"
                  >
                    {isRomanian ? 'Vezi zilele 4-7' : 'See days 4-7'}
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </div>

            {/* Column 2 — Shopping List */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <ShoppingCart size={20} className="text-teal-500" />
                {isRomanian ? 'Listă cumpărături Carrefour' : 'Carrefour Shopping List'}
              </h3>
              {[
                {
                  category: isRomanian ? 'Lactate & Ouă' : 'Dairy & Eggs',
                  icon: '🥛',
                  items: isRomanian
                    ? ['Brânză de capră – 200g', 'Ouă – 10 buc', 'Iaurt grecesc – 500g']
                    : ['Goat cheese – 200g', 'Eggs – 10 pcs', 'Greek yogurt – 500g']
                },
                {
                  category: isRomanian ? 'Legume & Fructe' : 'Vegetables & Fruits',
                  icon: '🥬',
                  items: isRomanian
                    ? ['Spanac proaspăt – 300g', 'Broccoli – 500g', 'Cartofi dulci – 1kg', 'Roșii – 500g', 'Afine – 250g', 'Banane – 1kg']
                    : ['Fresh spinach – 300g', 'Broccoli – 500g', 'Sweet potatoes – 1kg', 'Tomatoes – 500g', 'Blueberries – 250g', 'Bananas – 1kg']
                },
                {
                  category: isRomanian ? 'Carne & Pește' : 'Meat & Fish',
                  icon: '🐟',
                  items: isRomanian
                    ? ['Piept de pui – 600g', 'Fileu de somon – 400g', 'Păstrăv – 2 buc', 'Ton conservă – 2 cutii']
                    : ['Chicken breast – 600g', 'Salmon fillet – 400g', 'Trout – 2 pcs', 'Canned tuna – 2 cans']
                },
                {
                  category: isRomanian ? 'Cereale & Semințe' : 'Grains & Seeds',
                  icon: '🌾',
                  items: isRomanian
                    ? ['Fulgi de ovăz – 500g', 'Semințe de in – 200g', 'Nuci – 300g', 'Orez brun – 500g']
                    : ['Oat flakes – 500g', 'Flax seeds – 200g', 'Walnuts – 300g', 'Brown rice – 500g']
                },
              ].map((cat, i) => (
                <div key={i} className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                  <p className="text-sm font-bold text-slate-700 mb-2 flex items-center gap-2">
                    <span>{cat.icon}</span> {cat.category}
                  </p>
                  <ul className="space-y-1">
                    {cat.items.map((item, j) => (
                      <li key={j} className="text-sm text-slate-500 flex items-center gap-2">
                        <CheckCircle size={12} className="text-teal-400 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Column 3 — Exercise Day */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Dumbbell size={20} className="text-violet-500" />
                {isRomanian ? 'Program exerciții — Ziua 1' : 'Exercise Program — Day 1'}
              </h3>
              <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                <p className="text-sm font-bold text-violet-600 mb-2 flex items-center gap-2">
                  <Activity size={14} />
                  {isRomanian ? 'Încălzire — 10 min' : 'Warm-up — 10 min'}
                </p>
                <ul className="space-y-1 text-sm text-slate-500">
                  <li>{isRomanian ? '• Mers pe loc – 3 min' : '• Walking in place – 3 min'}</li>
                  <li>{isRomanian ? '• Rotări de brațe – 2 min' : '• Arm circles – 2 min'}</li>
                  <li>{isRomanian ? '• Stretching dinamic – 5 min' : '• Dynamic stretching – 5 min'}</li>
                </ul>
              </div>
              <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                <p className="text-sm font-bold text-violet-600 mb-2 flex items-center gap-2">
                  <Dumbbell size={14} />
                  {isRomanian ? 'Antrenament principal — 30 min' : 'Main workout — 30 min'}
                </p>
                <ul className="space-y-1.5 text-sm text-slate-500">
                  <li className="flex justify-between"><span>{isRomanian ? 'Genuflexiuni' : 'Squats'}</span><span className="text-violet-500 font-medium">3×15</span></li>
                  <li className="flex justify-between"><span>{isRomanian ? 'Flotări' : 'Push-ups'}</span><span className="text-violet-500 font-medium">3×12</span></li>
                  <li className="flex justify-between"><span>{isRomanian ? 'Fandări' : 'Lunges'}</span><span className="text-violet-500 font-medium">3×12</span></li>
                  <li className="flex justify-between"><span>{isRomanian ? 'Plank' : 'Plank'}</span><span className="text-violet-500 font-medium">3×45s</span></li>
                  <li className="flex justify-between"><span>{isRomanian ? 'Ridicări de bazin' : 'Glute bridges'}</span><span className="text-violet-500 font-medium">3×15</span></li>
                </ul>
              </div>
              <div className="bg-white rounded-xl p-4 border border-slate-100 shadow-sm">
                <p className="text-sm font-bold text-violet-600 mb-2 flex items-center gap-2">
                  <Leaf size={14} />
                  {isRomanian ? 'Revenire — 10 min' : 'Cool-down — 10 min'}
                </p>
                <ul className="space-y-1 text-sm text-slate-500">
                  <li>{isRomanian ? '• Stretching static – 7 min' : '• Static stretching – 7 min'}</li>
                  <li>{isRomanian ? '• Respirație profundă – 3 min' : '• Deep breathing – 3 min'}</li>
                </ul>
              </div>
              <div className="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-4 border border-violet-100 text-center">
                <p className="text-xs text-violet-500 mb-1">{isRomanian ? 'Adaptat pentru colesterol crescut' : 'Adapted for high cholesterol'}</p>
                <p className="text-sm font-semibold text-violet-700">{isRomanian ? 'Focus pe exerciții cardio + rezistență' : 'Focus on cardio + resistance exercises'}</p>
              </div>
            </div>
          </div>

          {/* CTA below sample */}
          <div className="text-center mt-12">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold text-lg hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/30"
            >
              {isRomanian ? 'Obține planul TĂU personalizat' : 'Get YOUR personalized plan'}
              <ArrowRight size={20} />
            </Link>
            <p className="text-sm text-slate-400 mt-3">
              {isRomanian ? '30 zile gratuit • Nu necesită card bancar' : '30 days free • No credit card required'}
            </p>
          </div>
        </div>
      </section>

      {/* Stats / Social Proof */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8">
            {[
              {
                value: publicStats ? <AnimatedCounter end={publicStats.biomarkers_analyzed} /> : '100+',
                label: isRomanian ? 'Biomarkeri Analizați' : 'Biomarkers Analyzed',
                sub: isRomanian ? 'Extrași automat din PDF-uri' : 'Auto-extracted from PDFs',
              },
              {
                value: publicStats ? <AnimatedCounter end={publicStats.documents_processed} /> : '50+',
                label: isRomanian ? 'Documente Procesate' : 'Documents Processed',
                sub: isRomanian ? 'De la furnizorii medicali din România' : 'From Romanian medical providers',
              },
              {
                value: '8+',
                label: isRomanian ? 'Specialiști AI' : 'AI Specialists',
                sub: isRomanian ? 'Cardiolog, Endocrinolog, Nutriționist...' : 'Cardiologist, Endocrinologist, Nutritionist...',
              },
              {
                value: '256-bit',
                label: isRomanian ? 'Criptare' : 'Encryption',
                sub: isRomanian ? 'AES-256-GCM per utilizator' : 'AES-256-GCM per user',
              },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500 mb-2">
                  {stat.value}
                </div>
                <div className="font-semibold text-slate-800 mb-1">{stat.label}</div>
                <div className="text-sm text-slate-500">{stat.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
              {isRomanian ? 'Tot ce ai nevoie pentru sănătatea ta' : 'Everything you need for your health'}
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              {isRomanian
                ? 'Funcționalități puternice pentru a-ți înțelege și monitoriza sănătatea'
                : 'Powerful features to understand and monitor your health'}
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Brain,
                title: isRomanian ? 'Echipă de specialiști AI' : 'AI specialist team',
                description: isRomanian
                  ? 'Nu doar un raport generic. Cardiolog, Endocrinolog, Hematolog, Hepatolog, Nefrolog și alți specialiști — fiecare analizează ce contează în domeniul lui'
                  : 'Not just a generic report. Cardiologist, Endocrinologist, Hematologist, Hepatologist, Nephrologist and more — each analyzes what matters in their field',
                color: 'text-violet-600',
                bg: 'bg-violet-50',
              },
              {
                icon: UtensilsCrossed,
                title: isRomanian ? 'Nutriție personalizată' : 'Personalized nutrition',
                description: isRomanian
                  ? 'Plan alimentar de 7 zile bazat pe analizele TALE, nu sfaturi generice. Cu rețete românești: ciorbă, sarmale, tocăniță — nu „eat more kale"'
                  : 'A 7-day meal plan based on YOUR lab results, not generic advice. With Romanian recipes: ciorbă, sarmale — not "eat more kale"',
                color: 'text-orange-600',
                bg: 'bg-orange-50',
              },
              {
                icon: Dumbbell,
                title: isRomanian ? 'Program de exerciții' : 'Exercise program',
                description: isRomanian
                  ? 'Plan de 7 zile cu exerciții adaptate profilului tău medical. Cu încălzire, antrenament, relaxare și progresie pe 8 săptămâni'
                  : '7-day workout plan adapted to your medical profile. With warm-up, workout, cool-down and 8-week progression',
                color: 'text-blue-600',
                bg: 'bg-blue-50',
              },
              {
                icon: ShoppingCart,
                title: isRomanian ? 'Listă de cumpărături' : 'Grocery list',
                description: isRomanian
                  ? 'Primești lista de cumpărături completă, organizată pe categorii, gata de dus la Mega Image sau piață'
                  : 'Get the complete shopping list, organized by category, ready for the store or market',
                color: 'text-green-600',
                bg: 'bg-green-50',
              },
              {
                icon: TrendingUp,
                title: isRomanian ? 'Evoluție în timp' : 'Biomarker trends',
                description: isRomanian
                  ? 'Grafice interactive cu evoluția fiecărui biomarker. Vezi cum se schimbă colesterolul, hemoglobina sau glicemia ta'
                  : 'Interactive charts tracking each biomarker over time. See how your cholesterol, hemoglobin or glucose changes',
                color: 'text-cyan-600',
                bg: 'bg-cyan-50',
              },
              {
                icon: Stethoscope,
                title: isRomanian ? 'Analiza lacunelor' : 'Gap analysis',
                description: isRomanian
                  ? 'Află ce analize îți lipsesc bazat pe vârstă, sex și istoricul tău medical'
                  : 'Find out what tests you\'re missing based on age, gender and medical history',
                color: 'text-teal-600',
                bg: 'bg-teal-50',
              },
              {
                icon: Shield,
                title: isRomanian ? 'Criptare per utilizator' : 'Per-user encryption',
                description: isRomanian
                  ? 'AES-256-GCM per cont. Nici echipa noastră nu poate vedea datele tale medicale. GDPR complet'
                  : 'AES-256-GCM per account. Not even our team can see your medical data. Fully GDPR compliant',
                color: 'text-emerald-600',
                bg: 'bg-emerald-50',
              },
              {
                icon: Clock,
                title: isRomanian ? 'Toate laboratoarele, un loc' : 'All labs, one place',
                description: isRomanian
                  ? 'Regina Maria, Synevo, MedLife, Sanador — conectezi conturile și analizele se descarcă automat'
                  : 'Regina Maria, Synevo, MedLife, Sanador — connect your accounts and lab results download automatically',
                color: 'text-amber-600',
                bg: 'bg-amber-50',
              },
            ].map((feature, index) => (
              <div key={index} className="bg-white rounded-2xl p-6 border border-slate-100 hover:shadow-lg transition-shadow">
                <div className={`w-12 h-12 ${feature.bg} rounded-xl flex items-center justify-center mb-4`}>
                  <feature.icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{feature.title}</h3>
                <p className="text-slate-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-8 md:p-12 text-white">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full text-sm mb-6">
                  <Lock size={16} aria-hidden="true" />
                  {isRomanian ? 'Securitate de nivel bancar' : 'Bank-level security'}
                </div>
                <h2 className="text-3xl md:text-4xl font-bold mb-6">
                  {isRomanian
                    ? 'Datele tale medicale sunt în siguranță'
                    : 'Your medical data is safe'}
                </h2>
                <p className="text-slate-300 text-lg mb-8">
                  {isRomanian
                    ? 'Folosim criptare end-to-end AES-256-GCM. Nici măcar echipa noastră nu poate vedea datele tale. Tu deții controlul total.'
                    : 'We use end-to-end AES-256-GCM encryption. Not even our team can see your data. You have full control.'}
                </p>
                <div className="space-y-4">
                  {[
                    isRomanian ? 'Criptare AES-256-GCM' : 'AES-256-GCM encryption',
                    isRomanian ? 'Cheie de recuperare personală' : 'Personal recovery key',
                    isRomanian ? 'Conform GDPR' : 'GDPR compliant',
                    isRomanian ? 'Servere în UE' : 'EU servers',
                  ].map((item, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div className="w-6 h-6 bg-teal-500 rounded-full flex items-center justify-center">
                        <CheckCircle size={14} className="text-white" />
                      </div>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 rounded-3xl blur-3xl"></div>
                <div className="relative bg-white/5 backdrop-blur rounded-2xl p-8 border border-white/10">
                  <div className="flex items-center justify-center mb-6">
                    <div className="w-24 h-24 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-full flex items-center justify-center">
                      <Shield className="w-12 h-12 text-white" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold mb-2">256-bit</p>
                    <p className="text-slate-300">
                      {isRomanian ? 'Criptare militară' : 'Military-grade encryption'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section className="py-20 px-6 bg-gradient-to-b from-white to-cyan-50">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
            {isRomanian ? 'Prețuri simple și accesibile' : 'Simple and affordable pricing'}
          </h2>
          <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto">
            {isRomanian
              ? 'Primești 30 de zile de Premium gratuit la înregistrare. Fără card bancar.'
              : 'Get 30 days of free Premium when you sign up. No credit card required.'}
          </p>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <h3 className="text-xl font-bold text-slate-800 mb-2">Free</h3>
              <div className="text-4xl font-bold text-slate-800 mb-6">0 <span className="text-lg font-normal text-slate-500">RON</span></div>
              <ul className="space-y-3 text-left mb-8">
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-slate-500" />
                  <span>20 {isRomanian ? 'documente' : 'documents'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-slate-500" />
                  <span>2 {isRomanian ? 'analize AI/lună' : 'AI analyses/month'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-slate-500" />
                  <span>1 {isRomanian ? 'cont medical' : 'medical account'}</span>
                </li>
              </ul>
              <Link
                to="/login"
                className="block w-full py-3 border-2 border-slate-200 text-slate-700 rounded-xl font-semibold hover:bg-slate-50 transition-colors"
              >
                {isRomanian ? 'Începe Gratuit' : 'Start Free'}
              </Link>
            </div>
            {/* Premium */}
            <div className="bg-gradient-to-b from-amber-50 to-white rounded-2xl p-8 border-2 border-amber-400 shadow-lg relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                {isRomanian ? '30 zile gratuit' : '30 days free'}
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">Premium</h3>
              <div className="text-4xl font-bold text-slate-800 mb-6">29 <span className="text-lg font-normal text-slate-500">RON/{isRomanian ? 'lună' : 'mo'}</span></div>
              <ul className="space-y-3 text-left mb-8">
                <li className="flex items-center gap-2 text-slate-700">
                  <CheckCircle size={16} className="text-amber-500" />
                  <span>500 {isRomanian ? 'documente' : 'documents'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-700">
                  <CheckCircle size={16} className="text-amber-500" />
                  <span>30 {isRomanian ? 'analize AI/lună' : 'AI analyses/month'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-700">
                  <CheckCircle size={16} className="text-amber-500" />
                  <span>8+ {isRomanian ? 'specialiști AI' : 'AI specialists'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-700">
                  <CheckCircle size={16} className="text-amber-500" />
                  <span>{isRomanian ? 'Export PDF' : 'PDF export'}</span>
                </li>
              </ul>
              <Link
                to="/login"
                className="block w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-colors"
              >
                {isRomanian ? 'Încearcă 30 Zile Gratuit' : 'Try 30 Days Free'}
              </Link>
            </div>
            {/* Family */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <h3 className="text-xl font-bold text-slate-800 mb-2">Family</h3>
              <div className="text-4xl font-bold text-slate-800 mb-6">49 <span className="text-lg font-normal text-slate-500">RON/{isRomanian ? 'lună' : 'mo'}</span></div>
              <ul className="space-y-3 text-left mb-8">
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-purple-500" />
                  <span>{isRomanian ? 'Până la 5 membri' : 'Up to 5 members'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-purple-500" />
                  <span>{isRomanian ? 'Toate funcțiile Premium' : 'All Premium features'}</span>
                </li>
                <li className="flex items-center gap-2 text-slate-600">
                  <CheckCircle size={16} className="text-purple-500" />
                  <span>{isRomanian ? 'Conturi separate' : 'Separate accounts'}</span>
                </li>
              </ul>
              <Link
                to="/login"
                className="block w-full py-3 border-2 border-purple-500 text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition-colors"
              >
                {isRomanian ? 'Începe cu Family' : 'Start with Family'}
              </Link>
            </div>
          </div>
          <p className="mt-8 text-slate-500">
            <Link to="/pricing" className="text-cyan-600 hover:underline font-medium">
              {isRomanian ? 'Vezi comparația completă →' : 'See full comparison →'}
            </Link>
          </p>
        </div>
      </section>

      {/* Built for real health scenarios */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
              {isRomanian ? 'Construit pentru scenarii reale de sănătate' : 'Built for real health scenarios'}
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: isRomanian ? 'Monitorizare completă' : 'Complete Monitoring',
                description: isRomanian
                  ? 'Ai analize de la Regina Maria și Synevo din ultimii 5 ani? Le vezi pe toate într-un singur loc, cu grafice de evoluție pentru fiecare biomarker.'
                  : 'Have tests from Regina Maria and Synevo over the last 5 years? See them all in one place, with evolution charts for each biomarker.',
                subtitle: isRomanian ? 'Toate analizele, un singur loc' : 'All tests, one place',
                icon: Activity,
              },
              {
                title: isRomanian ? 'Prevenție inteligentă' : 'Smart Prevention',
                description: isRomanian
                  ? 'Specialiștii AI detectează trenduri îngrijorătoare pe care le-ai rata altfel — de exemplu un colesterol care crește treptat de la o analiză la alta.'
                  : 'AI specialists detect concerning trends you might miss — for example cholesterol gradually increasing from one test to the next.',
                subtitle: isRomanian ? 'Detectarea timpurie a problemelor' : 'Early problem detection',
                icon: Brain,
              },
              {
                title: isRomanian ? 'Confidențialitate totală' : 'Total Privacy',
                description: isRomanian
                  ? 'Datele sunt criptate cu cheia ta personală (AES-256-GCM). Nici măcar administratorul platformei nu le poate vedea sau accesa.'
                  : 'Data is encrypted with your personal key (AES-256-GCM). Not even the platform administrator can see or access it.',
                subtitle: isRomanian ? 'Zero acces pentru terți' : 'Zero third-party access',
                icon: Shield,
              },
            ].map((card, index) => (
              <div key={index} className="bg-slate-50 rounded-2xl p-8 border border-slate-100">
                <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mb-6">
                  <card.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{card.title}</h3>
                <p className="text-slate-600 mb-4 leading-relaxed">{card.description}</p>
                <p className="text-sm text-slate-500 font-medium">{card.subtitle}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Blog + Biomarker Section for SEO internal linking */}
      <section className="py-20 px-6 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto">
          {/* Latest Blog Articles */}
          {blogArticles.length > 0 && (
            <div className="mb-16">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="text-3xl font-bold text-slate-800">
                    {isRomanian ? 'Din blogul nostru' : 'From our blog'}
                  </h2>
                  <p className="text-slate-500 mt-1">
                    {isRomanian ? 'Sfaturi de sănătate, nutriție și interpretare analize' : 'Health tips, nutrition and lab result interpretation'}
                  </p>
                </div>
                <Link to="/blog" className="hidden sm:flex items-center gap-1 text-teal-600 font-semibold hover:gap-2 transition-all">
                  {isRomanian ? 'Toate articolele' : 'All articles'} <ArrowRight size={16} />
                </Link>
              </div>
              <div className="grid md:grid-cols-3 gap-6">
                {blogArticles.map(a => (
                  <Link
                    key={a.slug}
                    to={`/blog/${a.slug}`}
                    className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-slate-300 transition-all group"
                  >
                    <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                      <Calendar size={12} />
                      {a.published_at ? new Date(a.published_at).toLocaleDateString(isRomanian ? 'ro-RO' : 'en-US', { month: 'short', day: 'numeric' }) : ''}
                    </div>
                    <h3 className="font-bold text-slate-800 group-hover:text-teal-700 transition-colors mb-2 line-clamp-2">
                      {isRomanian ? a.title : (a.title_en || a.title)}
                    </h3>
                    <p className="text-sm text-slate-500 line-clamp-2">
                      {isRomanian ? a.excerpt : (a.excerpt_en || a.excerpt)}
                    </p>
                  </Link>
                ))}
              </div>
              <div className="text-center mt-6 sm:hidden">
                <Link to="/blog" className="text-teal-600 font-semibold">
                  {isRomanian ? 'Toate articolele →' : 'All articles →'}
                </Link>
              </div>
            </div>
          )}

          {/* Popular Biomarkers */}
          <div>
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-bold text-slate-800">
                  {isRomanian ? 'Ghid biomarkeri' : 'Biomarker guide'}
                </h2>
                <p className="text-slate-500 mt-1">
                  {isRomanian ? 'Cele mai căutate analize — valori normale și interpretare' : 'Most searched tests — normal values and interpretation'}
                </p>
              </div>
              <Link to="/biomarker" className="hidden sm:flex items-center gap-1 text-teal-600 font-semibold hover:gap-2 transition-all">
                {isRomanian ? 'Toți biomarkerii' : 'All biomarkers'} <ArrowRight size={16} />
              </Link>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 sm:gap-3">
              {[
                { slug: 'hemoglobina', name: 'Hemoglobina', aliases: 'Hb, HGB' },
                { slug: 'glicemie', name: 'Glicemia', aliases: 'Glucoză' },
                { slug: 'colesterol-total', name: 'Colesterol Total', aliases: '' },
                { slug: 'colesterol-ldl', name: 'Colesterol LDL', aliases: '"cel rău"' },
                { slug: 'tgo', name: 'TGO (AST)', aliases: 'Transaminaze' },
                { slug: 'tgp', name: 'TGP (ALT)', aliases: 'Transaminaze' },
                { slug: 'tsh', name: 'TSH', aliases: 'Tiroidă' },
                { slug: 'vitamina-d', name: 'Vitamina D', aliases: '25-OH' },
                { slug: 'fier-seric', name: 'Fier seric', aliases: '' },
                { slug: 'hemoglobina-glicata', name: 'HbA1c', aliases: 'Diabet' },
                { slug: 'vitamina-b12', name: 'Vitamina B12', aliases: '' },
                { slug: 'creatinina', name: 'Creatinina', aliases: 'Rinichi' },
              ].map(b => (
                <Link
                  key={b.slug}
                  to={`/biomarker/${b.slug}`}
                  className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4 hover:shadow-md hover:border-teal-200 transition-all group text-center"
                >
                  <p className="font-bold text-slate-800 group-hover:text-teal-700 transition-colors text-xs sm:text-sm">{b.name}</p>
                  {b.aliases && <p className="text-[10px] sm:text-xs text-slate-400 mt-0.5">{b.aliases}</p>}
                </Link>
              ))}
            </div>
            <div className="text-center mt-6 sm:hidden">
              <Link to="/biomarker" className="text-teal-600 font-semibold">
                {isRomanian ? 'Toți biomarkerii →' : 'All biomarkers →'}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-6">
            {isRomanian
              ? 'Începe să-ți monitorizezi sănătatea astăzi'
              : 'Start monitoring your health today'}
          </h2>
          <p className="text-xl text-slate-600 mb-8">
            {isRomanian
              ? 'Primești 30 de zile de Premium gratuit. Fără card bancar.'
              : 'Get 30 days of free Premium. No credit card required.'}
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold text-lg hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/30"
          >
            {isRomanian ? 'Încearcă 30 Zile Gratuit' : 'Try 30 Days Free'}
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-slate-200 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
                <HeartPulse className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-slate-800">Analize.Online</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-600 flex-wrap justify-center">
              <Link to="/biomarker" className="hover:text-cyan-600">
                {isRomanian ? 'Ghid Biomarkeri' : 'Biomarker Guide'}
              </Link>
              <Link to="/blog" className="hover:text-cyan-600">
                Blog
              </Link>
              <Link to="/pricing" className="hover:text-cyan-600">
                {isRomanian ? 'Prețuri' : 'Pricing'}
              </Link>
              <Link to="/despre-noi" className="hover:text-cyan-600">
                {isRomanian ? 'Despre noi' : 'About'}
              </Link>
              <Link to="/contact" className="hover:text-cyan-600">
                Contact
              </Link>
              <Link to="/terms" className="hover:text-cyan-600">
                {isRomanian ? 'Termeni' : 'Terms'}
              </Link>
              <Link to="/privacy" className="hover:text-cyan-600">
                {isRomanian ? 'Confidențialitate' : 'Privacy'}
              </Link>
              <Link to="/disclaimer-medical" className="hover:text-cyan-600">
                {isRomanian ? 'Disclaimer medical' : 'Medical Disclaimer'}
              </Link>
            </div>
            <p className="text-sm text-slate-500">
              © 2026 Analize.Online. {isRomanian ? 'Toate drepturile rezervate.' : 'All rights reserved.'}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
