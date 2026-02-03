import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Check, X, Crown, Users, Sparkles, HeartPulse, ArrowRight, FileText,
  Brain, Share2, History, Zap, Shield, Stethoscope, TrendingUp, Download,
  Clock, Heart, Activity, ChevronDown, ChevronUp
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Pricing() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';
  const navigate = useNavigate();
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/subscription/plans');
      setPlans(response.data.plans);
    } catch (err) {
      console.error('Failed to fetch plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = (planId) => {
    if (!user) {
      navigate('/login');
      return;
    }
    if (planId === 'free') return;
    navigate(`/billing?plan=${planId}`);
  };

  const premiumMonthly = plans.find(p => p.id === 'premium_monthly');
  const premiumYearly = plans.find(p => p.id === 'premium_yearly');
  const familyPlan = plans.find(p => p.id === 'family_monthly');

  const activePremium = selectedPeriod === 'yearly' ? premiumYearly : premiumMonthly;

  // Premium benefits with detailed descriptions
  const premiumBenefits = [
    {
      icon: Brain,
      title: isRomanian ? '5 Specialisti AI' : '5 AI Specialists',
      description: isRomanian
        ? 'Cardiolog, Endocrinolog, Hematolog, Hepatolog si Nefrolog - analize detaliate pentru fiecare sistem'
        : 'Cardiologist, Endocrinologist, Hematologist, Hepatologist and Nephrologist - detailed analysis for each system',
      color: 'text-violet-600',
      bg: 'bg-violet-50',
    },
    {
      icon: TrendingUp,
      title: isRomanian ? '30 Analize AI / luna' : '30 AI Analyses / month',
      description: isRomanian
        ? 'Ruleaza analize AI de cate ori ai nevoie - vezi cum evolueaza sanatatea ta in timp'
        : 'Run AI analyses as often as you need - see how your health evolves over time',
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      icon: Stethoscope,
      title: isRomanian ? 'Analiza lacunelor in screening' : 'Screening Gap Analysis',
      description: isRomanian
        ? 'Afla ce analize medicale ar trebui sa faci bazat pe varsta, sex si istoricul tau medical'
        : 'Find out what medical tests you should do based on your age, gender and medical history',
      color: 'text-teal-600',
      bg: 'bg-teal-50',
    },
    {
      icon: History,
      title: isRomanian ? 'Comparatii istorice' : 'Historical Comparisons',
      description: isRomanian
        ? 'Compara analizele de acum cu cele de acum 6 luni sau 1 an - vezi tendintele'
        : 'Compare current tests with those from 6 months or 1 year ago - see trends',
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      icon: Download,
      title: isRomanian ? 'Export PDF' : 'PDF Export',
      description: isRomanian
        ? 'Descarca rapoartele AI in format PDF pentru a le arata medicului tau'
        : 'Download AI reports in PDF format to show your doctor',
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
    {
      icon: Shield,
      title: isRomanian ? 'Conturi medicale nelimitate' : 'Unlimited Medical Accounts',
      description: isRomanian
        ? 'Conecteaza Regina Maria, Synevo, Medlife si orice alt provider - toate intr-un singur loc'
        : 'Connect Regina Maria, Synevo, Medlife and any other provider - all in one place',
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      icon: Zap,
      title: isRomanian ? 'Sincronizare prioritara' : 'Priority Sync',
      description: isRomanian
        ? 'Analizele tale sunt sincronizate cu prioritate - primesti rezultatele mai repede'
        : 'Your tests are synced with priority - you get results faster',
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
    {
      icon: FileText,
      title: isRomanian ? '500 Documente' : '500 Documents',
      description: isRomanian
        ? 'Stocheaza pana la 500 de documente medicale - 10x mai mult decat planul gratuit'
        : 'Store up to 500 medical documents - 10x more than the free plan',
      color: 'text-slate-600',
      bg: 'bg-slate-50',
    },
  ];

  // Family additional benefits
  const familyBenefits = [
    {
      icon: Users,
      title: isRomanian ? 'Pana la 5 membri' : 'Up to 5 members',
      description: isRomanian
        ? 'Adauga sotul/sotia, copiii sau parintii - fiecare cu cont propriu'
        : 'Add spouse, children or parents - each with their own account',
    },
    {
      icon: Shield,
      title: isRomanian ? 'Date complet separate' : 'Completely separate data',
      description: isRomanian
        ? 'Fiecare membru are propriile analize, rapoarte si istoric - 100% privat'
        : 'Each member has their own tests, reports and history - 100% private',
    },
    {
      icon: Heart,
      title: isRomanian ? 'Economisesti 15 RON/luna' : 'Save 15 RON/month',
      description: isRomanian
        ? 'La 5 membri, fiecare plateste doar 2 RON/luna in loc de 5 RON'
        : 'With 5 members, each pays only 2 RON/month instead of 5 RON',
    },
  ];

  // Feature comparison data
  const features = [
    {
      category: isRomanian ? 'Stocare & Sincronizare' : 'Storage & Sync',
      items: [
        {
          name: isRomanian ? 'Documente medicale' : 'Medical documents',
          free: '50',
          premium: '500',
          family: isRomanian ? '500 / membru' : '500 / member',
          icon: FileText,
        },
        {
          name: isRomanian ? 'Conturi medicale conectate' : 'Connected medical accounts',
          free: '2',
          premium: isRomanian ? 'Nelimitat' : 'Unlimited',
          family: isRomanian ? 'Nelimitat' : 'Unlimited',
          icon: Shield,
        },
        {
          name: isRomanian ? 'Sincronizare prioritara' : 'Priority sync',
          free: false,
          premium: true,
          family: true,
          icon: Zap,
        },
      ],
    },
    {
      category: isRomanian ? 'Analize AI' : 'AI Analysis',
      items: [
        {
          name: isRomanian ? 'Analize AI pe luna' : 'AI analyses per month',
          free: '3',
          premium: '30',
          family: isRomanian ? '30 / membru' : '30 / member',
          icon: Brain,
        },
        {
          name: isRomanian ? 'Analiza generala de sanatate' : 'General health analysis',
          free: true,
          premium: true,
          family: true,
          icon: HeartPulse,
        },
        {
          name: isRomanian ? 'Cardiolog AI' : 'AI Cardiologist',
          free: false,
          premium: true,
          family: true,
          icon: Heart,
        },
        {
          name: isRomanian ? 'Endocrinolog AI' : 'AI Endocrinologist',
          free: false,
          premium: true,
          family: true,
          icon: Activity,
        },
        {
          name: isRomanian ? 'Hematolog AI' : 'AI Hematologist',
          free: false,
          premium: true,
          family: true,
          icon: Activity,
        },
        {
          name: isRomanian ? 'Hepatolog AI' : 'AI Hepatologist',
          free: false,
          premium: true,
          family: true,
          icon: Activity,
        },
        {
          name: isRomanian ? 'Nefrolog AI' : 'AI Nephrologist',
          free: false,
          premium: true,
          family: true,
          icon: Activity,
        },
        {
          name: isRomanian ? 'Analiza lacunelor in screening' : 'Screening gap analysis',
          free: false,
          premium: true,
          family: true,
          icon: Stethoscope,
        },
      ],
    },
    {
      category: isRomanian ? 'Rapoarte & Partajare' : 'Reports & Sharing',
      items: [
        {
          name: isRomanian ? 'Export PDF rapoarte' : 'PDF report export',
          free: false,
          premium: true,
          family: true,
          icon: Download,
        },
        {
          name: isRomanian ? 'Partajare cu medicii' : 'Share with doctors',
          free: false,
          premium: true,
          family: true,
          icon: Share2,
        },
        {
          name: isRomanian ? 'Comparatii istorice' : 'Historical comparisons',
          free: false,
          premium: true,
          family: true,
          icon: History,
        },
      ],
    },
    {
      category: isRomanian ? 'Familie' : 'Family',
      items: [
        {
          name: isRomanian ? 'Membri familie' : 'Family members',
          free: '-',
          premium: '-',
          family: isRomanian ? 'Pana la 5' : 'Up to 5',
          icon: Users,
        },
        {
          name: isRomanian ? 'Fiecare membru are cont separat' : 'Each member has separate account',
          free: false,
          premium: false,
          family: true,
          icon: Shield,
        },
      ],
    },
  ];

  const renderFeatureValue = (value) => {
    if (value === true) {
      return <Check className="w-5 h-5 text-green-500 mx-auto" />;
    }
    if (value === false) {
      return <X className="w-5 h-5 text-slate-300 mx-auto" />;
    }
    return <span className="text-slate-700 font-medium">{value}</span>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <header className="px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2 text-cyan-600">
          <HeartPulse size={28} />
          <span className="text-xl font-bold text-slate-800">Analize.Online</span>
        </div>
        {user ? (
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800"
          >
            {isRomanian ? 'Inapoi la Dashboard' : 'Back to Dashboard'}
          </button>
        ) : (
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 text-sm font-medium text-cyan-600 hover:text-cyan-700"
          >
            {isRomanian ? 'Autentificare' : 'Sign In'}
          </button>
        )}
      </header>

      {/* Hero */}
      <div className="text-center px-6 py-12">
        <h1 className="text-4xl font-bold text-slate-800 mb-4">
          {isRomanian ? 'Alege planul potrivit pentru tine' : 'Choose the right plan for you'}
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          {isRomanian
            ? 'Toate planurile includ sincronizare automata cu Regina Maria, Synevo si alti provideri medicali.'
            : 'All plans include automatic sync with Regina Maria, Synevo and other medical providers.'}
        </p>
      </div>

      {/* Period Toggle */}
      <div className="flex justify-center mb-8">
        <div className="bg-slate-100 p-1 rounded-xl flex">
          <button
            onClick={() => setSelectedPeriod('monthly')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPeriod === 'monthly'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            {isRomanian ? 'Lunar' : 'Monthly'}
          </button>
          <button
            onClick={() => setSelectedPeriod('yearly')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedPeriod === 'yearly'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            {isRomanian ? 'Anual' : 'Yearly'}
            <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">
              -33%
            </span>
          </button>
        </div>
      </div>

      {/* Plan Cards */}
      <div className="max-w-6xl mx-auto px-6 pb-12">
        <div className="grid md:grid-cols-3 gap-6">
          {/* Free Plan */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-slate-800 mb-2">Free</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-800">0</span>
                <span className="text-slate-500">RON</span>
              </div>
              <p className="text-slate-500 mt-2 text-sm">
                {isRomanian
                  ? 'Pentru a incepe sa iti monitorizezi sanatatea'
                  : 'To start monitoring your health'}
              </p>
            </div>

            <div className="space-y-3 mb-6 flex-grow">
              <div className="flex items-center gap-2 text-slate-600">
                <Check className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <span>50 {isRomanian ? 'documente' : 'documents'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Check className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <span>2 {isRomanian ? 'conturi medicale' : 'medical accounts'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Check className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <span>3 {isRomanian ? 'analize AI/luna' : 'AI analyses/month'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Check className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <span>{isRomanian ? 'Doar analiza generala' : 'General analysis only'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <X className="w-5 h-5 flex-shrink-0" />
                <span className="line-through">{isRomanian ? 'Specialisti AI' : 'AI Specialists'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <X className="w-5 h-5 flex-shrink-0" />
                <span className="line-through">{isRomanian ? 'Export PDF' : 'PDF Export'}</span>
              </div>
            </div>

            <button
              onClick={() => handleSelectPlan('free')}
              disabled={user}
              className="w-full py-3 px-4 rounded-xl border border-slate-200 text-slate-600 font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              {user ? (isRomanian ? 'Planul curent' : 'Current plan') : (isRomanian ? 'Incepe gratuit' : 'Start free')}
            </button>
          </div>

          {/* Premium Plan */}
          <div className="bg-gradient-to-b from-amber-50 to-white rounded-2xl border-2 border-amber-400 p-6 flex flex-col relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                <Sparkles size={12} />
                {isRomanian ? 'Recomandat' : 'Recommended'}
              </span>
            </div>

            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Crown className="w-5 h-5 text-amber-500" />
                <h3 className="text-xl font-bold text-slate-800">Premium</h3>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-800">
                  {activePremium?.price || 5}
                </span>
                <span className="text-slate-500">
                  RON / {selectedPeriod === 'yearly' ? (isRomanian ? 'an' : 'year') : (isRomanian ? 'luna' : 'month')}
                </span>
              </div>
              {selectedPeriod === 'yearly' && (
                <p className="text-green-600 text-sm mt-1 font-medium">
                  {isRomanian ? 'Economisesti 20 RON pe an' : 'Save 20 RON per year'}
                </p>
              )}
              {selectedPeriod === 'monthly' && (
                <p className="text-slate-500 text-sm mt-1">
                  {isRomanian ? 'Mai putin decat o cafea' : 'Less than a coffee'}
                </p>
              )}
            </div>

            {/* Key Benefits Summary */}
            <div className="bg-amber-100/50 rounded-xl p-4 mb-4">
              <p className="text-sm font-semibold text-amber-800 mb-2">
                {isRomanian ? 'Ce primesti:' : 'What you get:'}
              </p>
              <ul className="space-y-1.5 text-sm text-amber-900">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span><strong>5</strong> {isRomanian ? 'doctori AI specialisti' : 'AI specialist doctors'}</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span><strong>30</strong> {isRomanian ? 'analize AI pe luna' : 'AI analyses per month'}</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>{isRomanian ? 'Analiza lacunelor in screening' : 'Screening gap analysis'}</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>{isRomanian ? 'Export PDF + Partajare cu medicii' : 'PDF export + Share with doctors'}</span>
                </li>
              </ul>
            </div>

            <div className="space-y-2 mb-6 flex-grow text-sm">
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span>500 {isRomanian ? 'documente' : 'documents'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Conturi medicale nelimitate' : 'Unlimited medical accounts'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Comparatii istorice' : 'Historical comparisons'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Sincronizare prioritara' : 'Priority sync'}</span>
              </div>
            </div>

            <button
              onClick={() => handleSelectPlan(activePremium?.id)}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium hover:from-amber-600 hover:to-orange-600 transition-colors flex items-center justify-center gap-2"
            >
              {isRomanian ? 'Alege Premium' : 'Choose Premium'}
              <ArrowRight size={18} />
            </button>
          </div>

          {/* Family Plan */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-purple-500" />
                <h3 className="text-xl font-bold text-slate-800">Family</h3>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-800">
                  {familyPlan?.price || 10}
                </span>
                <span className="text-slate-500">RON / {isRomanian ? 'luna' : 'month'}</span>
              </div>
              <p className="text-purple-600 text-sm mt-1 font-medium">
                {isRomanian
                  ? '= 2 RON/persoana la 5 membri'
                  : '= 2 RON/person with 5 members'}
              </p>
            </div>

            {/* Key Benefits Summary */}
            <div className="bg-purple-50 rounded-xl p-4 mb-4">
              <p className="text-sm font-semibold text-purple-800 mb-2">
                {isRomanian ? 'Ce primesti:' : 'What you get:'}
              </p>
              <ul className="space-y-1.5 text-sm text-purple-900">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-purple-600 flex-shrink-0" />
                  <span><strong>{isRomanian ? 'Pana la 5 membri' : 'Up to 5 members'}</strong></span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-purple-600 flex-shrink-0" />
                  <span>{isRomanian ? 'Fiecare cu cont propriu si date private' : 'Each with own account and private data'}</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-purple-600 flex-shrink-0" />
                  <span>{isRomanian ? 'Toate beneficiile Premium' : 'All Premium benefits'}</span>
                </li>
              </ul>
            </div>

            <div className="space-y-2 mb-6 flex-grow text-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                {isRomanian ? 'Fiecare membru primeste:' : 'Each member gets:'}
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-purple-500 flex-shrink-0" />
                <span>5 {isRomanian ? 'specialisti AI' : 'AI specialists'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-purple-500 flex-shrink-0" />
                <span>30 {isRomanian ? 'analize AI/luna' : 'AI analyses/month'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-purple-500 flex-shrink-0" />
                <span>500 {isRomanian ? 'documente' : 'documents'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-4 h-4 text-purple-500 flex-shrink-0" />
                <span>{isRomanian ? 'Toate functiile Premium' : 'All Premium features'}</span>
              </div>
            </div>

            <button
              onClick={() => handleSelectPlan('family_monthly')}
              className="w-full py-3 px-4 rounded-xl border-2 border-purple-500 text-purple-600 font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
            >
              {isRomanian ? 'Alege Family' : 'Choose Family'}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Premium Benefits Detail Section */}
      <div className="max-w-6xl mx-auto px-6 pb-12">
        <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 rounded-3xl p-8 border border-amber-200">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-amber-500 text-white px-4 py-1.5 rounded-full text-sm font-medium mb-4">
              <Crown size={16} />
              Premium
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              {isRomanian ? 'Ce primesti cu Premium?' : 'What do you get with Premium?'}
            </h2>
            <p className="text-slate-600">
              {isRomanian
                ? 'Acces complet la toate instrumentele pentru a-ti intelege sanatatea'
                : 'Full access to all tools to understand your health'}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {premiumBenefits.map((benefit, index) => (
              <div key={index} className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className={`w-10 h-10 rounded-lg ${benefit.bg} flex items-center justify-center mb-3`}>
                  <benefit.icon className={`w-5 h-5 ${benefit.color}`} />
                </div>
                <h3 className="font-semibold text-slate-800 mb-1">{benefit.title}</h3>
                <p className="text-sm text-slate-500">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Family Benefits Section */}
      <div className="max-w-6xl mx-auto px-6 pb-12">
        <div className="bg-gradient-to-br from-purple-50 via-violet-50 to-indigo-50 rounded-3xl p-8 border border-purple-200">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-purple-500 text-white px-4 py-1.5 rounded-full text-sm font-medium mb-4">
              <Users size={16} />
              Family
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              {isRomanian ? 'De ce Family?' : 'Why Family?'}
            </h2>
            <p className="text-slate-600">
              {isRomanian
                ? 'Cel mai bun pret pentru familii - toate beneficiile Premium pentru toti membrii'
                : 'Best price for families - all Premium benefits for all members'}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {familyBenefits.map((benefit, index) => (
              <div key={index} className="bg-white rounded-xl p-5 shadow-sm text-center">
                <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
                  <benefit.icon className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-slate-800 mb-2">{benefit.title}</h3>
                <p className="text-sm text-slate-500">{benefit.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 bg-white rounded-xl p-6 border border-purple-100">
            <h3 className="font-semibold text-slate-800 mb-4 text-center">
              {isRomanian ? 'Exemplu: Familie cu 5 membri' : 'Example: Family with 5 members'}
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-500 mb-1">{isRomanian ? 'Cu 5 planuri Premium separate' : 'With 5 separate Premium plans'}</p>
                <p className="text-2xl font-bold text-slate-800">5 x 5 = <span className="text-rose-500">25 RON</span>/luna</p>
              </div>
              <div className="text-center p-4 bg-purple-100 rounded-lg">
                <p className="text-sm text-purple-600 mb-1">{isRomanian ? 'Cu Family Plan' : 'With Family Plan'}</p>
                <p className="text-2xl font-bold text-purple-700">10 RON/luna</p>
                <p className="text-sm text-purple-600 font-medium">{isRomanian ? 'Economisesti 15 RON!' : 'Save 15 RON!'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Comparison Table - Collapsible */}
      <div className="max-w-6xl mx-auto px-6 pb-20">
        <button
          onClick={() => setShowComparison(!showComparison)}
          className="w-full flex items-center justify-center gap-2 py-4 text-slate-600 hover:text-slate-800 transition-colors"
        >
          <span className="font-medium">
            {isRomanian ? 'Vezi comparatia completa' : 'See full comparison'}
          </span>
          {showComparison ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {showComparison && (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden animate-in slide-in-from-top-4 duration-300">
            {/* Table Header */}
            <div className="grid grid-cols-4 gap-4 p-4 bg-slate-50 border-b border-slate-200 font-medium text-slate-600">
              <div>{isRomanian ? 'Functionalitate' : 'Feature'}</div>
              <div className="text-center">Free</div>
              <div className="text-center text-amber-600">Premium</div>
              <div className="text-center text-purple-600">Family</div>
            </div>

            {/* Table Body */}
            {features.map((category, catIndex) => (
              <div key={catIndex}>
                {/* Category Header */}
                <div className="grid grid-cols-4 gap-4 p-4 bg-slate-50/50 border-b border-slate-100">
                  <div className="col-span-4 font-semibold text-slate-800">{category.category}</div>
                </div>

                {/* Category Items */}
                {category.items.map((item, itemIndex) => (
                  <div
                    key={itemIndex}
                    className="grid grid-cols-4 gap-4 p-4 border-b border-slate-100 last:border-b-0 hover:bg-slate-50/50"
                  >
                    <div className="flex items-center gap-2 text-slate-700">
                      <item.icon className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="text-sm">{item.name}</span>
                    </div>
                    <div className="text-center text-sm">{renderFeatureValue(item.free)}</div>
                    <div className="text-center text-sm">{renderFeatureValue(item.premium)}</div>
                    <div className="text-center text-sm">{renderFeatureValue(item.family)}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* FAQ or Info */}
      <div className="max-w-6xl mx-auto px-6 pb-20 text-center">
        <p className="text-slate-500">
          {isRomanian ? 'Intrebari?' : 'Questions?'}{' '}
          <a href="mailto:support@analize.online" className="text-cyan-600 hover:underline">
            support@analize.online
          </a>
        </p>
      </div>
    </div>
  );
}
