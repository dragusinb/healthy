import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Crown, CreditCard, Calendar, CheckCircle, AlertCircle,
  ArrowLeft, ExternalLink, Users, Sparkles, XCircle
} from 'lucide-react';
import api from '../api/client';
import UsageStats from '../components/UsageStats';
import FamilyManagement from '../components/FamilyManagement';
import { useSubscription } from '../context/SubscriptionContext';

export default function Billing() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { subscription, refreshSubscription, tier } = useSubscription();

  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [familyInfo, setFamilyInfo] = useState(null);

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
      const [plansRes, familyRes] = await Promise.all([
        api.get('/subscription/plans'),
        api.get('/subscription/family').catch(() => ({ data: { has_family: false } }))
      ]);
      setPlans(plansRes.data.plans);
      setFamilyInfo(familyRes.data);
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
                <p className="text-slate-500">
                  {subscription?.billing_cycle === 'yearly' ? t('billing.yearlyPlan') : t('billing.monthlyPlan')}
                </p>
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
      <div className="mb-6">
        <UsageStats />
      </div>

      {/* Upgrade Options (for free users) */}
      {!isPremium && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl border border-amber-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Crown className="w-6 h-6 text-amber-500" />
            <h3 className="text-lg font-semibold text-slate-800">{t('billing.upgradeTitle')}</h3>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Premium Monthly */}
            <div className="bg-white rounded-xl p-4 border border-amber-200">
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-2xl font-bold text-slate-800">5 RON</span>
                <span className="text-slate-500">/ {t('pricing.monthShort')}</span>
              </div>
              <p className="text-sm text-slate-600 mb-4">{t('billing.premiumMonthlyDesc')}</p>
              <button
                onClick={() => handleCheckout('premium_monthly')}
                disabled={checkoutLoading}
                className="w-full py-2 px-4 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50"
              >
                {checkoutLoading ? t('common.loading') : t('billing.subscribe')}
              </button>
            </div>

            {/* Premium Yearly */}
            <div className="bg-white rounded-xl p-4 border border-amber-200 relative">
              <span className="absolute -top-2 right-4 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                -33%
              </span>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-2xl font-bold text-slate-800">40 RON</span>
                <span className="text-slate-500">/ {t('pricing.year')}</span>
              </div>
              <p className="text-sm text-slate-600 mb-4">{t('billing.premiumYearlyDesc')}</p>
              <button
                onClick={() => handleCheckout('premium_yearly')}
                disabled={checkoutLoading}
                className="w-full py-2 px-4 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50"
              >
                {checkoutLoading ? t('common.loading') : t('billing.subscribe')}
              </button>
            </div>
          </div>

          {/* Family Option */}
          <div className="mt-4 p-4 bg-white rounded-xl border border-purple-200">
            <div className="flex items-center gap-3 mb-2">
              <Users className="w-5 h-5 text-purple-500" />
              <span className="font-medium text-slate-800">Family Plan</span>
              <span className="text-lg font-bold text-slate-800">10 RON / {t('pricing.monthShort')}</span>
            </div>
            <p className="text-sm text-slate-600 mb-3">{t('billing.familyDesc')}</p>
            <button
              onClick={() => handleCheckout('family_monthly')}
              disabled={checkoutLoading}
              className="px-4 py-2 border-2 border-purple-500 text-purple-600 rounded-lg font-medium hover:bg-purple-50 transition-colors disabled:opacity-50"
            >
              {checkoutLoading ? t('common.loading') : t('billing.getFamily')}
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
