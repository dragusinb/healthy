import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HeartPulse, Shield, Brain, Zap, FileText, TrendingUp,
  CheckCircle, ArrowRight, Lock, Users, Clock, Smartphone,
  Globe, Star, ChevronRight, Activity, Stethoscope,
  UtensilsCrossed, Dumbbell, ShoppingCart, ChefHat, Leaf, Apple, BookOpen, FlaskConical, Calendar
} from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import api from '../api/client';

export default function Home() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const isRomanian = i18n.language === 'ro';
  const [blogArticles, setBlogArticles] = useState([]);

  usePageTitle(null, isRomanian
    ? 'Toate analizele tale medicale, într-un singur loc'
    : 'All your medical tests, in one place');

  useEffect(() => {
    api.get('/blog/articles?limit=3').then(res => setBlogArticles(res.data.articles || [])).catch(() => {});
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
              className="text-slate-600 hover:text-slate-800 font-medium hidden sm:block"
            >
              {isRomanian ? 'Prețuri' : 'Pricing'}
            </Link>
            <Link
              to="/login"
              className="text-slate-600 hover:text-slate-800 font-medium hidden sm:block"
            >
              {isRomanian ? 'Autentificare' : 'Login'}
            </Link>
            <Link
              to="/login?mode=register"
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg font-medium hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md shadow-cyan-500/20"
            >
              {isRomanian ? 'Înregistrare' : 'Sign Up'}
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="hero" className="pt-32 pb-20 px-6 bg-gradient-to-b from-cyan-50 via-white to-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-cyan-100 text-cyan-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Shield size={16} />
                {isRomanian ? 'Date criptate end-to-end' : 'End-to-end encrypted'}
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-800 leading-tight mb-6">
                {isRomanian ? (
                  <>Toate analizele tale medicale, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500">într-un singur loc</span></>
                ) : (
                  <>All your medical tests, <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500">in one place</span></>
                )}
              </h1>
              <p className="text-xl text-slate-600 mb-8 leading-relaxed">
                {isRomanian
                  ? 'Conectează conturile de la Regina Maria, Synevo, MedLife și Sanador. Primești interpretare de la o echipă de specialiști AI, plan nutrițional cu rețete românești și program de exerciții — totul bazat pe analizele tale reale.'
                  : 'Connect your Regina Maria, Synevo, MedLife and Sanador accounts. Get analysis from a team of AI specialists, a nutrition plan with Romanian recipes and an exercise program — all based on your real lab results.'}
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/login"
                  className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold text-lg hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/30 flex items-center justify-center gap-2"
                >
                  {isRomanian ? 'Creează Cont Gratuit' : 'Create Free Account'}
                  <ArrowRight size={20} />
                </Link>
                <Link
                  to="/pricing"
                  className="px-8 py-4 bg-white border-2 border-slate-200 text-slate-700 rounded-xl font-semibold text-lg hover:border-slate-300 hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
                >
                  {isRomanian ? 'Vezi Prețurile' : 'See Pricing'}
                </Link>
              </div>
              <div className="flex items-center gap-6 mt-8 text-sm text-slate-500">
                <div className="flex items-center gap-2">
                  <CheckCircle size={16} className="text-teal-500" />
                  {isRomanian ? 'Gratuit pentru început' : 'Free to start'}
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle size={16} className="text-teal-500" />
                  {isRomanian ? 'Fără card bancar' : 'No credit card'}
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-cyan-100 to-teal-100 rounded-3xl p-8 shadow-2xl shadow-cyan-500/10">
                <div className="bg-white rounded-2xl p-6 shadow-lg mb-4">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-500 rounded-xl flex items-center justify-center">
                      <Brain className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">
                        {isRomanian ? 'Analiză AI Completă' : 'Complete AI Analysis'}
                      </p>
                      <p className="text-sm text-slate-500">
                        {isRomanian ? 'Bazată pe 47 biomarkeri' : 'Based on 47 biomarkers'}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg">
                      <span className="text-sm text-slate-600">Colesterol total</span>
                      <span className="text-sm font-medium text-green-600">Normal ✓</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-amber-50 rounded-lg">
                      <span className="text-sm text-slate-600">Vitamina D</span>
                      <span className="text-sm font-medium text-amber-600">Atenție !</span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg">
                      <span className="text-sm text-slate-600">Hemoglobina</span>
                      <span className="text-sm font-medium text-green-600">Normal ✓</span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-xl p-4 shadow-md">
                    <Stethoscope className="w-8 h-8 text-teal-500 mb-2" />
                    <p className="text-2xl font-bold text-slate-800">8+</p>
                    <p className="text-xs text-slate-500">
                      {isRomanian ? 'Specialiști AI' : 'AI Specialists'}
                    </p>
                  </div>
                  <div className="bg-white rounded-xl p-4 shadow-md">
                    <TrendingUp className="w-8 h-8 text-violet-500 mb-2" />
                    <p className="text-2xl font-bold text-slate-800">100%</p>
                    <p className="text-xs text-slate-500">
                      {isRomanian ? 'Istoric complet' : 'Full history'}
                    </p>
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

      {/* Stats / Social Proof */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              {
                value: '4',
                label: isRomanian ? 'Provideri Integrați' : 'Integrated Providers',
                sub: 'Regina Maria, Synevo, MedLife, Sanador',
              },
              {
                value: '8+',
                label: isRomanian ? 'Specialiști AI' : 'AI Specialists',
                sub: isRomanian ? 'Cardiolog, Endocrinolog, Nutriționist...' : 'Cardiologist, Endocrinologist, Nutritionist...',
              },
              {
                value: '150+',
                label: isRomanian ? 'Tipuri de Biomarkeri' : 'Biomarker Types',
                sub: isRomanian ? 'Extrași automat din PDF-uri' : 'Auto-extracted from PDFs',
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
              ? 'Începe gratuit. Upgrade când ai nevoie de mai mult.'
              : 'Start free. Upgrade when you need more.'}
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
                {isRomanian ? 'Popular' : 'Popular'}
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
                {isRomanian ? 'Începe cu Premium' : 'Start with Premium'}
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

      {/* Testimonials / Use Cases */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">
              {isRomanian ? 'De ce utilizatorii aleg Analize.Online' : 'Why users choose Analize.Online'}
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                quote: isRomanian
                  ? 'Am analize de la Regina Maria și Synevo din ultimii 5 ani. Acum le văd pe toate într-un singur loc, cu grafice de evoluție.'
                  : 'I have tests from Regina Maria and Synevo over the last 5 years. Now I see them all in one place, with evolution charts.',
                name: isRomanian ? 'Monitorizare completă' : 'Complete Monitoring',
                role: isRomanian ? 'Toate analizele, un singur loc' : 'All tests, one place',
                icon: Activity,
              },
              {
                quote: isRomanian
                  ? 'Specialistul AI cardiolog mi-a semnalat un trend îngrijorător la colesterol pe care nu l-aș fi observat singur.'
                  : 'The AI cardiologist specialist flagged a concerning cholesterol trend I wouldn\'t have noticed on my own.',
                name: isRomanian ? 'Prevenție inteligentă' : 'Smart Prevention',
                role: isRomanian ? 'Detectarea timpurie a problemelor' : 'Early problem detection',
                icon: Brain,
              },
              {
                quote: isRomanian
                  ? 'Datele mele sunt criptate cu cheia mea personală. Nici măcar administratorul platformei nu le poate vedea.'
                  : 'My data is encrypted with my personal key. Not even the platform administrator can see it.',
                name: isRomanian ? 'Confidențialitate totală' : 'Total Privacy',
                role: isRomanian ? 'Zero acces pentru terți' : 'Zero third-party access',
                icon: Shield,
              },
            ].map((testimonial, index) => (
              <div key={index} className="bg-slate-50 rounded-2xl p-8 border border-slate-100">
                <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl flex items-center justify-center mb-6">
                  <testimonial.icon className="w-6 h-6 text-white" />
                </div>
                <p className="text-slate-600 mb-6 leading-relaxed italic">"{testimonial.quote}"</p>
                <div>
                  <p className="font-semibold text-slate-800">{testimonial.name}</p>
                  <p className="text-sm text-slate-500">{testimonial.role}</p>
                </div>
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
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
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
                  className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md hover:border-teal-200 transition-all group text-center"
                >
                  <p className="font-bold text-slate-800 group-hover:text-teal-700 transition-colors text-sm">{b.name}</p>
                  {b.aliases && <p className="text-xs text-slate-400 mt-0.5">{b.aliases}</p>}
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
              ? 'Creează un cont gratuit în 30 de secunde. Fără card bancar.'
              : 'Create a free account in 30 seconds. No credit card required.'}
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold text-lg hover:from-cyan-600 hover:to-teal-600 transition-all shadow-lg shadow-cyan-500/30"
          >
            {isRomanian ? 'Creează Cont Gratuit' : 'Create Free Account'}
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
              <Link to="/terms" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600">
                {isRomanian ? 'Termeni' : 'Terms'}
              </Link>
              <Link to="/privacy" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600">
                {isRomanian ? 'Confidențialitate' : 'Privacy'}
              </Link>
              <a href="mailto:contact@analize.online" className="hover:text-cyan-600">
                Contact
              </a>
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
