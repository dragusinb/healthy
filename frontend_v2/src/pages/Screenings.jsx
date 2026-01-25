import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import api from '../api/client';
import {
    ClipboardList, Sparkles, Calendar, Clock, Loader2, AlertTriangle,
    CheckCircle, ChevronRight, ArrowLeft, RefreshCw, Heart, Activity,
    Shield, User
} from 'lucide-react';
import { cn } from '../lib/utils';

const CATEGORY_ICONS = {
    'Cardiovascular': Heart,
    'Cancer': Shield,
    'Metabolic': Activity,
    'General': ClipboardList
};

const Screenings = () => {
    const { t } = useTranslation();
    const [gapAnalysis, setGapAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [error, setError] = useState(null);
    const [profile, setProfile] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [gapRes, profileRes] = await Promise.all([
                api.get('/health/gap-analysis/latest').catch(() => ({ data: { has_report: false } })),
                api.get('/users/me').catch(() => ({ data: {} }))
            ]);

            if (gapRes.data.has_report) {
                setGapAnalysis({
                    summary: gapRes.data.summary,
                    recommended_tests: gapRes.data.recommended_tests,
                    created_at: gapRes.data.created_at
                });
            }
            setProfile(profileRes.data);
            setError(null);
        } catch (e) {
            console.error("Failed to fetch data", e);
            setError("Failed to load screenings data");
        } finally {
            setLoading(false);
        }
    };

    const runGapAnalysis = async () => {
        setAnalyzing(true);
        setError(null);
        try {
            const res = await api.post('/health/gap-analysis');
            setGapAnalysis({
                ...res.data.analysis,
                created_at: res.data.analyzed_at
            });
        } catch (e) {
            console.error("Gap analysis failed", e);
            setError(e.response?.data?.detail || "Analysis failed. Please try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    // Group tests by category
    const groupedTests = gapAnalysis?.recommended_tests?.reduce((acc, test) => {
        const category = test.category || 'General';
        if (!acc[category]) acc[category] = [];
        acc[category].push(test);
        return acc;
    }, {}) || {};

    // Count by priority
    const priorityCounts = gapAnalysis?.recommended_tests?.reduce((acc, test) => {
        const priority = test.priority || 'low';
        acc[priority] = (acc[priority] || 0) + 1;
        return acc;
    }, {}) || {};

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-primary-500" size={32} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center gap-4">
                    <Link
                        to="/health"
                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft size={20} className="text-slate-500" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                            <div className="p-2 bg-violet-100 text-violet-600 rounded-xl">
                                <ClipboardList size={24} />
                            </div>
                            {t('screenings.title') || 'Recommended Screenings'}
                        </h1>
                        <p className="text-slate-500 mt-1">
                            {t('screenings.subtitle') || 'Personalized health screening recommendations based on your profile'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={runGapAnalysis}
                    disabled={analyzing}
                    className={cn(
                        "flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all shadow-md",
                        analyzing
                            ? "bg-violet-100 text-violet-600 cursor-wait"
                            : "bg-violet-600 text-white hover:bg-violet-700 shadow-violet-500/30"
                    )}
                >
                    {analyzing ? (
                        <>
                            <Loader2 className="animate-spin" size={20} />
                            {t('common.analyzing') || 'Analyzing...'}
                        </>
                    ) : (
                        <>
                            <RefreshCw size={20} />
                            {t('screenings.refresh') || 'Refresh Recommendations'}
                        </>
                    )}
                </button>
            </div>

            {error && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl flex items-center gap-3">
                    <AlertTriangle size={20} />
                    {error}
                </div>
            )}

            {/* Profile Summary */}
            {profile && (profile.full_name || profile.date_of_birth || profile.gender) && (
                <div className="card p-4 flex items-center gap-4">
                    <div className="p-3 bg-slate-100 rounded-xl">
                        <User size={24} className="text-slate-600" />
                    </div>
                    <div className="flex-1">
                        <p className="font-medium text-slate-800">
                            {t('screenings.basedOnProfile') || 'Recommendations based on your profile'}
                        </p>
                        <div className="flex flex-wrap gap-3 mt-1 text-sm text-slate-500">
                            {profile.full_name && <span>{profile.full_name}</span>}
                            {profile.date_of_birth && (
                                <span>
                                    {Math.floor((new Date() - new Date(profile.date_of_birth)) / (365.25 * 24 * 60 * 60 * 1000))} years old
                                </span>
                            )}
                            {profile.gender && <span className="capitalize">{profile.gender}</span>}
                        </div>
                    </div>
                    <Link
                        to="/profile"
                        className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                        {t('screenings.updateProfile') || 'Update Profile'}
                    </Link>
                </div>
            )}

            {gapAnalysis ? (
                <>
                    {/* Summary Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="card p-4 text-center">
                            <p className="text-3xl font-bold text-slate-800">
                                {gapAnalysis.recommended_tests?.length || 0}
                            </p>
                            <p className="text-sm text-slate-500">{t('screenings.totalRecommended') || 'Recommended Tests'}</p>
                        </div>
                        <div className="card p-4 text-center bg-rose-50 border-rose-200">
                            <p className="text-3xl font-bold text-rose-600">
                                {priorityCounts.high || 0}
                            </p>
                            <p className="text-sm text-rose-600">{t('screenings.highPriority') || 'High Priority'}</p>
                        </div>
                        <div className="card p-4 text-center bg-amber-50 border-amber-200">
                            <p className="text-3xl font-bold text-amber-600">
                                {priorityCounts.medium || 0}
                            </p>
                            <p className="text-sm text-amber-600">{t('screenings.mediumPriority') || 'Medium Priority'}</p>
                        </div>
                        <div className="card p-4 text-center bg-slate-50">
                            <p className="text-3xl font-bold text-slate-600">
                                {priorityCounts.low || 0}
                            </p>
                            <p className="text-sm text-slate-600">{t('screenings.lowPriority') || 'Routine'}</p>
                        </div>
                    </div>

                    {/* Summary */}
                    {gapAnalysis.summary && (
                        <div className="card p-6">
                            <h2 className="text-lg font-semibold text-slate-800 mb-3">
                                {t('screenings.summary') || 'Summary'}
                            </h2>
                            <p className="text-slate-700 leading-relaxed">{gapAnalysis.summary}</p>
                            {gapAnalysis.created_at && (
                                <p className="text-sm text-slate-400 mt-3">
                                    {t('screenings.lastUpdated') || 'Last updated'}: {new Date(gapAnalysis.created_at).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Grouped Tests by Category */}
                    {Object.entries(groupedTests).map(([category, tests]) => {
                        const CategoryIcon = CATEGORY_ICONS[category] || ClipboardList;
                        return (
                            <div key={category} className="card overflow-hidden">
                                <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center gap-3">
                                    <div className="p-2 bg-white rounded-lg shadow-sm">
                                        <CategoryIcon size={20} className="text-slate-600" />
                                    </div>
                                    <h2 className="text-lg font-semibold text-slate-800">{category}</h2>
                                    <span className="text-sm text-slate-500">({tests.length} tests)</span>
                                </div>
                                <div className="divide-y divide-slate-50">
                                    {tests.map((test, i) => (
                                        <div key={i} className={cn(
                                            "p-4 hover:bg-slate-50 transition-colors",
                                            test.is_overdue && test.last_done_date === null && "bg-rose-50/50"
                                        )}>
                                            <div className="flex items-start justify-between gap-4 mb-2">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="font-semibold text-slate-800">{test.test_name}</span>
                                                    <span className={cn(
                                                        "text-xs px-2 py-0.5 rounded-full font-medium",
                                                        test.priority === 'high' ? "bg-rose-100 text-rose-700" :
                                                        test.priority === 'medium' ? "bg-amber-100 text-amber-700" :
                                                        "bg-slate-100 text-slate-600"
                                                    )}>
                                                        {test.priority === 'high' ? (t('screenings.high') || 'High Priority') :
                                                         test.priority === 'medium' ? (t('screenings.medium') || 'Medium') :
                                                         (t('screenings.routine') || 'Routine')}
                                                    </span>
                                                </div>
                                                {/* Last Done Status */}
                                                <div className="shrink-0">
                                                    {test.last_done_date ? (
                                                        <span className={cn(
                                                            "text-xs px-2 py-1 rounded-lg flex items-center gap-1",
                                                            test.is_overdue
                                                                ? "bg-amber-100 text-amber-700 border border-amber-200"
                                                                : "bg-teal-100 text-teal-700 border border-teal-200"
                                                        )}>
                                                            {test.is_overdue ? <AlertTriangle size={12} /> : <CheckCircle size={12} />}
                                                            {test.months_since_last === 0
                                                                ? (t('screenings.thisMonth') || 'This month')
                                                                : test.months_since_last === 1
                                                                    ? (t('screenings.oneMonthAgo') || '1 month ago')
                                                                    : `${test.months_since_last} ${t('screenings.monthsAgo') || 'months ago'}`
                                                            }
                                                        </span>
                                                    ) : (
                                                        <span className="text-xs px-2 py-1 rounded-lg bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1">
                                                            <AlertTriangle size={12} />
                                                            {t('screenings.neverDone') || 'Never done'}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="text-sm text-slate-600 mb-3">{test.reason}</p>
                                            <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                                                {test.frequency && (
                                                    <span className="flex items-center gap-1">
                                                        <Calendar size={12} />
                                                        {test.frequency}
                                                    </span>
                                                )}
                                                {test.age_recommendation && (
                                                    <span className="flex items-center gap-1">
                                                        <Clock size={12} />
                                                        {test.age_recommendation}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}

                    {/* Notes */}
                    {gapAnalysis.notes && (
                        <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
                            <strong>{t('common.note') || 'Note'}:</strong> {gapAnalysis.notes}
                        </div>
                    )}
                </>
            ) : (
                <div className="card p-12 text-center">
                    <div className="w-16 h-16 bg-violet-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <ClipboardList size={32} className="text-violet-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">
                        {t('screenings.noAnalysis') || 'No Recommendations Yet'}
                    </h3>
                    <p className="text-slate-500 mb-6 max-w-md mx-auto">
                        {t('screenings.noAnalysisHint') || 'Get personalized health screening recommendations based on your age, gender, and medical history.'}
                    </p>
                    <button
                        onClick={runGapAnalysis}
                        disabled={analyzing}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-violet-600 text-white rounded-xl font-semibold hover:bg-violet-700 transition-colors"
                    >
                        <Sparkles size={20} />
                        {t('screenings.getRecommendations') || 'Get Recommendations'}
                    </button>
                </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl text-sm text-slate-500">
                <Shield size={20} className="shrink-0 mt-0.5" />
                <p>
                    <strong>{t('common.disclaimer') || 'Disclaimer'}:</strong> {t('screenings.disclaimer') || 'These recommendations are generated by AI based on general health guidelines and your profile. They are not a substitute for professional medical advice. Always consult with your healthcare provider about appropriate screenings for your individual needs.'}
                </p>
            </div>
        </div>
    );
};

export default Screenings;
