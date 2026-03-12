import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Pill, Plus, Check, X, Trash2, Edit3, Clock, Flame, Calendar,
  ChevronDown, ChevronUp, MoreVertical, Undo2
} from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../api/client';
import { ListSkeleton } from '../components/Skeleton';
import { MedicationsEmpty } from '../components/EmptyState';

const TIME_ICONS = {
  morning: '🌅',
  afternoon: '☀️',
  evening: '🌙',
  bedtime: '💤',
};

const AddMedicationForm = ({ onAdd, onCancel, t }) => {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [timeOfDay, setTimeOfDay] = useState('morning');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    onAdd({ name: name.trim(), dosage, frequency, time_of_day: timeOfDay, notes });
  };

  return (
    <form onSubmit={handleSubmit} className="card p-5 border-2 border-primary-200 bg-primary-50/30">
      <h4 className="font-semibold text-slate-800 mb-4">{t('medications.addNew')}</h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
        <input
          type="text" value={name} onChange={(e) => setName(e.target.value)}
          placeholder={t('medications.namePlaceholder')}
          aria-label="Medication name"
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
          autoFocus required
        />
        <input
          type="text" value={dosage} onChange={(e) => setDosage(e.target.value)}
          placeholder={t('medications.dosagePlaceholder')}
          aria-label="Dosage"
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none"
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
        <select value={frequency} onChange={(e) => setFrequency(e.target.value)}
          aria-label="Frequency"
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none bg-white"
        >
          <option value="daily">{t('medications.frequencies.daily')}</option>
          <option value="twice_daily">{t('medications.frequencies.twiceDaily')}</option>
          <option value="weekly">{t('medications.frequencies.weekly')}</option>
          <option value="as_needed">{t('medications.frequencies.asNeeded')}</option>
        </select>
        <select value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)}
          aria-label="Time of day"
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none bg-white"
        >
          <option value="morning">{t('medications.times.morning')}</option>
          <option value="afternoon">{t('medications.times.afternoon')}</option>
          <option value="evening">{t('medications.times.evening')}</option>
          <option value="bedtime">{t('medications.times.bedtime')}</option>
        </select>
      </div>
      <input
        type="text" value={notes} onChange={(e) => setNotes(e.target.value)}
        placeholder={t('medications.notesPlaceholder')}
        aria-label="Notes"
        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none mb-4"
      />
      <div className="flex gap-2 justify-end">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        >
          {t('common.cancel')}
        </button>
        <button type="submit"
          className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
        >
          {t('common.add')}
        </button>
      </div>
    </form>
  );
};

const MedicationItem = ({ med, onToggle, onDelete, onUndo, t }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <div className={cn(
      "flex items-center gap-3 p-4 rounded-xl border transition-all",
      med.taken_today
        ? "bg-emerald-50/50 border-emerald-200"
        : "bg-white border-slate-200 hover:border-slate-300"
    )}>
      {/* Check button */}
      <button
        onClick={() => onToggle(med)}
        className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all border-2",
          med.taken_today
            ? "bg-emerald-500 border-emerald-500 text-white"
            : "border-slate-400 text-slate-500 hover:border-primary-500 hover:text-primary-500"
        )}
        aria-label="Mark as taken"
      >
        <Check size={18} />
      </button>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className={cn("font-medium text-sm", med.taken_today ? "text-emerald-700" : "text-slate-800")}>
          {med.name}
        </p>
        <div className="flex items-center gap-2 text-xs text-slate-600">
          {med.dosage && <span>{med.dosage}</span>}
          {med.dosage && med.time_of_day && <span>·</span>}
          {med.time_of_day && (
            <span className="flex items-center gap-1">
              {TIME_ICONS[med.time_of_day]} {t(`medications.times.${med.time_of_day}`)}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="relative">
        <button
          onClick={() => setShowActions(!showActions)}
          className="p-2 text-slate-500 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          aria-label="More actions"
        >
          <MoreVertical size={16} />
        </button>
        {showActions && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowActions(false)} />
            <div className="absolute right-0 top-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-20 py-1 min-w-[140px]">
              {med.taken_today && Array.isArray(med.today_logs) && med.today_logs.length > 0 && (
                <button
                  onClick={() => { onUndo(med); setShowActions(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Undo2 size={14} /> {t('medications.undo')}
                </button>
              )}
              <button
                onClick={() => { onDelete(med.id); setShowActions(false); }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-rose-600 hover:bg-rose-50"
              >
                <Trash2 size={14} /> {t('common.delete')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default function Medications() {
  const { t } = useTranslation();
  const [medications, setMedications] = useState([]);
  const [adherence, setAdherence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [medsRes, adherenceRes] = await Promise.all([
        api.get('/medications').catch(e => {
          if (e.response?.status === 401) return { data: [] };
          throw e;
        }),
        api.get('/medications/adherence').catch(e => {
          if (e.response?.status === 401) return { data: null };
          throw e;
        })
      ]);
      const medsRaw = medsRes?.data;
      setMedications(Array.isArray(medsRaw) ? medsRaw : []);
      const adhRaw = adherenceRes?.data;
      if (adhRaw && typeof adhRaw === 'object') {
        // Guard daily_data to always be an array
        setAdherence({
          ...adhRaw,
          daily_data: Array.isArray(adhRaw.daily_data) ? adhRaw.daily_data : []
        });
      } else {
        setAdherence(null);
      }
    } catch (e) {
      console.error('Failed to load medications', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAdd = async (data) => {
    try {
      await api.post('/medications', data);
      setShowAdd(false);
      fetchData();
    } catch (e) {
      console.error('Failed to add medication', e);
    }
  };

  const handleToggle = async (med) => {
    try {
      if (med.taken_today) {
        // Undo last log
        if (med.today_logs?.length > 0) {
          const lastLog = med.today_logs[med.today_logs.length - 1];
          await api.delete(`/medications/log/${lastLog.id}`);
        }
      } else {
        await api.post('/medications/log', {
          medication_id: med.id,
          time_slot: med.time_of_day
        });
      }
      fetchData();
    } catch (e) {
      console.error('Failed to toggle medication', e);
    }
  };

  const handleUndo = async (med) => {
    if (med.today_logs?.length > 0) {
      const lastLog = med.today_logs[med.today_logs.length - 1];
      try {
        await api.delete(`/medications/log/${lastLog.id}`);
        fetchData();
      } catch (e) {
        console.error('Failed to undo', e);
      }
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/medications/${id}`);
      fetchData();
    } catch (e) {
      console.error('Failed to delete medication', e);
    }
  };

  if (loading) {
    return <ListSkeleton rows={4} />;
  }

  const takenCount = medications.filter(m => m.taken_today).length;
  const totalCount = medications.length;

  return (
    <div className="space-y-6">
      {/* Adherence Stats */}
      {adherence && totalCount > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4 text-center">
            <Flame size={20} className={cn("mx-auto mb-1", adherence.streak > 0 ? "text-orange-500" : "text-slate-500")} />
            <p className="text-2xl font-bold text-slate-800">{adherence.streak}</p>
            <p className="text-xs text-slate-600">{t('medications.streakDays')}</p>
          </div>
          <div className="card p-4 text-center">
            <Check size={20} className="mx-auto mb-1 text-emerald-500" />
            <p className="text-2xl font-bold text-slate-800">{takenCount}/{totalCount}</p>
            <p className="text-xs text-slate-600">{t('medications.takenToday')}</p>
          </div>
          <div className="card p-4 text-center">
            <Calendar size={20} className="mx-auto mb-1 text-primary-500" />
            <p className="text-2xl font-bold text-slate-800">{adherence.adherence_pct}%</p>
            <p className="text-xs text-slate-600">{t('medications.adherence30d')}</p>
          </div>
          <div className="card p-4 text-center">
            <Pill size={20} className="mx-auto mb-1 text-violet-500" />
            <p className="text-2xl font-bold text-slate-800">{totalCount}</p>
            <p className="text-xs text-slate-600">{t('medications.activeMeds')}</p>
          </div>
        </div>
      )}

      {/* Today's checklist */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span className="p-1.5 bg-primary-50 text-primary-600 rounded-lg"><Pill size={18} /></span>
            {t('medications.todayChecklist')}
          </h3>
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-50 text-primary-600 rounded-lg text-sm font-medium hover:bg-primary-100 transition-colors"
          >
            <Plus size={16} /> {t('common.add')}
          </button>
        </div>

        {/* Progress bar */}
        {totalCount > 0 && (
          <div className="mb-4">
            <div className="flex justify-between text-xs text-slate-600 mb-1">
              <span>{takenCount} / {totalCount} {t('medications.taken')}</span>
              <span>{Math.round((takenCount / totalCount) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div
                className={cn(
                  "h-2 rounded-full transition-all duration-500",
                  takenCount === totalCount ? "bg-emerald-500" : "bg-primary-500"
                )}
                style={{ width: `${totalCount > 0 ? (takenCount / totalCount) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}

        {showAdd && (
          <div className="mb-4">
            <AddMedicationForm onAdd={handleAdd} onCancel={() => setShowAdd(false)} t={t} />
          </div>
        )}

        {medications.length === 0 && !showAdd ? (
          <MedicationsEmpty />
        ) : (
          <div className="space-y-2">
            {medications.map(med => (
              <MedicationItem
                key={med.id}
                med={med}
                onToggle={handleToggle}
                onDelete={handleDelete}
                onUndo={handleUndo}
                t={t}
              />
            ))}
          </div>
        )}
      </div>

      {/* Adherence chart */}
      {adherence && adherence.daily_data && adherence.daily_data.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <span className="p-1.5 bg-violet-50 text-violet-600 rounded-lg"><Calendar size={18} /></span>
            {t('medications.adherenceHistory')}
          </h3>
          <div className="flex items-end gap-1 h-20">
            {adherence.daily_data.map((day, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className={cn(
                    "w-full rounded-t-sm transition-all",
                    day.complete ? "bg-emerald-400" : day.taken > 0 ? "bg-amber-400" : "bg-slate-200"
                  )}
                  style={{ height: `${day.total > 0 ? Math.max(8, (day.taken / day.total) * 64) : 8}px` }}
                  title={`${day.date}: ${day.taken}/${day.total}`}
                />
                {i % 2 === 0 && (
                  <span className="text-[9px] text-slate-600">
                    {new Date(day.date).getDate()}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
