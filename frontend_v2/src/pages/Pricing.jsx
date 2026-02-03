import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, X, Crown, Users, Sparkles, HeartPulse, ArrowRight, FileText, Brain, Share2, History, Zap, Shield } from 'lucide-react';
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
          family: isRomanian ? 'Nelimitat / membru' : 'Unlimited / member',
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
          name: isRomanian ? 'Specialisti AI (Cardiologie, Endocrinologie, etc.)' : 'AI Specialists (Cardiology, Endocrinology, etc.)',
          free: false,
          premium: true,
          family: true,
          icon: Brain,
        },
        {
          name: isRomanian ? 'Analiza lacunelor in screening' : 'Screening gap analysis',
          free: false,
          premium: true,
          family: true,
          icon: Brain,
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
          icon: FileText,
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
          icon: Users,
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
          <span className="text-xl font-bold text-slate-800">Healthy.ai</span>
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
            ? 'Toate planurile includ acces la sincronizarea automata a analizelor medicale si monitorizarea biomarkerilor.'
            : 'All plans include access to automatic medical test sync and biomarker monitoring.'}
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
      <div className="max-w-6xl mx-auto px-6 pb-8">
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
                <span>{isRomanian ? 'Analiza generala' : 'General analysis'}</span>
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
                {isRomanian ? 'Popular' : 'Popular'}
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
                <p className="text-green-600 text-sm mt-1">
                  {isRomanian ? 'Economisesti 20 RON pe an' : 'Save 20 RON per year'}
                </p>
              )}
              <p className="text-slate-500 mt-2 text-sm">
                {isRomanian
                  ? 'Acces complet la toate functiile premium'
                  : 'Full access to all premium features'}
              </p>
            </div>

            <div className="space-y-3 mb-6 flex-grow">
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>500 {isRomanian ? 'documente' : 'documents'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Conturi medicale nelimitate' : 'Unlimited medical accounts'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>30 {isRomanian ? 'analize AI/luna' : 'AI analyses/month'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Toti specialistii AI' : 'All AI specialists'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Export PDF rapoarte' : 'PDF report export'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Partajare cu medicii' : 'Share with doctors'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                <span>{isRomanian ? 'Comparatii istorice' : 'Historical comparisons'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
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
              <p className="text-slate-500 mt-2 text-sm">
                {isRomanian
                  ? 'Premium pentru toata familia ta'
                  : 'Premium for your whole family'}
              </p>
            </div>

            <div className="space-y-3 mb-6 flex-grow">
              <div className="flex items-center gap-2 text-purple-700 font-semibold">
                <Users className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>{isRomanian ? 'Pana la 5 membri' : 'Up to 5 members'}</span>
              </div>
              <div className="border-t border-slate-100 my-2"></div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                {isRomanian ? 'Fiecare membru primeste:' : 'Each member gets:'}
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>500 {isRomanian ? 'documente' : 'documents'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>{isRomanian ? 'Conturi medicale nelimitate' : 'Unlimited medical accounts'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>30 {isRomanian ? 'analize AI/luna' : 'AI analyses/month'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>{isRomanian ? 'Toate functiile Premium' : 'All Premium features'}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-700">
                <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>{isRomanian ? 'Conturi separate, date private' : 'Separate accounts, private data'}</span>
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

      {/* Feature Comparison Table */}
      <div className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-slate-800 text-center mb-8">
          {isRomanian ? 'Comparatie detaliata' : 'Detailed comparison'}
        </h2>

        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
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
