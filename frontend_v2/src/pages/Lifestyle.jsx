import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
    Leaf, Apple, Dumbbell, Loader2, RefreshCw, CheckCircle,
    AlertTriangle, Shield, Droplets, Clock, Flame, Target,
    TrendingUp, ChevronRight, User, UtensilsCrossed, Footprints
} from 'lucide-react';
import { cn } from '../lib/utils';

const ANALYSIS_STEPS = [
    { key: 'loading', duration: 800 },
    { key: 'nutrition', duration: 6000 },
    { key: 'exercise', duration: 6000 },
    { key: 'saving', duration: 1000 },
    { key: 'finishing', duration: 1000 },
];

const Lifestyle = () => {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState('nutrition');
    const [latestData, setLatestData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisStep, setAnalysisStep] = useState(0);
    const [error, setError] = useState(null);

    const getStepLabel = (key) => t(`lifestyle.analysisSteps.${key}`) || key;

    useEffect(() => { fetchData(); }, []);

    useEffect(() => {
        if (!analyzing) { setAnalysisStep(0); return; }
        let currentStep = 0;
        const runSteps = () => {
            if (currentStep < ANALYSIS_STEPS.length) {
                setAnalysisStep(currentStep);
                currentStep++;
                setTimeout(runSteps, ANALYSIS_STEPS[currentStep - 1].duration);
            }
        };
        runSteps();
    }, [analyzing]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await api.get('/lifestyle/latest');
            setLatestData(res.data);
            setError(null);
        } catch (e) {
            console.error("Failed to fetch lifestyle data", e);
            setError("Failed to load lifestyle data");
        } finally {
            setLoading(false);
        }
    };

    const runAnalysis = async () => {
        setAnalyzing(true);
        setError(null);
        try {
            await api.post('/lifestyle/analyze');
            await fetchData();
        } catch (e) {
            console.error("Lifestyle analysis failed", e);
            setError(e.response?.data?.detail || "Analysis failed. Please try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-emerald-500" size={32} />
            </div>
        );
    }

    const nutrition = latestData?.nutrition;
    const exercise = latestData?.exercise;
    const hasReport = latestData?.has_report;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-emerald-100 text-emerald-600 rounded-xl">
                            <Leaf size={24} />
                        </div>
                        {t('lifestyle.title')}
                    </h1>
                    <p className="text-slate-500 mt-1">{t('lifestyle.subtitle')}</p>
                </div>

                <button
                    onClick={runAnalysis}
                    disabled={analyzing}
                    className={cn(
                        "flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all shadow-md",
                        analyzing
                            ? "bg-emerald-100 text-emerald-600 cursor-wait"
                            : "bg-emerald-600 text-white hover:bg-emerald-700 shadow-emerald-500/30"
                    )}
                >
                    {analyzing ? (
                        <>
                            <Loader2 className="animate-spin" size={20} />
                            {getStepLabel(ANALYSIS_STEPS[analysisStep]?.key)}
                        </>
                    ) : (
                        <>
                            <RefreshCw size={20} />
                            {hasReport ? t('lifestyle.refreshAdvice') : t('lifestyle.getAdvice')}
                        </>
                    )}
                </button>
            </div>

            {/* Profile Completeness Banner */}
            {hasReport && (!nutrition?.daily_targets?.calories || nutrition?.warnings?.some(w => w.toLowerCase().includes('profile'))) && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
                    <User size={20} className="text-amber-600 shrink-0" />
                    <p className="text-sm text-amber-700">
                        {t('lifestyle.profileIncomplete')}{' '}
                        <Link to="/profile" className="font-semibold underline hover:text-amber-800">
                            {t('nav.profile')} &rarr;
                        </Link>
                    </p>
                </div>
            )}

            {/* Analysis Progress */}
            {analyzing && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-emerald-100 rounded-full">
                            <Leaf size={24} className="text-emerald-600 animate-pulse" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-emerald-800">{t('lifestyle.title')}</h3>
                            <p className="text-sm text-emerald-600">{getStepLabel(ANALYSIS_STEPS[analysisStep]?.key)}</p>
                        </div>
                    </div>
                    <div className="space-y-2">
                        {ANALYSIS_STEPS.map((step, i) => (
                            <div key={step.key} className="flex items-center gap-3">
                                {i < analysisStep ? (
                                    <CheckCircle size={16} className="text-emerald-600" />
                                ) : i === analysisStep ? (
                                    <Loader2 size={16} className="text-emerald-600 animate-spin" />
                                ) : (
                                    <div className="w-4 h-4 rounded-full border-2 border-emerald-300" />
                                )}
                                <span className={cn(
                                    "text-sm",
                                    i <= analysisStep ? "text-emerald-700" : "text-emerald-400"
                                )}>
                                    {getStepLabel(step.key)}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {error && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-center gap-3">
                    <AlertTriangle size={20} />
                    {error}
                </div>
            )}

            {/* Main Content */}
            {!analyzing && hasReport ? (
                <>
                    {/* Tab Switcher */}
                    <div className="flex gap-2 bg-white border border-slate-200 rounded-xl p-1.5">
                        <button
                            onClick={() => setActiveTab('nutrition')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold text-sm transition-all",
                                activeTab === 'nutrition'
                                    ? "bg-emerald-600 text-white shadow-md"
                                    : "text-slate-600 hover:bg-emerald-50 hover:text-emerald-700"
                            )}
                        >
                            <Apple size={18} />
                            {t('lifestyle.tabs.nutrition')}
                        </button>
                        <button
                            onClick={() => setActiveTab('exercise')}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold text-sm transition-all",
                                activeTab === 'exercise'
                                    ? "bg-emerald-600 text-white shadow-md"
                                    : "text-slate-600 hover:bg-emerald-50 hover:text-emerald-700"
                            )}
                        >
                            <Dumbbell size={18} />
                            {t('lifestyle.tabs.exercise')}
                        </button>
                    </div>

                    {/* Date */}
                    {latestData?.created_at && (
                        <p className="text-sm text-slate-400 text-right">
                            {new Date(latestData.created_at).toLocaleDateString()}
                        </p>
                    )}

                    {/* Nutrition Tab */}
                    {activeTab === 'nutrition' && nutrition && (
                        <div className="space-y-6">
                            {/* Summary */}
                            <div className="card p-6">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 bg-emerald-100 rounded-lg">
                                        <Apple size={20} className="text-emerald-600" />
                                    </div>
                                    <h2 className="text-lg font-semibold text-slate-800">{t('lifestyle.nutrition.summary')}</h2>
                                </div>
                                <p className="text-slate-700 leading-relaxed">{nutrition.summary}</p>
                            </div>

                            {/* Daily Targets */}
                            {nutrition.daily_targets && Object.keys(nutrition.daily_targets).length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.nutrition.dailyTargets')}</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {nutrition.daily_targets.calories && (
                                            <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-xl border border-orange-100">
                                                <Flame size={24} className="text-orange-500 shrink-0" />
                                                <div>
                                                    <p className="text-xs text-orange-600 font-medium">{t('lifestyle.nutrition.calories')}</p>
                                                    <p className="font-semibold text-slate-800">{nutrition.daily_targets.calories}</p>
                                                </div>
                                            </div>
                                        )}
                                        {nutrition.daily_targets.hydration && (
                                            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl border border-blue-100">
                                                <Droplets size={24} className="text-blue-500 shrink-0" />
                                                <div>
                                                    <p className="text-xs text-blue-600 font-medium">{t('lifestyle.nutrition.hydration')}</p>
                                                    <p className="font-semibold text-slate-800">{nutrition.daily_targets.hydration}</p>
                                                </div>
                                            </div>
                                        )}
                                        {nutrition.daily_targets.meal_frequency && (
                                            <div className="flex items-center gap-3 p-4 bg-violet-50 rounded-xl border border-violet-100">
                                                <UtensilsCrossed size={24} className="text-violet-500 shrink-0" />
                                                <div>
                                                    <p className="text-xs text-violet-600 font-medium">{t('lifestyle.nutrition.mealFrequency')}</p>
                                                    <p className="font-semibold text-slate-800">{nutrition.daily_targets.meal_frequency}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Priority Foods */}
                            {nutrition.priority_foods?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.nutrition.priorityFoods')}</h3>
                                    <div className="space-y-4">
                                        {nutrition.priority_foods.map((group, i) => (
                                            <div key={i} className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h4 className="font-semibold text-emerald-800">{group.category}</h4>
                                                    {group.target && (
                                                        <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-medium">
                                                            {t('lifestyle.target')}: {group.target}
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-emerald-700 mb-3">{group.reason}</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {group.foods?.map((food, j) => (
                                                        <span key={j} className="inline-flex items-center gap-1 text-sm bg-white px-3 py-1.5 rounded-lg border border-emerald-200 text-slate-700">
                                                            <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                                                            {food}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Foods to Reduce */}
                            {nutrition.foods_to_reduce?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.nutrition.foodsToReduce')}</h3>
                                    <div className="space-y-3">
                                        {nutrition.foods_to_reduce.map((item, i) => (
                                            <div key={i} className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                                                <h4 className="font-semibold text-amber-800 mb-1">{item.category}</h4>
                                                <p className="text-sm text-amber-700 mb-2">{item.reason}</p>
                                                {item.alternatives?.length > 0 && (
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="text-xs text-amber-600 font-medium">{t('lifestyle.nutrition.alternatives')}:</span>
                                                        {item.alternatives.map((alt, j) => (
                                                            <span key={j} className="text-xs bg-white px-2 py-1 rounded border border-amber-200 text-slate-700">
                                                                {alt}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Meal Timing */}
                            {nutrition.meal_timing?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.nutrition.mealTiming')}</h3>
                                    <div className="space-y-3">
                                        {nutrition.meal_timing.map((meal, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                                                <Clock size={18} className="text-emerald-500 shrink-0 mt-0.5" />
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-semibold text-slate-800">{meal.meal}</span>
                                                        <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded">{meal.timing}</span>
                                                    </div>
                                                    <p className="text-sm text-slate-600 mt-0.5">{meal.focus}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Supplements */}
                            {nutrition.supplements_to_discuss?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.nutrition.supplements')}</h3>
                                    <div className="space-y-3">
                                        {nutrition.supplements_to_discuss.map((supp, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-violet-50 rounded-lg border border-violet-100">
                                                <Target size={18} className="text-violet-500 shrink-0 mt-0.5" />
                                                <div>
                                                    <span className="font-semibold text-slate-800">{supp.supplement}</span>
                                                    <p className="text-sm text-slate-600">{supp.reason}</p>
                                                    {supp.note && (
                                                        <p className="text-xs text-violet-600 mt-1 italic">{supp.note}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Nutrition Warnings */}
                            {nutrition.warnings?.length > 0 && (
                                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
                                    <h3 className="font-semibold text-rose-800 flex items-center gap-2 mb-2">
                                        <AlertTriangle size={18} />
                                        {t('lifestyle.warnings')}
                                    </h3>
                                    <ul className="space-y-1">
                                        {nutrition.warnings.map((w, i) => (
                                            <li key={i} className="text-sm text-rose-700 flex items-start gap-2">
                                                <span className="shrink-0 mt-1">-</span>
                                                {w}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Exercise Tab */}
                    {activeTab === 'exercise' && exercise && (
                        <div className="space-y-6">
                            {/* Summary */}
                            <div className="card p-6">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="p-2 bg-emerald-100 rounded-lg">
                                        <Dumbbell size={20} className="text-emerald-600" />
                                    </div>
                                    <h2 className="text-lg font-semibold text-slate-800">{t('lifestyle.exercise.summary')}</h2>
                                </div>
                                <p className="text-slate-700 leading-relaxed">{exercise.summary}</p>
                            </div>

                            {/* Current Assessment */}
                            {exercise.current_assessment && Object.keys(exercise.current_assessment).length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.exercise.assessment')}</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {exercise.current_assessment.activity_level && (
                                            <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                                                <p className="text-xs text-blue-600 font-medium mb-1">{t('lifestyle.exercise.activityLevel')}</p>
                                                <p className="font-semibold text-slate-800">{exercise.current_assessment.activity_level}</p>
                                            </div>
                                        )}
                                        {exercise.current_assessment.exercise_readiness && (
                                            <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                                                <p className="text-xs text-emerald-600 font-medium mb-1">{t('lifestyle.exercise.exerciseReadiness')}</p>
                                                <p className="font-semibold text-slate-800 capitalize">{exercise.current_assessment.exercise_readiness}</p>
                                            </div>
                                        )}
                                        {exercise.current_assessment.key_health_factors?.length > 0 && (
                                            <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                                                <p className="text-xs text-amber-600 font-medium mb-1">{t('lifestyle.exercise.healthFactors')}</p>
                                                <ul className="text-sm text-slate-700 space-y-0.5">
                                                    {exercise.current_assessment.key_health_factors.map((f, i) => (
                                                        <li key={i}>- {f}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Weekly Plan */}
                            {exercise.weekly_plan?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.exercise.weeklyPlan')}</h3>
                                    <div className="space-y-4">
                                        {exercise.weekly_plan.map((activity, i) => (
                                            <div key={i} className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                                                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                                                    <h4 className="font-semibold text-emerald-800 flex items-center gap-2">
                                                        <Dumbbell size={16} className="text-emerald-600" />
                                                        {activity.activity}
                                                    </h4>
                                                    <div className="flex gap-2 flex-wrap">
                                                        {activity.frequency && (
                                                            <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full">
                                                                {t('lifestyle.exercise.frequency')}: {activity.frequency}
                                                            </span>
                                                        )}
                                                        {activity.duration && (
                                                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                                                                {t('lifestyle.exercise.duration')}: {activity.duration}
                                                            </span>
                                                        )}
                                                        {activity.intensity && (
                                                            <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full">
                                                                {t('lifestyle.exercise.intensity')}: {activity.intensity}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                {activity.details && (
                                                    <p className="text-sm text-slate-700 mb-2">{activity.details}</p>
                                                )}
                                                {activity.biomarker_benefit && (
                                                    <p className="text-xs text-emerald-600 flex items-center gap-1">
                                                        <TrendingUp size={12} />
                                                        {t('lifestyle.exercise.biomarkerBenefit')}: {activity.biomarker_benefit}
                                                    </p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Daily Habits */}
                            {exercise.daily_habits?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.exercise.dailyHabits')}</h3>
                                    <div className="space-y-3">
                                        {exercise.daily_habits.map((habit, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                                                <Footprints size={18} className="text-emerald-500 shrink-0 mt-0.5" />
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-semibold text-slate-800">{habit.habit}</span>
                                                        {habit.when && (
                                                            <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded">{habit.when}</span>
                                                        )}
                                                    </div>
                                                    {habit.benefit && (
                                                        <p className="text-sm text-slate-600 mt-0.5">{habit.benefit}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Progression */}
                            {exercise.progression && Object.keys(exercise.progression).length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.exercise.progression')}</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {exercise.progression.current_week && (
                                            <div className="p-4 bg-emerald-50 rounded-xl border-2 border-emerald-300 relative">
                                                <div className="absolute -top-3 left-3 bg-emerald-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                                                    {t('lifestyle.exercise.currentWeek')}
                                                </div>
                                                <p className="text-sm text-slate-700 mt-2">{exercise.progression.current_week}</p>
                                            </div>
                                        )}
                                        {exercise.progression.week_4 && (
                                            <div className="p-4 bg-blue-50 rounded-xl border border-blue-200 relative">
                                                <div className="absolute -top-3 left-3 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                                                    {t('lifestyle.exercise.week4')}
                                                </div>
                                                <div className="flex items-center gap-1 mb-1 mt-1">
                                                    <ChevronRight size={14} className="text-blue-400" />
                                                    <ChevronRight size={14} className="text-blue-400 -ml-2" />
                                                </div>
                                                <p className="text-sm text-slate-700">{exercise.progression.week_4}</p>
                                            </div>
                                        )}
                                        {exercise.progression.week_8 && (
                                            <div className="p-4 bg-violet-50 rounded-xl border border-violet-200 relative">
                                                <div className="absolute -top-3 left-3 bg-violet-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                                                    {t('lifestyle.exercise.week8')}
                                                </div>
                                                <div className="flex items-center gap-1 mb-1 mt-1">
                                                    <ChevronRight size={14} className="text-violet-400" />
                                                    <ChevronRight size={14} className="text-violet-400 -ml-2" />
                                                    <ChevronRight size={14} className="text-violet-400 -ml-2" />
                                                </div>
                                                <p className="text-sm text-slate-700">{exercise.progression.week_8}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Precautions */}
                            {exercise.precautions?.length > 0 && (
                                <div className="card p-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">{t('lifestyle.exercise.precautions')}</h3>
                                    <div className="space-y-3">
                                        {exercise.precautions.map((prec, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
                                                <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
                                                <div>
                                                    <span className="font-semibold text-slate-800">{prec.concern}</span>
                                                    <p className="text-sm text-slate-600">{prec.recommendation}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Exercise Warnings */}
                            {exercise.warnings?.length > 0 && (
                                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
                                    <h3 className="font-semibold text-rose-800 flex items-center gap-2 mb-2">
                                        <AlertTriangle size={18} />
                                        {t('lifestyle.warnings')}
                                    </h3>
                                    <ul className="space-y-1">
                                        {exercise.warnings.map((w, i) => (
                                            <li key={i} className="text-sm text-rose-700 flex items-start gap-2">
                                                <span className="shrink-0 mt-1">-</span>
                                                {w}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </>
            ) : !analyzing && (
                /* Empty State */
                <div className="card p-12 text-center">
                    <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Leaf size={32} className="text-emerald-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">{t('lifestyle.noAnalysisYet')}</h3>
                    <p className="text-slate-500 mb-6 max-w-md mx-auto">
                        {t('lifestyle.noAnalysisHint')}
                    </p>
                    <button
                        onClick={runAnalysis}
                        disabled={analyzing}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 transition-colors"
                    >
                        <Leaf size={20} />
                        {t('lifestyle.getAdvice')}
                    </button>
                </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl text-sm text-slate-500">
                <Shield size={20} className="shrink-0 mt-0.5" />
                <p>
                    <strong>{t('common.disclaimer') || 'Disclaimer'}:</strong> {t('lifestyle.disclaimer')}
                </p>
            </div>
        </div>
    );
};

export default Lifestyle;
