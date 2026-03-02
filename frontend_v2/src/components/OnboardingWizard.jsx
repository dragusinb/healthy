import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HeartPulse, Link as LinkIcon, User, Brain, ArrowRight, ArrowLeft,
  CheckCircle, Upload, Activity, ChevronRight, X, Sparkles
} from 'lucide-react';
import { cn } from '../lib/utils';

const steps = [
  { key: 'welcome', icon: HeartPulse, color: 'from-cyan-500 to-teal-500' },
  { key: 'connect', icon: LinkIcon, color: 'from-violet-500 to-purple-500' },
  { key: 'profile', icon: User, color: 'from-amber-500 to-orange-500' },
  { key: 'analyze', icon: Brain, color: 'from-emerald-500 to-teal-500' },
];

export default function OnboardingWizard({ onDismiss }) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);

  const handleComplete = () => {
    localStorage.setItem('onboardingCompleted', 'true');
    onDismiss();
  };

  const handleSkip = () => {
    localStorage.setItem('onboardingCompleted', 'true');
    onDismiss();
  };

  const step = steps[currentStep];
  const StepIcon = step.icon;
  const isLast = currentStep === steps.length - 1;

  return (
    <div className="card overflow-hidden mb-8 animate-in fade-in slide-in-from-bottom-8 duration-700 border-2 border-primary-100">
      {/* Progress bar */}
      <div className="h-1 bg-slate-100">
        <div
          className="h-1 bg-gradient-to-r from-cyan-500 to-teal-500 transition-all duration-500"
          style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
        />
      </div>

      <div className="p-6 md:p-8">
        {/* Header with close button */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={cn("w-12 h-12 rounded-2xl bg-gradient-to-br flex items-center justify-center shadow-lg", step.color)}>
              <StepIcon size={24} className="text-white" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {t('onboarding.step')} {currentStep + 1}/{steps.length}
              </p>
              <h3 className="text-xl font-bold text-slate-800">
                {t(`onboarding.${step.key}.title`)}
              </h3>
            </div>
          </div>
          <button onClick={handleSkip} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Step content */}
        <div className="mb-8">
          <p className="text-slate-600 mb-6 leading-relaxed">
            {t(`onboarding.${step.key}.description`)}
          </p>

          {/* Step-specific actions */}
          {step.key === 'welcome' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {['sync', 'analyze', 'track'].map((feature) => (
                <div key={feature} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                  <CheckCircle size={18} className="text-emerald-500 shrink-0" />
                  <span className="text-sm text-slate-700">{t(`onboarding.welcome.${feature}`)}</span>
                </div>
              ))}
            </div>
          )}

          {step.key === 'connect' && (
            <div className="space-y-3">
              <Link to="/linked-accounts" onClick={handleComplete}
                className="flex items-center gap-3 p-4 bg-violet-50 border border-violet-200 rounded-xl hover:bg-violet-100 transition-colors group"
              >
                <div className="p-2 bg-violet-100 rounded-lg">
                  <LinkIcon size={20} className="text-violet-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-violet-800">{t('onboarding.connect.linkAccount')}</p>
                  <p className="text-sm text-violet-600">{t('onboarding.connect.linkAccountDesc')}</p>
                </div>
                <ChevronRight size={18} className="text-violet-400 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link to="/documents" onClick={handleComplete}
                className="flex items-center gap-3 p-4 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors group"
              >
                <div className="p-2 bg-slate-100 rounded-lg">
                  <Upload size={20} className="text-slate-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-slate-800">{t('onboarding.connect.uploadPdf')}</p>
                  <p className="text-sm text-slate-500">{t('onboarding.connect.uploadPdfDesc')}</p>
                </div>
                <ChevronRight size={18} className="text-slate-400 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          )}

          {step.key === 'profile' && (
            <Link to="/profile" onClick={handleComplete}
              className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 transition-colors group"
            >
              <div className="p-2 bg-amber-100 rounded-lg">
                <User size={20} className="text-amber-600" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-amber-800">{t('onboarding.profile.completeProfile')}</p>
                <p className="text-sm text-amber-600">{t('onboarding.profile.completeProfileDesc')}</p>
              </div>
              <ChevronRight size={18} className="text-amber-400 group-hover:translate-x-1 transition-transform" />
            </Link>
          )}

          {step.key === 'analyze' && (
            <Link to="/health" onClick={handleComplete}
              className="flex items-center gap-3 p-4 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl hover:from-emerald-600 hover:to-teal-600 transition-colors group"
            >
              <div className="p-2 bg-white/20 rounded-lg">
                <Sparkles size={20} />
              </div>
              <div className="flex-1">
                <p className="font-medium">{t('onboarding.analyze.runAnalysis')}</p>
                <p className="text-sm text-emerald-100">{t('onboarding.analyze.runAnalysisDesc')}</p>
              </div>
              <ChevronRight size={18} className="text-emerald-200 group-hover:translate-x-1 transition-transform" />
            </Link>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ArrowLeft size={16} /> {t('common.back')}
          </button>

          <div className="flex items-center gap-2">
            {steps.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentStep(i)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all",
                  i === currentStep ? "bg-primary-500 w-6" : i < currentStep ? "bg-primary-300" : "bg-slate-200"
                )}
              />
            ))}
          </div>

          {isLast ? (
            <button onClick={handleComplete}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              {t('onboarding.done')} <CheckCircle size={16} />
            </button>
          ) : (
            <button onClick={() => setCurrentStep(currentStep + 1)}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              {t('common.next')} <ArrowRight size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
