import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingUp, TrendingDown, Minus, ChevronRight, Info } from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../api/client';

const GRADE_CONFIG = {
  excellent: { color: 'text-emerald-600', bg: 'bg-emerald-50', ring: 'stroke-emerald-500', label: 'healthScore.excellent' },
  good: { color: 'text-teal-600', bg: 'bg-teal-50', ring: 'stroke-teal-500', label: 'healthScore.good' },
  fair: { color: 'text-amber-600', bg: 'bg-amber-50', ring: 'stroke-amber-500', label: 'healthScore.fair' },
  needs_attention: { color: 'text-orange-600', bg: 'bg-orange-50', ring: 'stroke-orange-500', label: 'healthScore.needsAttention' },
  critical: { color: 'text-rose-600', bg: 'bg-rose-50', ring: 'stroke-rose-500', label: 'healthScore.critical' },
};

const ScoreRing = ({ score, grade, size = 140 }) => {
  const config = GRADE_CONFIG[grade] || GRADE_CONFIG.fair;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(circumference - (score / 100) * circumference);
    }, 300);
    return () => clearTimeout(timer);
  }, [score, circumference]);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth={strokeWidth}
          className="stroke-slate-100"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn(config.ring, "transition-all duration-1000 ease-out")}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-3xl font-bold", config.color)}>{score}</span>
        <span className="text-xs text-slate-600 font-medium">/100</span>
      </div>
    </div>
  );
};

export default function HealthScoreCard() {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.get('/dashboard/health-score')
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="card p-6 animate-pulse">
        <div className="flex items-center gap-6">
          <div className="w-[140px] h-[140px] rounded-full bg-slate-100" />
          <div className="flex-1 space-y-3">
            <div className="h-5 bg-slate-100 rounded w-32" />
            <div className="h-4 bg-slate-100 rounded w-48" />
            <div className="h-4 bg-slate-100 rounded w-40" />
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const grade = GRADE_CONFIG[data.grade] || GRADE_CONFIG.fair;

  return (
    <div className="card p-6">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        <ScoreRing score={data.score} grade={data.grade} />

        <div className="flex-1 text-center sm:text-left">
          <h3 className="text-lg font-bold text-slate-800 mb-1">
            {t('healthScore.title')}
          </h3>
          <span className={cn("inline-block px-3 py-1 rounded-full text-sm font-semibold mb-3", grade.bg, grade.color)}>
            {t(grade.label)}
          </span>

          {!data.has_data && (
            <p className="text-sm text-slate-600">
              {t('healthScore.noData')}
            </p>
          )}

          {data.has_data && (
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(data.components).map(([key, comp]) => (
                <div key={key} className="flex items-center gap-2 text-sm">
                  <div className="w-full bg-slate-100 rounded-full h-1.5">
                    <div
                      className={cn("h-1.5 rounded-full transition-all duration-700",
                        comp.score >= 80 ? 'bg-emerald-500' : comp.score >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                      )}
                      style={{ width: `${comp.score}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-600 whitespace-nowrap">
                    {t(`healthScore.${key}`)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Expandable insights */}
      {data.insights && data.insights.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors"
          >
            <Info size={14} />
            {t('healthScore.insights')}
            <ChevronRight size={14} className={cn("transition-transform", expanded && "rotate-90")} />
          </button>
          {expanded && (
            <div className="mt-3 space-y-2">
              {data.insights.map((insight, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-slate-600 bg-slate-50 rounded-lg p-2">
                  {insight.includes('improving') ? <TrendingUp size={14} className="text-emerald-500 mt-0.5 shrink-0" /> :
                   insight.includes('declining') || insight.includes('attention') ? <TrendingDown size={14} className="text-rose-500 mt-0.5 shrink-0" /> :
                   <Minus size={14} className="text-slate-500 mt-0.5 shrink-0" />}
                  <span>{t(`healthScore.insight_${insight}`)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
