import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { X, Crown, Check, Sparkles } from 'lucide-react';

export default function UpgradePrompt({ isOpen, onClose, reason, feature }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  if (!isOpen) return null;

  const getReasonText = () => {
    switch (reason) {
      case 'documents':
        return t('subscription.limitDocuments');
      case 'providers':
        return t('subscription.limitProviders');
      case 'ai_analyses':
        return t('subscription.limitAnalyses');
      case 'feature':
        return t('subscription.limitFeature', { feature });
      default:
        return t('subscription.limitGeneric');
    }
  };

  const premiumFeatures = [
    t('subscription.featureUnlimitedProviders'),
    t('subscription.feature500Documents'),
    t('subscription.feature30Analyses'),
    t('subscription.featureAllSpecialists'),
    t('subscription.featurePdfExport'),
    t('subscription.featureShareReports'),
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-8 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
          <div className="flex items-center gap-3 mb-2">
            <Crown className="w-8 h-8" />
            <h2 className="text-2xl font-bold">{t('subscription.upgradeTitle')}</h2>
          </div>
          <p className="text-amber-100">{getReasonText()}</p>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-amber-500" />
              <h3 className="font-semibold text-gray-800">{t('subscription.premiumIncludes')}</h3>
            </div>
            <ul className="space-y-2">
              {premiumFeatures.map((feature, i) => (
                <li key={i} className="flex items-center gap-2 text-gray-600">
                  <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Pricing */}
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 mb-6">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-800">5 RON</span>
              <span className="text-gray-500">/ {t('subscription.month')}</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {t('subscription.orYearly', { price: '40 RON' })}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors font-medium"
            >
              {t('common.cancel')}
            </button>
            <button
              onClick={() => {
                onClose();
                navigate('/billing');
              }}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:from-amber-600 hover:to-orange-600 transition-colors font-medium flex items-center justify-center gap-2"
            >
              <Crown size={18} />
              {t('subscription.upgradeCta')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
