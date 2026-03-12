import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, Brain, TrendingUp, AlertTriangle, Clock, ChevronDown } from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../api/client';

const ICON_MAP = {
  file: FileText,
  brain: Brain,
  trending_up: TrendingUp,
  alert: AlertTriangle,
};

const TYPE_STYLES = {
  document: { dot: 'bg-primary-500', iconBg: 'bg-primary-50', iconColor: 'text-primary-600' },
  analysis: { dot: 'bg-violet-500', iconBg: 'bg-violet-50', iconColor: 'text-violet-600' },
  improvement: { dot: 'bg-emerald-500', iconBg: 'bg-emerald-50', iconColor: 'text-emerald-600' },
  alert: { dot: 'bg-rose-500', iconBg: 'bg-rose-50', iconColor: 'text-rose-600' },
};

function formatTimeAgo(dateStr, t) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return t('healthTimeline.today');
  if (diffDays === 1) return t('healthTimeline.yesterday');
  if (diffDays < 7) return `${diffDays} ${t('common.days')}`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo`;
  return `${Math.floor(diffDays / 365)}y`;
}

export default function HealthTimeline({ limit = 8 }) {
  const { t } = useTranslation();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    api.get(`/dashboard/timeline?limit=20`)
      .then(res => setEvents(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="flex gap-3 animate-pulse">
            <div className="w-8 h-8 rounded-full bg-slate-100 shrink-0" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-100 rounded w-3/4" />
              <div className="h-3 bg-slate-100 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-slate-600">
        <Clock size={32} className="mx-auto mb-2 opacity-50" />
        <p className="text-sm">{t('healthTimeline.noEvents')}</p>
      </div>
    );
  }

  const visibleEvents = showAll ? events : events.slice(0, limit);

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-px bg-slate-200" />

      <div className="space-y-1">
        {visibleEvents.map((event, i) => {
          const style = TYPE_STYLES[event.type] || TYPE_STYLES.document;
          const IconComponent = ICON_MAP[event.icon] || FileText;

          return (
            <Link
              key={i}
              to={event.link || '#'}
              className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors group relative"
            >
              {/* Timeline dot + icon */}
              <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0 z-10 border-2 border-white shadow-sm", style.iconBg)}>
                <IconComponent size={14} className={style.iconColor} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate group-hover:text-primary-600 transition-colors">
                  {event.title}
                </p>
                <div className="flex items-center gap-2 text-xs text-slate-600">
                  <span>{event.subtitle}</span>
                  <span>·</span>
                  <span>{formatTimeAgo(event.date, t)}</span>
                </div>
              </div>

              {/* Risk level badge for analyses */}
              {event.risk_level && event.risk_level !== 'normal' && (
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded-full font-medium shrink-0",
                  event.risk_level === 'attention' ? 'bg-amber-50 text-amber-600' :
                  event.risk_level === 'concern' ? 'bg-orange-50 text-orange-600' :
                  event.risk_level === 'urgent' ? 'bg-rose-50 text-rose-600' : ''
                )}>
                  {t(`healthReports.riskLevels.${event.risk_level}`)}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {events.length > limit && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="w-full mt-3 flex items-center justify-center gap-1 text-sm text-slate-500 hover:text-primary-600 py-2 transition-colors"
        >
          <ChevronDown size={14} />
          {t('healthTimeline.showMore')} ({events.length - limit})
        </button>
      )}
    </div>
  );
}
