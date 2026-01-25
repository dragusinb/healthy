import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
    Activity, Brain, Heart, Droplets, FlaskConical, Stethoscope,
    AlertTriangle, CheckCircle, Clock, ChevronRight, Loader2,
    RefreshCw, FileText, TrendingUp, Shield, ChevronDown, X, Eye,
    ClipboardList, Sparkles, Calendar
} from 'lucide-react';
import { cn } from '../lib/utils';

const SPECIALTY_ICONS = {
    cardiology: Heart,
    endocrinology: Activity,
    hematology: Droplets,
    hepatology: FlaskConical,
    nephrology: Stethoscope,
    general: Brain
};

const RISK_COLORS = {
    // General report statuses
    normal: { bg: 'bg-teal-50', text: 'text-teal-700', border: 'border-teal-200', icon: CheckCircle },
    attention: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: Clock },
    concern: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', icon: AlertTriangle },
    urgent: { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', icon: AlertTriangle },
    // Specialist report statuses
    high: { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', icon: AlertTriangle },
    low: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: AlertTriangle },
    'slightly high': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: Clock },
    'slightly low': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: Clock },
};

const ANALYSIS_STEPS = [
    { key: 'loading', label: 'Loading your biomarkers...', duration: 800 },
    { key: 'analyzing', label: 'Analyzing health data...', duration: 1500 },
    { key: 'general', label: 'Running general health assessment...', duration: 3000 },
    { key: 'cardiology', label: 'Consulting Cardiologist AI...', duration: 2500 },
    { key: 'endocrinology', label: 'Consulting Endocrinologist AI...', duration: 2500 },
    { key: 'hematology', label: 'Consulting Hematologist AI...', duration: 2500 },
    { key: 'hepatology', label: 'Consulting Hepatologist AI...', duration: 2500 },
    { key: 'nephrology', label: 'Consulting Nephrologist AI...', duration: 2500 },
    { key: 'compiling', label: 'Compiling final recommendations...', duration: 2000 },
    { key: 'finishing', label: 'Finalizing report...', duration: 1500 },
];

const openPdf = async (documentId) => {
    try {
        const token = localStorage.getItem('token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/documents/${documentId}/download`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch PDF');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
    } catch (e) {
        console.error('Failed to open PDF:', e);
    }
};

const HealthReports = () => {
    const { t } = useTranslation();
    const [latestReport, setLatestReport] = useState(null);
    const [reports, setReports] = useState([]);
    const [specialists, setSpecialists] = useState({});
    const [biomarkers, setBiomarkers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisStep, setAnalysisStep] = useState(0);
    const [error, setError] = useState(null);
    const [selectedReport, setSelectedReport] = useState(null);
    const [gapAnalysis, setGapAnalysis] = useState(null);
    const [gapLoading, setGapLoading] = useState(false);
    const [showGapSection, setShowGapSection] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    // Simulate progress steps during analysis
    useEffect(() => {
        if (!analyzing) {
            setAnalysisStep(0);
            return;
        }

        let currentStep = 0;
        const runSteps = () => {
            if (currentStep < ANALYSIS_STEPS.length) {
                setAnalysisStep(currentStep);
                const delay = ANALYSIS_STEPS[currentStep].duration;
                currentStep++;
                setTimeout(runSteps, delay);
            }
        };
        runSteps();
    }, [analyzing]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [latestRes, reportsRes, specialistsRes, biomarkersRes, gapRes] = await Promise.all([
                api.get('/health/latest'),
                api.get('/health/reports?limit=10'),
                api.get('/health/specialists'),
                api.get('/dashboard/biomarkers'),
                api.get('/health/gap-analysis/latest').catch(() => ({ data: { has_report: false } }))
            ]);
            setLatestReport(latestRes.data);
            setReports(reportsRes.data);
            setSpecialists(specialistsRes.data);
            setBiomarkers(biomarkersRes.data);

            // Load saved gap analysis if exists
            if (gapRes.data.has_report) {
                setGapAnalysis({
                    summary: gapRes.data.summary,
                    recommended_tests: gapRes.data.recommended_tests
                });
                setShowGapSection(true);
            }

            setError(null);
        } catch (e) {
            console.error("Failed to fetch health data", e);
            setError("Failed to load health reports");
        } finally {
            setLoading(false);
        }
    };

    // Find document_id for a biomarker by name (improved matching)
    const findDocumentForMarker = (markerName) => {
        if (!markerName || !biomarkers.length) return null;
        const name = markerName.toLowerCase().trim();

        // Normalize common variations
        const normalizedName = name
            .replace(/[-_]/g, ' ')
            .replace(/\s+/g, ' ')
            .replace(/hemoglobina/i, 'hemoglobin')
            .replace(/colesterol/i, 'cholesterol')
            .replace(/trigliceride/i, 'triglycerides')
            .replace(/glucoza/i, 'glucose')
            .replace(/creatinina/i, 'creatinine');

        // Try exact match first
        let match = biomarkers.find(b => b.name.toLowerCase().trim() === name);
        if (match) return match.document_id;

        // Try partial match
        match = biomarkers.find(b => {
            const bioName = b.name.toLowerCase().trim();
            return bioName.includes(name) || name.includes(bioName);
        });
        if (match) return match.document_id;

        // Try word-based match (any significant word matches)
        const words = normalizedName.split(' ').filter(w => w.length > 3);
        for (const word of words) {
            match = biomarkers.find(b => b.name.toLowerCase().includes(word));
            if (match) return match.document_id;
        }

        return null;
    };

    const runAnalysis = async () => {
        setAnalyzing(true);
        setError(null);
        try {
            await api.post('/health/analyze');
            await fetchData();
        } catch (e) {
            console.error("Analysis failed", e);
            setError(e.response?.data?.detail || "Analysis failed. Please try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    const runGapAnalysis = async () => {
        setGapLoading(true);
        setError(null);
        try {
            const res = await api.post('/health/gap-analysis');
            setGapAnalysis(res.data.analysis);
            setShowGapSection(true);
        } catch (e) {
            console.error("Gap analysis failed", e);
            setError(e.response?.data?.detail || "Gap analysis failed. Please try again.");
        } finally {
            setGapLoading(false);
        }
    };

    const getSpecialistReport = (specialtyKey) => {
        return reports.find(r => r.report_type === specialtyKey);
    };

    const getRiskStyle = (level) => RISK_COLORS[level] || RISK_COLORS.normal;

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
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                        <div className="p-2 bg-primary-100 text-primary-600 rounded-xl">
                            <Brain size={24} />
                        </div>
                        AI Health Analysis
                    </h1>
                    <p className="text-slate-500 mt-1">AI-powered insights from your biomarkers</p>
                </div>

                <button
                    onClick={runAnalysis}
                    disabled={analyzing}
                    className={cn(
                        "flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all shadow-md",
                        analyzing
                            ? "bg-primary-100 text-primary-600 cursor-wait"
                            : "bg-primary-600 text-white hover:bg-primary-700 shadow-primary-500/30"
                    )}
                >
                    {analyzing ? (
                        <>
                            <Loader2 className="animate-spin" size={20} />
                            {ANALYSIS_STEPS[analysisStep]?.label || 'Analyzing...'}
                        </>
                    ) : (
                        <>
                            <RefreshCw size={20} />
                            Run New Analysis
                        </>
                    )}
                </button>
            </div>

            {/* Analysis Progress */}
            {analyzing && (
                <div className="bg-primary-50 border border-primary-200 rounded-xl p-6">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-primary-100 rounded-full">
                            <Brain size={24} className="text-primary-600 animate-pulse" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-primary-800">AI Analysis in Progress</h3>
                            <p className="text-sm text-primary-600">{ANALYSIS_STEPS[analysisStep]?.label}</p>
                        </div>
                    </div>
                    <div className="space-y-2">
                        {ANALYSIS_STEPS.map((step, i) => (
                            <div key={step.key} className="flex items-center gap-3">
                                {i < analysisStep ? (
                                    <CheckCircle size={16} className="text-primary-600" />
                                ) : i === analysisStep ? (
                                    <Loader2 size={16} className="text-primary-600 animate-spin" />
                                ) : (
                                    <div className="w-4 h-4 rounded-full border-2 border-primary-300" />
                                )}
                                <span className={cn(
                                    "text-sm",
                                    i <= analysisStep ? "text-primary-700" : "text-primary-400"
                                )}>
                                    {step.label}
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

            {/* Latest Report Summary */}
            {!analyzing && latestReport?.has_report ? (
                <div className="card overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-slate-800">Latest Analysis</h2>
                            <span className="text-sm text-slate-400">
                                {new Date(latestReport.created_at).toLocaleDateString()}
                            </span>
                        </div>
                    </div>

                    <div className="p-6">
                        {/* Risk Level Badge */}
                        <div className="flex items-center gap-4 mb-6">
                            {(() => {
                                const style = getRiskStyle(latestReport.risk_level);
                                const Icon = style.icon;
                                return (
                                    <div className={cn(
                                        "flex items-center gap-2 px-4 py-2 rounded-full border",
                                        style.bg, style.text, style.border
                                    )}>
                                        <Icon size={18} />
                                        <span className="font-semibold capitalize">{latestReport.risk_level}</span>
                                    </div>
                                );
                            })()}
                            <span className="text-slate-500">
                                {latestReport.biomarkers_analyzed} biomarkers analyzed
                            </span>
                        </div>

                        {/* Summary */}
                        <p className="text-slate-700 text-lg leading-relaxed mb-6">
                            {latestReport.summary}
                        </p>

                        {/* Key Findings */}
                        {latestReport.findings?.length > 0 && (
                            <div className="mb-6">
                                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                                    Key Findings
                                </h3>
                                <div className="space-y-3">
                                    {latestReport.findings.map((finding, i) => {
                                        const style = getRiskStyle(finding.status);
                                        return (
                                            <div key={i} className={cn(
                                                "p-4 rounded-xl border",
                                                style.bg, style.border
                                            )}>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className={cn("font-semibold", style.text)}>
                                                        {finding.category}
                                                    </span>
                                                    <span className={cn(
                                                        "text-xs px-2 py-0.5 rounded-full",
                                                        style.bg, style.text, "border", style.border
                                                    )}>
                                                        {finding.status}
                                                    </span>
                                                </div>
                                                <p className="text-slate-600 text-sm">{finding.explanation}</p>
                                                {finding.markers?.length > 0 && (
                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        {finding.markers.map((marker, j) => {
                                                            const documentId = findDocumentForMarker(marker);
                                                            return (
                                                                <span key={j} className="inline-flex items-center gap-1 text-xs bg-white/50 px-2 py-1 rounded border border-slate-200">
                                                                    {marker}
                                                                    {documentId && (
                                                                        <button
                                                                            onClick={() => openPdf(documentId)}
                                                                            className="p-0.5 text-slate-400 hover:text-primary-600 rounded transition-colors"
                                                                            title="View source PDF"
                                                                        >
                                                                            <Eye size={12} />
                                                                        </button>
                                                                    )}
                                                                </span>
                                                            );
                                                        })}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Recommendations */}
                        {latestReport.recommendations?.length > 0 && (
                            <div>
                                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                                    Recommendations
                                </h3>
                                <div className="space-y-2">
                                    {latestReport.recommendations.map((rec, i) => (
                                        <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                                            <div className={cn(
                                                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                                                rec.priority === 'high' ? "bg-rose-100 text-rose-600" :
                                                rec.priority === 'medium' ? "bg-amber-100 text-amber-600" :
                                                "bg-slate-200 text-slate-600"
                                            )}>
                                                {i + 1}
                                            </div>
                                            <div>
                                                <p className="font-medium text-slate-800">{rec.action}</p>
                                                <p className="text-sm text-slate-500">{rec.reason}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            ) : !analyzing && (
                <div className="card p-12 text-center">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Brain size={32} className="text-slate-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-2">No Analysis Yet</h3>
                    <p className="text-slate-500 mb-6 max-w-md mx-auto">
                        Run your first AI health analysis to get personalized insights from your biomarkers.
                    </p>
                    <button
                        onClick={runAnalysis}
                        disabled={analyzing}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors"
                    >
                        <TrendingUp size={20} />
                        Run Analysis
                    </button>
                </div>
            )}

            {/* Available Specialists */}
            <div className="card overflow-hidden">
                <div className="p-6 border-b border-slate-100">
                    <h2 className="text-lg font-semibold text-slate-800">Specialist Analyses</h2>
                    <p className="text-sm text-slate-500 mt-1">Deep-dive analyses by medical specialty</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                    {Object.entries(specialists).map(([key, spec]) => {
                        const Icon = SPECIALTY_ICONS[key] || Stethoscope;
                        const report = getSpecialistReport(key);
                        const hasReport = !!report;

                        return (
                            <div
                                key={key}
                                className={cn(
                                    "group p-4 rounded-xl border transition-all",
                                    hasReport
                                        ? "border-teal-200 bg-teal-50/30 hover:bg-teal-50 cursor-pointer"
                                        : "border-slate-200 hover:border-slate-300"
                                )}
                                onClick={() => hasReport && setSelectedReport(report)}
                            >
                                <div className="flex items-start gap-4">
                                    <div className={cn(
                                        "p-3 rounded-xl transition-colors",
                                        hasReport ? "bg-teal-100" : "bg-slate-100 group-hover:bg-slate-200"
                                    )}>
                                        <Icon size={24} className={hasReport ? "text-teal-600" : "text-slate-600"} />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-slate-800">{spec.name}</h3>
                                        <p className="text-sm text-slate-500 mt-1">{spec.focus}</p>
                                        {hasReport ? (
                                            <button className="inline-flex items-center gap-1 text-xs text-teal-600 mt-2 font-medium hover:text-teal-700">
                                                <CheckCircle size={12} />
                                                View Report
                                                <ChevronRight size={12} />
                                            </button>
                                        ) : (
                                            <span className="inline-flex items-center gap-1 text-xs text-slate-400 mt-2">
                                                <Clock size={12} />
                                                No report yet
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Gap Analysis Section */}
            <div className="card overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-violet-100 rounded-lg">
                            <ClipboardList size={20} className="text-violet-600" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-slate-800">{t('healthReports.gapAnalysis.title') || 'Recommended Screenings'}</h2>
                            <p className="text-sm text-slate-500 mt-0.5">{t('healthReports.gapAnalysis.subtitle') || 'AI-recommended tests based on your age and medical history'}</p>
                        </div>
                    </div>
                    <button
                        onClick={runGapAnalysis}
                        disabled={gapLoading}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all text-sm",
                            gapLoading
                                ? "bg-violet-100 text-violet-600 cursor-wait"
                                : "bg-violet-600 text-white hover:bg-violet-700"
                        )}
                    >
                        {gapLoading ? (
                            <>
                                <Loader2 className="animate-spin" size={16} />
                                {t('common.loading') || 'Analyzing...'}
                            </>
                        ) : (
                            <>
                                <Sparkles size={16} />
                                {t('healthReports.gapAnalysis.getRecommendations') || 'Get Recommendations'}
                            </>
                        )}
                    </button>
                </div>

                {gapAnalysis ? (
                    <div className="p-6">
                        {/* Summary */}
                        {gapAnalysis.summary && (
                            <p className="text-slate-700 mb-6 leading-relaxed">{gapAnalysis.summary}</p>
                        )}

                        {/* Recommended Tests */}
                        {gapAnalysis.recommended_tests?.length > 0 && (
                            <div className="space-y-3">
                                {gapAnalysis.recommended_tests.map((test, i) => (
                                    <div key={i} className={cn(
                                        "p-4 rounded-xl border",
                                        test.priority === 'high' ? "bg-rose-50 border-rose-200" :
                                        test.priority === 'medium' ? "bg-amber-50 border-amber-200" :
                                        "bg-slate-50 border-slate-200"
                                    )}>
                                        <div className="flex items-start justify-between gap-3 mb-2">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-slate-800">{test.test_name}</span>
                                                <span className={cn(
                                                    "text-xs px-2 py-0.5 rounded-full font-medium",
                                                    test.priority === 'high' ? "bg-rose-100 text-rose-700" :
                                                    test.priority === 'medium' ? "bg-amber-100 text-amber-700" :
                                                    "bg-slate-200 text-slate-600"
                                                )}>
                                                    {test.priority === 'high' ? (t('healthReports.gapAnalysis.highPriority') || 'High Priority') :
                                                     test.priority === 'medium' ? (t('healthReports.gapAnalysis.mediumPriority') || 'Medium Priority') :
                                                     (t('healthReports.gapAnalysis.lowPriority') || 'Low Priority')}
                                                </span>
                                            </div>
                                            {test.category && (
                                                <span className="text-xs bg-white px-2 py-1 rounded border border-slate-200 text-slate-500">
                                                    {test.category}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-slate-600 mb-2">{test.reason}</p>
                                        <div className="flex items-center gap-4 text-xs text-slate-500">
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
                        )}

                        {/* Notes */}
                        {gapAnalysis.notes && (
                            <div className="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700">
                                <strong>{t('healthReports.gapAnalysis.note') || 'Note'}:</strong> {gapAnalysis.notes}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="p-8 text-center">
                        <div className="w-12 h-12 bg-violet-100 rounded-full flex items-center justify-center mx-auto mb-3">
                            <ClipboardList size={24} className="text-violet-400" />
                        </div>
                        <p className="text-slate-500 text-sm">
                            {t('healthReports.gapAnalysis.noAnalysisHint') || 'Click "Get Recommendations" to see which health screenings you might be missing based on your age and medical history.'}
                        </p>
                    </div>
                )}
            </div>

            {/* Report History */}
            {reports.length > 0 && (
                <div className="card overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                        <h2 className="text-lg font-semibold text-slate-800">Report History</h2>
                    </div>

                    <div className="divide-y divide-slate-50">
                        {reports.map((report) => {
                            const Icon = SPECIALTY_ICONS[report.report_type] || FileText;
                            const style = getRiskStyle(report.risk_level);

                            return (
                                <div
                                    key={report.id}
                                    className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                                    onClick={() => setSelectedReport(report)}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={cn("p-2 rounded-lg", style.bg)}>
                                            <Icon size={20} className={style.text} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-slate-800 truncate">{report.title}</p>
                                            <p className="text-sm text-slate-500 truncate">{report.summary}</p>
                                        </div>
                                        <div className="text-right shrink-0 flex items-center gap-3">
                                            <div>
                                                <span className={cn(
                                                    "text-xs px-2 py-1 rounded-full",
                                                    style.bg, style.text
                                                )}>
                                                    {report.risk_level}
                                                </span>
                                                <p className="text-xs text-slate-400 mt-1">
                                                    {new Date(report.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                            <ChevronRight size={18} className="text-slate-300" />
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Report Detail Modal */}
            {selectedReport && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedReport(null)}>
                    <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="sticky top-0 bg-white border-b border-slate-100 p-6 flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-slate-800">{selectedReport.title}</h2>
                                <p className="text-sm text-slate-500 mt-1">
                                    {new Date(selectedReport.created_at).toLocaleDateString()}
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedReport(null)}
                                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                <X size={20} className="text-slate-500" />
                            </button>
                        </div>

                        <div className="p-6">
                            {/* Risk Level */}
                            {(() => {
                                const style = getRiskStyle(selectedReport.risk_level);
                                const Icon = style.icon;
                                return (
                                    <div className={cn(
                                        "inline-flex items-center gap-2 px-4 py-2 rounded-full border mb-4",
                                        style.bg, style.text, style.border
                                    )}>
                                        <Icon size={18} />
                                        <span className="font-semibold capitalize">{selectedReport.risk_level}</span>
                                    </div>
                                );
                            })()}

                            {/* Summary */}
                            <p className="text-slate-700 leading-relaxed mb-6">
                                {selectedReport.summary}
                            </p>

                            {/* Findings */}
                            {selectedReport.findings?.length > 0 && (
                                <div className="mb-6">
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                                        Findings
                                    </h3>
                                    <div className="space-y-3">
                                        {selectedReport.findings.map((finding, i) => {
                                            const style = getRiskStyle(finding.status);
                                            // Handle both general report format (category/explanation) and specialist format (marker/significance)
                                            const title = finding.category || finding.marker;
                                            const description = finding.explanation || finding.significance;
                                            const value = finding.value;
                                            const refRange = finding.reference_range;
                                            const documentId = findDocumentForMarker(finding.marker);
                                            return (
                                                <div key={i} className={cn("p-4 rounded-xl border", style.bg, style.border)}>
                                                    <div className="flex items-center justify-between gap-2 mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <span className={cn("font-semibold", style.text)}>{title}</span>
                                                            {documentId && (
                                                                <button
                                                                    onClick={() => openPdf(documentId)}
                                                                    className="p-1 text-slate-400 hover:text-primary-600 hover:bg-white/50 rounded transition-colors"
                                                                    title="View source PDF"
                                                                >
                                                                    <Eye size={14} />
                                                                </button>
                                                            )}
                                                        </div>
                                                        <span className={cn("text-xs px-2 py-0.5 rounded-full border", style.bg, style.text, style.border)}>
                                                            {finding.status}
                                                        </span>
                                                    </div>
                                                    {value && (
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <p className="text-slate-800 font-medium text-sm">{value}</p>
                                                            {refRange && (
                                                                <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                                                                    Ref: {refRange}
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}
                                                    <p className="text-slate-600 text-sm">{description}</p>
                                                    {finding.markers?.length > 0 && (
                                                        <div className="flex flex-wrap gap-2 mt-2">
                                                            {finding.markers.map((marker, j) => {
                                                                const docId = findDocumentForMarker(marker);
                                                                return (
                                                                    <span key={j} className="inline-flex items-center gap-1 text-xs bg-white/50 px-2 py-1 rounded border border-slate-200">
                                                                        {marker}
                                                                        {docId && (
                                                                            <button
                                                                                onClick={() => openPdf(docId)}
                                                                                className="p-0.5 text-slate-400 hover:text-primary-600 rounded transition-colors"
                                                                                title="View source PDF"
                                                                            >
                                                                                <Eye size={12} />
                                                                            </button>
                                                                        )}
                                                                    </span>
                                                                );
                                                            })}
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Recommendations */}
                            {selectedReport.recommendations?.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
                                        Recommendations
                                    </h3>
                                    <div className="space-y-2">
                                        {selectedReport.recommendations.map((rec, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                                                <div className={cn(
                                                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                                                    rec.priority === 'high' ? "bg-rose-100 text-rose-600" :
                                                    rec.priority === 'medium' ? "bg-amber-100 text-amber-600" :
                                                    "bg-slate-200 text-slate-600"
                                                )}>
                                                    {i + 1}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-slate-800">{rec.action}</p>
                                                    <p className="text-sm text-slate-500">{rec.reason}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl text-sm text-slate-500">
                <Shield size={20} className="shrink-0 mt-0.5" />
                <p>
                    <strong>Disclaimer:</strong> This AI analysis is for informational purposes only and is not a substitute
                    for professional medical advice. Always consult with a qualified healthcare provider for medical decisions.
                </p>
            </div>
        </div>
    );
};

export default HealthReports;
