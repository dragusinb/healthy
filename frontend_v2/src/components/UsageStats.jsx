import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Link, Brain, AlertCircle } from 'lucide-react';
import { useSubscription } from '../context/SubscriptionContext';

export default function UsageStats({ compact = false }) {
  const { t } = useTranslation();
  const { usage, limits, loading, tier } = useSubscription();

  if (loading || !usage) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-lg h-24"></div>
    );
  }

  const stats = [
    {
      icon: FileText,
      label: t('subscription.documents'),
      current: usage.documents,
      limit: limits.max_documents,
      percent: usage.documents_percent,
      color: 'cyan',
    },
    {
      icon: Link,
      label: t('subscription.providers'),
      current: usage.providers,
      limit: limits.max_providers > 100 ? '∞' : limits.max_providers,
      percent: limits.max_providers > 100 ? 0 : usage.providers_percent,
      color: 'violet',
      hideBar: limits.max_providers > 100,
    },
    {
      icon: Brain,
      label: t('subscription.aiAnalyses'),
      current: usage.ai_analyses_this_month,
      limit: limits.ai_analyses_per_month,
      percent: usage.ai_analyses_percent,
      color: 'amber',
    },
  ];

  if (compact) {
    return (
      <div className="flex gap-4 text-sm">
        {stats.map((stat, i) => (
          <div key={i} className="flex items-center gap-2">
            <stat.icon className={`w-4 h-4 text-${stat.color}-500`} />
            <span className="text-gray-600">
              {stat.current}/{stat.limit}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">{t('subscription.usage')}</h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          tier === 'free'
            ? 'bg-gray-100 text-gray-600'
            : tier === 'family'
              ? 'bg-purple-100 text-purple-700'
              : 'bg-amber-100 text-amber-700'
        }`}>
          {tier === 'free' ? 'Free' : tier === 'family' ? 'Family' : 'Premium'}
        </span>
      </div>

      <div className="p-4 space-y-4">
        {stats.map((stat, i) => (
          <div key={i}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <stat.icon className={`w-4 h-4 text-${stat.color}-500`} />
                <span className="text-sm text-gray-600">{stat.label}</span>
              </div>
              <span className="text-sm font-medium text-gray-800">
                {stat.current} / {stat.limit}
              </span>
            </div>
            {!stat.hideBar && (
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    stat.percent >= 90
                      ? 'bg-red-500'
                      : stat.percent >= 70
                        ? 'bg-amber-500'
                        : `bg-${stat.color}-500`
                  }`}
                  style={{ width: `${Math.min(100, stat.percent)}%` }}
                />
              </div>
            )}
            {stat.percent >= 90 && (
              <div className="flex items-center gap-1 mt-1 text-xs text-red-600">
                <AlertCircle className="w-3 h-3" />
                {t('subscription.nearLimit')}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
