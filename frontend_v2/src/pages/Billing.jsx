import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Crown, CreditCard, Calendar, CheckCircle, AlertCircle,
  ArrowLeft, ExternalLink, Users, Sparkles, XCircle, Check,
  Brain, Stethoscope, Download, History, Shield, Zap, ChevronDown, ChevronUp
} from 'lucide-react';
import api from '../api/client';
import UsageStats from '../components/UsageStats';
import FamilyManagement from '../components/FamilyManagement';
import { useSubscription } from '../context/SubscriptionContext';

export default function Billing() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { subscription, refreshSubscription, tier } = useSubscription();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [familyInfo, setFamilyInfo] = useState(null);
  const [specialists, setSpecialists] = useState({});

  // Check for payment completion
  const paymentStatus = searchParams.get('payment');

  useEffect(() => {
    fetchData();
    if (paymentStatus === 'complete') {
      // Refresh subscription status after payment
      setTimeout(() => {
        refreshSubscription();
        setSuccess(t('billing.paymentSuccess'));
      }, 2000);
    }
  }, [paymentStatus]);

  const fetchData = async () => {
    try {
      const [plansRes, familyRes, specialistsRes] = await Promise.all([
        api.get('/subscription/plans'),
        api.get('/subscription/family').catch(() => ({ data: { has_family: false } })),
        api.get('/health/specialists').catch(() => ({ data: { specialists: {} } }))
      ]);
      setPlans(plansRes.data.plans);
      setFamilyInfo(familyRes.data);
      setSpecialists(specialistsRes.data.specialists || {});
    } catch (err) {
      setError(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = async (planType) => {
    setCheckoutLoading(true);
    setError(null);

    try {
      const response = await api.post('/subscription/checkout', {
        plan_type: planType,
      });

      // Create and submit form for Netopia redirect
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = response.data.payment_url;

      const envKeyInput = document.createElement('input');
      envKeyInput.type = 'hidden';
      envKeyInput.name = 'env_key';
      envKeyInput.value = response.data.env_key;
      form.appendChild(envKeyInput);

      const dataInput = document.createElement('input');
      dataInput.type = 'hidden';
      dataInput.name = 'data';
      dataInput.value = response.data.data;
      form.appendChild(dataInput);

      document.body.appendChild(form);
      form.submit();

    } catch (err) {
      setError(err.response?.data?.detail || t('billing.checkoutError'));
      setCheckoutLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm(t('billing.confirmCancel'))) return;

    try {
      await api.post('/subscription/cancel');
      refreshSubscription();
      setSuccess(t('billing.cancelSuccess'));
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'));
    }
  };

  const handleReactivate = async () => {
    try {
      await api.post('/subscription/reactivate');
      refreshSubscription();
      setSuccess(t('billing.reactivateSuccess'));
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'));
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  const isPremium = tier === 'premium' || tier === 'family';

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t('billing.title')}</h1>
          <p className="text-slate-600">{t('billing.subtitle')}</p>
        </div>
      </div>

      {/* Status Messages */}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3 text-green-700">
          <CheckCircle className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Subscription */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm mb-6">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {tier === 'family' ? (
                <div className="p-3 bg-purple-100 rounded-xl">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
              ) : tier === 'premium' ? (
                <div className="p-3 bg-amber-100 rounded-xl">
                  <Crown className="w-6 h-6 text-amber-600" />
                </div>
              ) : (
                <div className="p-3 bg-slate-100 rounded-xl">
                  <Sparkles className="w-6 h-6 text-slate-600" />
                </div>
              )}
              <div>
                <h2 className="text-lg font-semibold text-slate-800">
                  {tier === 'family' ? 'Family' : tier === 'premium' ? 'Premium' : 'Free'}
                </h2>
                {isPremium && (
                  <p className="text-slate-500">
                    {subscription?.billing_cycle === 'yearly' ? t('billing.yearlyPlan') : t('billing.monthlyPlan')}
                  </p>
                )}
              </div>
            </div>

            {isPremium && (
              <div className="text-right">
                <p className="text-sm text-slate-500">{t('billing.nextBilling')}</p>
                <p className="font-medium text-slate-800">
                  {subscription?.current_period_end
                    ? new Date(subscription.current_period_end).toLocaleDateString()
                    : '-'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Subscription Actions */}
        {isPremium && (
          <div className="p-4 bg-slate-50 flex items-center justify-between">
            {subscription?.cancel_at_period_end ? (
              <>
                <div className="flex items-center gap-2 text-amber-600">
                  <AlertCircle size={18} />
                  <span className="text-sm">{t('billing.cancelledNotice')}</span>
                </div>
                <button
                  onClick={handleReactivate}
                  className="px-4 py-2 text-sm font-medium text-cyan-600 hover:text-cyan-700"
                >
                  {t('billing.reactivate')}
                </button>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle size={18} />
                  <span className="text-sm">{t('billing.activeSubscription')}</span>
                </div>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700"
                >
                  {t('billing.cancelSubscription')}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Usage Stats */}
      <UsageStats />

      {/* Upgrade Options (for free users) */}
      {!isPremium && (
        <div className="mb-6 space-y-6">
          {/* What you get with Premium */}
          <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 rounded-2xl border border-amber-200 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-amber-500 rounded-lg">
                <Crown className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800">
                  {t('billing.whatYouGet', 'Ce primești cu Premium')}
                </h3>
                <p className="text-sm text-slate-600">
                  {t('billing.fullAccess', 'Acces complet la toate funcționalitățile')}
                </p>
              </div>
            </div>

            {/* Benefits Grid */}
            <div className="grid md:grid-cols-2 gap-3 mb-6">
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <Brain className="w-5 h-5 text-violet-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">
                    {isRomanian ? 'Specialiști AI dinamici' : 'Dynamic AI Specialists'}
                  </p>
                  <p className="text-xs text-slate-500">
                    {Object.keys(specialists).length > 0
                      ? Object.values(specialists).map(s => s.name).join(', ')
                      : (isRomanian ? 'Cardiolog, Endocrinolog, Hematolog și alții' : 'Cardiologist, Endocrinologist, Hematologist and more')}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <Stethoscope className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">{t('billing.benefit2Title', 'Analiza lacunelor în screening')}</p>
                  <p className="text-xs text-slate-500">{t('billing.benefit2Desc', 'Ce analize ar trebui să faci, bazat pe profilul tău')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <Download className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">{t('billing.benefit3Title', 'Export PDF')}</p>
                  <p className="text-xs text-slate-500">{t('billing.benefit3Desc', 'Descarcă rapoartele pentru a le arăta medicului')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <History className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">{t('billing.benefit4Title', 'Comparații istorice')}</p>
                  <p className="text-xs text-slate-500">{t('billing.benefit4Desc', 'Compară analizele de acum cu cele din trecut')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <Shield className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">{t('billing.benefit5Title', 'Conturi medicale nelimitate')}</p>
                  <p className="text-xs text-slate-500">{t('billing.benefit5Desc', 'Conectează Regina Maria, Synevo, Medlife, etc.')}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white/70 rounded-lg p-3">
                <Zap className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-800">{t('billing.benefit6Title', '30 analize AI / lună')}</p>
                  <p className="text-xs text-slate-500">{t('billing.benefit6Desc', 'De 10x mai multe decât planul gratuit')}</p>
                </div>
              </div>
            </div>

            {/* Pricing Options */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Premium Monthly */}
              <div className="bg-white rounded-xl p-4 border-2 border-amber-300 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-600">{t('billing.monthly', 'Lunar')}</span>
                </div>
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-3xl font-bold text-slate-800">5</span>
                  <span className="text-slate-500">RON / lună</span>
                </div>
                <p className="text-xs text-slate-500 mb-4">{t('billing.lessThanCoffee', 'Mai puțin decât o cafea')}</p>
                <button
                  onClick={() => handleCheckout('premium_monthly')}
                  disabled={checkoutLoading}
                  className="w-full py-2.5 px-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg font-medium hover:from-amber-600 hover:to-orange-600 transition-colors disabled:opacity-50"
                >
                  {checkoutLoading ? t('common.loading') : t('billing.getPremium', 'Obține Premium')}
                </button>
              </div>

              {/* Premium Yearly */}
              <div className="bg-white rounded-xl p-4 border-2 border-green-400 shadow-sm relative">
                <span className="absolute -top-2 right-4 bg-green-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {t('billing.save33', '-33%')}
                </span>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-600">{t('billing.yearly', 'Anual')}</span>
                  <span className="text-xs text-green-600 font-medium">{t('billing.bestValue', 'Cea mai bună valoare')}</span>
                </div>
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-3xl font-bold text-slate-800">40</span>
                  <span className="text-slate-500">RON / an</span>
                </div>
                <p className="text-xs text-green-600 mb-4">{t('billing.save20', 'Economisești 20 RON pe an')}</p>
                <button
                  onClick={() => handleCheckout('premium_yearly')}
                  disabled={checkoutLoading}
                  className="w-full py-2.5 px-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg font-medium hover:from-green-600 hover:to-emerald-600 transition-colors disabled:opacity-50"
                >
                  {checkoutLoading ? t('common.loading') : t('billing.getPremiumYearly', 'Obține Premium Anual')}
                </button>
              </div>
            </div>
          </div>

          {/* Family Plan */}
          <div className="bg-gradient-to-br from-purple-50 via-violet-50 to-indigo-50 rounded-2xl border border-purple-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-purple-500 rounded-lg">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-800">Family Plan</h3>
                <p className="text-sm text-slate-600">{t('billing.familySubtitle', 'Premium pentru toată familia')}</p>
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold text-slate-800">10</span>
                <span className="text-slate-500"> RON / lună</span>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-3 mb-4">
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <Users className="w-6 h-6 text-purple-600 mx-auto mb-1" />
                <p className="font-medium text-slate-800">{t('billing.upTo5', 'Până la 5 membri')}</p>
                <p className="text-xs text-slate-500">{t('billing.familyMembers', 'Soț/soție, copii, părinți')}</p>
              </div>
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <Shield className="w-6 h-6 text-purple-600 mx-auto mb-1" />
                <p className="font-medium text-slate-800">{t('billing.separateData', 'Date separate')}</p>
                <p className="text-xs text-slate-500">{t('billing.privateAccounts', 'Fiecare cu contul său privat')}</p>
              </div>
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <Sparkles className="w-6 h-6 text-purple-600 mx-auto mb-1" />
                <p className="font-medium text-slate-800">{t('billing.allPremium', 'Toate funcțiile Premium')}</p>
                <p className="text-xs text-slate-500">{t('billing.forEachMember', 'Pentru fiecare membru')}</p>
              </div>
            </div>

            <div className="bg-white/50 rounded-lg p-3 mb-4 text-center">
              <p className="text-sm text-purple-700">
                <span className="font-semibold">{t('billing.savingExample', 'Exemplu:')}</span> {t('billing.savingCalc', 'La 5 membri = 2 RON/persoană în loc de 5 RON')}
              </p>
            </div>

            <button
              onClick={() => handleCheckout('family_monthly')}
              disabled={checkoutLoading}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-purple-500 to-violet-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-violet-600 transition-colors disabled:opacity-50"
            >
              {checkoutLoading ? t('common.loading') : t('billing.getFamily', 'Obține Family')}
            </button>
          </div>
        </div>
      )}

      {/* Family Management */}
      <div className="mb-6">
        <FamilyManagement
          familyInfo={familyInfo}
          tier={tier}
          onRefresh={fetchData}
        />
      </div>

      {/* Payment Info */}
      <div className="mt-6 p-4 bg-slate-50 rounded-xl">
        <div className="flex items-center gap-2 text-slate-600 text-sm">
          <CreditCard size={16} />
          <span>{t('billing.securePayment')}</span>
        </div>
        <p className="text-xs text-slate-500 mt-2">{t('billing.paymentDisclaimer')}</p>
      </div>
    </div>
  );
}
