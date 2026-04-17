import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Crown, ArrowRight } from 'lucide-react';
import { useSubscription } from '../context/SubscriptionContext';

export default function TrialBanner() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isTrialing, trialDaysRemaining, subscription } = useSubscription();

  if (!isTrialing()) return null;

  const days = trialDaysRemaining();
  if (days === null) return null;

  const isUrgent = days <= 7;
  const trialExpired = subscription?.is_trial && subscription?.status !== 'trialing' && subscription?.tier === 'free';

  if (trialExpired) {
    return (
      <div className="bg-gradient-to-r from-red-500 to-rose-500 text-white px-4 py-2.5 flex items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-2">
          <Crown size={16} />
          <span className="font-medium">{t('subscription.trialExpiredMessage')}</span>
        </div>
        <button
          onClick={() => navigate('/billing')}
          className="flex items-center gap-1 bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full text-xs font-semibold transition-colors whitespace-nowrap"
        >
          {t('subscription.trialUpgradeNow')}
          <ArrowRight size={14} />
        </button>
      </div>
    );
  }

  return (
    <div className={`${isUrgent ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-amber-500 to-orange-500'} text-white px-4 py-2.5 flex items-center justify-between gap-3 text-sm`}>
      <div className="flex items-center gap-2">
        <Crown size={16} />
        <span className="font-medium">
          {t('subscription.trialBannerText', { days })}
        </span>
      </div>
      <button
        onClick={() => navigate('/billing')}
        className="flex items-center gap-1 bg-white/20 hover:bg-white/30 px-3 py-1 rounded-full text-xs font-semibold transition-colors whitespace-nowrap"
      >
        {t('subscription.trialKeepPremium')}
        <ArrowRight size={14} />
      </button>
    </div>
  );
}
