import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, Crown, Users, Sparkles, HeartPulse, ArrowRight } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Pricing() {
  const { t } = useTranslation();
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

  const freePlan = plans.find(p => p.id === 'free');
  const premiumMonthly = plans.find(p => p.id === 'premium_monthly');
  const premiumYearly = plans.find(p => p.id === 'premium_yearly');
  const familyPlan = plans.find(p => p.id === 'family_monthly');

  const activePremium = selectedPeriod === 'yearly' ? premiumYearly : premiumMonthly;

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
            {t('common.backToDashboard')}
          </button>
        ) : (
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 text-sm font-medium text-cyan-600 hover:text-cyan-700"
          >
            {t('auth.login')}
          </button>
        )}
      </header>

      {/* Hero */}
      <div className="text-center px-6 py-12">
        <h1 className="text-4xl font-bold text-slate-800 mb-4">
          {t('pricing.title')}
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          {t('pricing.subtitle')}
        </p>
      </div>

      {/* Period Toggle */}
      <div className="flex justify-center mb-12">
        <div className="bg-slate-100 p-1 rounded-xl flex">
          <button
            onClick={() => setSelectedPeriod('monthly')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPeriod === 'monthly'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            {t('pricing.monthly')}
          </button>
          <button
            onClick={() => setSelectedPeriod('yearly')}
            className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedPeriod === 'yearly'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            {t('pricing.yearly')}
            <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">
              -33%
            </span>
          </button>
        </div>
      </div>

      {/* Plans */}
      <div className="max-w-6xl mx-auto px-6 pb-20">
        <div className="grid md:grid-cols-3 gap-6">
          {/* Free Plan */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-slate-800 mb-2">Free</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-800">0</span>
                <span className="text-slate-500">RON</span>
              </div>
              <p className="text-slate-500 mt-2">{t('pricing.freeDesc')}</p>
            </div>

            <ul className="space-y-3 mb-6 flex-grow">
              {freePlan?.features && Object.entries(freePlan.features).map(([key, value]) => (
                <li key={key} className="flex items-center gap-2 text-slate-600">
                  <Check className="w-5 h-5 text-slate-400 flex-shrink-0" />
                  <span>{value}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSelectPlan('free')}
              disabled={user}
              className="w-full py-3 px-4 rounded-xl border border-slate-200 text-slate-600 font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              {user ? t('pricing.currentPlan') : t('pricing.getStarted')}
            </button>
          </div>

          {/* Premium Plan */}
          <div className="bg-gradient-to-b from-amber-50 to-white rounded-2xl border-2 border-amber-400 p-6 flex flex-col relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2">
              <span className="bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                <Sparkles size={12} />
                {t('pricing.popular')}
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
                  RON / {selectedPeriod === 'yearly' ? t('pricing.year') : t('pricing.monthShort')}
                </span>
              </div>
              {selectedPeriod === 'yearly' && (
                <p className="text-green-600 text-sm mt-1">{t('pricing.yearlySavings')}</p>
              )}
              <p className="text-slate-500 mt-2">{t('pricing.premiumDesc')}</p>
            </div>

            <ul className="space-y-3 mb-6 flex-grow">
              {activePremium?.features && Object.entries(activePremium.features).map(([key, value]) => {
                if (key === 'extras' && Array.isArray(value)) {
                  return value.map((extra, i) => (
                    <li key={`extra-${i}`} className="flex items-center gap-2 text-slate-600">
                      <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                      <span>{extra}</span>
                    </li>
                  ));
                }
                return (
                  <li key={key} className="flex items-center gap-2 text-slate-600">
                    <Check className="w-5 h-5 text-amber-500 flex-shrink-0" />
                    <span>{value}</span>
                  </li>
                );
              })}
            </ul>

            <button
              onClick={() => handleSelectPlan(activePremium?.id)}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium hover:from-amber-600 hover:to-orange-600 transition-colors flex items-center justify-center gap-2"
            >
              {t('pricing.upgradeToPremium')}
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
                <span className="text-slate-500">RON / {t('pricing.monthShort')}</span>
              </div>
              <p className="text-slate-500 mt-2">{t('pricing.familyDesc')}</p>
            </div>

            <ul className="space-y-3 mb-6 flex-grow">
              {familyPlan?.features && Object.entries(familyPlan.features).map(([key, value]) => {
                if (key === 'extras' && Array.isArray(value)) {
                  return value.map((extra, i) => (
                    <li key={`extra-${i}`} className="flex items-center gap-2 text-slate-600">
                      <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                      <span>{extra}</span>
                    </li>
                  ));
                }
                return (
                  <li key={key} className="flex items-center gap-2 text-slate-600">
                    <Check className="w-5 h-5 text-purple-500 flex-shrink-0" />
                    <span>{value}</span>
                  </li>
                );
              })}
            </ul>

            <button
              onClick={() => handleSelectPlan('family_monthly')}
              className="w-full py-3 px-4 rounded-xl border-2 border-purple-500 text-purple-600 font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
            >
              {t('pricing.getFamily')}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>

        {/* FAQ or Info */}
        <div className="mt-16 text-center">
          <p className="text-slate-500">
            {t('pricing.questions')}{' '}
            <a href="mailto:support@analize.online" className="text-cyan-600 hover:underline">
              support@analize.online
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
