import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';
import { useAuth } from './AuthContext';

const SubscriptionContext = createContext();

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

export const SubscriptionProvider = ({ children }) => {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [features, setFeatures] = useState(null);
  const [limits, setLimits] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSubscriptionStatus = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/subscription/status');
      setSubscription(response.data.subscription);
      setUsage(response.data.usage);
      setFeatures(response.data.features);
      setLimits(response.data.limits);
      setError(null);

      // Update LogRocket with subscription info
      try {
        const sub = response.data.subscription;
        const usg = response.data.usage;
        if (sub && user?.id) {
          window.LogRocket && window.LogRocket.identify(String(user.id), {
            subscriptionTier: sub.tier || 'free',
            subscriptionStatus: sub.status || 'active',
            aiAnalysesUsed: usg?.ai_analyses_this_month || 0,
            documentsCount: usg?.documents || 0,
          });
        }
      } catch (e) {
        // LogRocket not initialized
      }
    } catch (err) {
      console.error('Failed to fetch subscription:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchSubscriptionStatus();
  }, [fetchSubscriptionStatus]);

  // Helper functions to check limits
  const canUploadDocument = () => {
    if (!usage || !limits) return true;
    return usage.documents < limits.max_documents;
  };

  const canAddProvider = () => {
    if (!usage || !limits) return true;
    return usage.providers < limits.max_providers;
  };

  const canRunAnalysis = () => {
    if (!usage || !limits) return true;
    return usage.ai_analyses_this_month < limits.ai_analyses_per_month;
  };

  const hasFeature = (featureName) => {
    if (!features) return false;
    return features[featureName] === true;
  };

  const isPremium = () => {
    return subscription?.tier === 'premium' || subscription?.tier === 'family';
  };

  const isFree = () => {
    return !subscription || subscription.tier === 'free';
  };

  const isTrialing = () => {
    return subscription?.status === 'trialing';
  };

  const trialDaysRemaining = () => {
    return subscription?.trial_days_remaining ?? null;
  };

  const refreshSubscription = () => {
    setLoading(true);
    fetchSubscriptionStatus();
  };

  const value = {
    subscription,
    usage,
    features,
    limits,
    loading,
    error,
    canUploadDocument,
    canAddProvider,
    canRunAnalysis,
    hasFeature,
    isPremium,
    isFree,
    isTrialing,
    trialDaysRemaining,
    refreshSubscription,
    tier: subscription?.tier || 'free',
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

export default SubscriptionContext;
