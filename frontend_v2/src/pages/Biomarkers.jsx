import React, { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Activity, Search, AlertTriangle, ArrowUp, ArrowDown, Calendar, X, FileText, ChevronDown, ChevronRight, Heart, Droplets, FlaskConical, Stethoscope, Pill, Dna, Loader2, ArrowUpDown, Eye, History, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../lib/utils';
import { Link } from 'react-router-dom';

// Biomarker category definitions
const CATEGORIES = {
    hematology: {
        nameKey: 'biomarkers.categories.hematology',
        icon: Droplets,
        color: 'rose',
        keywords: ['hemoglobin', 'hematocrit', 'rbc', 'wbc', 'platelets', 'mcv', 'mch', 'mchc', 'rdw', 'reticulocytes', 'leucocite', 'eritrocite', 'trombocite', 'hematies', 'vsh', 'esr', 'neutrofil', 'limfocit', 'monocit', 'eozinofil', 'bazofil', 'htc', 'hgb']
    },
    lipids: {
        nameKey: 'biomarkers.categories.lipids',
        icon: Heart,
        color: 'amber',
        keywords: ['cholesterol', 'colesterol', 'ldl', 'hdl', 'triglycerides', 'trigliceride', 'lipoprotein', 'apolipoprotein', 'lipid']
    },
    liver: {
        nameKey: 'biomarkers.categories.liver',
        icon: FlaskConical,
        color: 'emerald',
        keywords: ['alt', 'ast', 'alp', 'ggt', 'bilirubin', 'bilirubina', 'albumin', 'albumina', 'tgp', 'tgo', 'gama', 'hepat', 'ficat']
    },
    kidney: {
        nameKey: 'biomarkers.categories.kidney',
        icon: Stethoscope,
        color: 'blue',
        keywords: ['creatinin', 'creatinine', 'bun', 'urea', 'egfr', 'cystatin', 'uric', 'acid uric', 'rinichi', 'renal']
    },
    metabolic: {
        nameKey: 'biomarkers.categories.metabolic',
        icon: Activity,
        color: 'violet',
        keywords: ['glucose', 'glucoza', 'glicemie', 'hba1c', 'hemoglobina glicata', 'insulin', 'insulina', 'glyc']
    },
    thyroid: {
        nameKey: 'biomarkers.categories.thyroid',
        icon: Dna,
        color: 'cyan',
        keywords: ['tsh', 't3', 't4', 'ft3', 'ft4', 'tiroid', 'thyroid']
    },
    vitamins: {
        nameKey: 'biomarkers.categories.vitamins',
        icon: Pill,
        color: 'orange',
        keywords: ['vitamin', 'vitamina', 'fier', 'iron', 'ferritin', 'feritina', 'zinc', 'magneziu', 'magnesium', 'calciu', 'calcium', 'potasiu', 'potassium', 'sodiu', 'sodium', 'fosfor', 'b12', 'd3', 'folat', 'folic']
    },
    other: {
        nameKey: 'biomarkers.categories.other',
        icon: Activity,
        color: 'slate',
        keywords: []
    }
};

const COLOR_CLASSES = {
    rose: { bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-700', icon: 'text-rose-500' },
    amber: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: 'text-amber-500' },
    emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', icon: 'text-emerald-500' },
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'text-blue-500' },
    violet: { bg: 'bg-violet-50', border: 'border-violet-200', text: 'text-violet-700', icon: 'text-violet-500' },
    cyan: { bg: 'bg-cyan-50', border: 'border-cyan-200', text: 'text-cyan-700', icon: 'text-cyan-500' },
    orange: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', icon: 'text-orange-500' },
    slate: { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-700', icon: 'text-slate-500' },
};

function categorize(biomarkerName) {
    const name = biomarkerName.toLowerCase();
    for (const [key, cat] of Object.entries(CATEGORIES)) {
        if (key === 'other') continue;
        if (cat.keywords.some(kw => name.includes(kw))) {
            return key;
        }
    }
    return 'other';
}

const openPdf = async (documentId, e, errorMessage, vaultLockedMessage, onError) => {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    try {
        const token = localStorage.getItem('token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/documents/${documentId}/download`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) {
            // Check for specific error codes
            if (response.status === 503) {
                throw new Error('vault_locked');
            }
            throw new Error('Failed to fetch PDF');
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // For mobile Safari, use a different approach
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (isMobile) {
            // Create a temporary link and click it
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            window.open(url, '_blank');
        }
        // Revoke blob URL after a delay to prevent memory leak
        setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
        console.error('Failed to open PDF:', err);
        if (onError) {
            if (err.message === 'vault_locked') {
                onError(vaultLockedMessage || 'Your vault is locked. Please log out and log back in.');
            } else {
                onError(errorMessage || 'Could not open PDF. Please try again.');
            }
        }
    }
};

// Biomarker row with expandable history - Mobile responsive
const BiomarkerRow = ({ group, t, expandedHistory, onToggleHistory, showOnlyIssues, onPdfError }) => {
    const latest = group.latest;
    const historyCount = group.history.length;
    const isExpanded = expandedHistory.has(group.canonical_name);

    // If filtering for issues only and this specific biomarker is normal, skip it
    if (showOnlyIssues && latest.status === 'normal') {
        return null;
    }

    // Calculate trend from history
    const getTrend = () => {
        if (historyCount < 2) return null;
        const recent = group.history[0]?.value;
        const previous = group.history[1]?.value;
        if (typeof recent !== 'number' || typeof previous !== 'number') return null;
        if (recent > previous * 1.05) return 'up';
        if (recent < previous * 0.95) return 'down';
        return 'stable';
    };

    const trend = getTrend();

    return (
        <>
            {/* Desktop layout */}
            <div
                className={cn(
                    "hidden md:grid grid-cols-12 gap-4 p-3 items-center hover:bg-slate-50/80 transition-all duration-200 group",
                    isExpanded && "bg-slate-50/50"
                )}
            >
                <div className="col-span-4 pl-2 flex items-center gap-2">
                    {historyCount > 1 && (
                        <button
                            onClick={() => onToggleHistory(group.canonical_name)}
                            className="p-1 text-slate-400 hover:text-primary-600 hover:bg-primary-100 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
                            aria-label={isExpanded ? t('biomarkers.collapseHistory') : t('biomarkers.expandHistory')}
                            aria-expanded={isExpanded}
                        >
                            {isExpanded ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
                        </button>
                    )}
                    {historyCount <= 1 && <div className="w-6" />}
                    <Link
                        to={`/evolution/${encodeURIComponent(group.canonical_name)}`}
                        className="font-medium text-slate-800 group-hover:text-primary-600 transition-colors truncate"
                    >
                        {group.canonical_name}
                    </Link>
                    {historyCount > 1 && (
                        <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                            {historyCount}x
                        </span>
                    )}
                    {trend && (
                        <span className={cn(
                            "p-0.5 rounded",
                            trend === 'up' && "text-amber-500",
                            trend === 'down' && "text-blue-500",
                            trend === 'stable' && "text-slate-400"
                        )}>
                            {trend === 'up' && <TrendingUp size={12} />}
                            {trend === 'down' && <TrendingDown size={12} />}
                            {trend === 'stable' && <Minus size={12} />}
                        </span>
                    )}
                </div>
                <div className="col-span-2 font-bold text-slate-800 flex items-baseline gap-1">
                    {latest.value} <span className="text-slate-400 text-xs font-medium">{latest.unit}</span>
                </div>
                <div className="col-span-2 text-xs text-slate-500 font-medium">
                    {latest.range}
                </div>
                <div className="col-span-2 text-xs text-slate-500">
                    {new Date(latest.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' })}
                </div>
                <div className="col-span-1 text-center">
                    {latest.document_id && (
                        <button
                            onClick={(e) => openPdf(latest.document_id, e, t('documents.pdfOpenError'), t('documents.vaultLocked'), onPdfError)}
                            className="inline-flex items-center justify-center p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            aria-label={t('documents.viewPdf')}
                        >
                            <Eye size={14} aria-hidden="true" />
                        </button>
                    )}
                </div>
                <div className="col-span-1 text-right pr-2">
                    {latest.status === 'normal' ? (
                        <span className="inline-block w-2 h-2 bg-teal-500 rounded-full" role="img" aria-label={t('biomarkers.normal')} />
                    ) : (
                        <span className="inline-flex items-center text-rose-600" role="img" aria-label={latest.status === 'high' ? t('biomarkers.high') : t('biomarkers.low')}>
                            {latest.status === 'high' ? <ArrowUp size={14} strokeWidth={3} aria-hidden="true" /> : <ArrowDown size={14} strokeWidth={3} aria-hidden="true" />}
                        </span>
                    )}
                </div>
            </div>

            {/* Mobile layout - Card style */}
            <div
                className={cn(
                    "md:hidden p-3 hover:bg-slate-50/80 transition-all duration-200",
                    isExpanded && "bg-slate-50/50"
                )}
            >
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            {historyCount > 1 && (
                                <button
                                    onClick={() => onToggleHistory(group.canonical_name)}
                                    className="p-1 text-slate-400 hover:text-primary-600 hover:bg-primary-100 rounded transition-colors flex-shrink-0"
                                >
                                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                </button>
                            )}
                            <Link
                                to={`/evolution/${encodeURIComponent(group.canonical_name)}`}
                                className="font-medium text-slate-800 hover:text-primary-600 transition-colors truncate"
                            >
                                {group.canonical_name}
                            </Link>
                            {historyCount > 1 && (
                                <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded flex-shrink-0">
                                    {historyCount}x
                                </span>
                            )}
                            {trend && (
                                <span className={cn(
                                    "p-0.5 rounded flex-shrink-0",
                                    trend === 'up' && "text-amber-500",
                                    trend === 'down' && "text-blue-500",
                                    trend === 'stable' && "text-slate-400"
                                )}>
                                    {trend === 'up' && <TrendingUp size={12} />}
                                    {trend === 'down' && <TrendingDown size={12} />}
                                    {trend === 'stable' && <Minus size={12} />}
                                </span>
                            )}
                        </div>
                        <div className="flex items-baseline gap-2 flex-wrap">
                            <span className="font-bold text-slate-800">{latest.value}</span>
                            <span className="text-slate-400 text-xs">{latest.unit}</span>
                            <span className="text-slate-400" aria-hidden="true">•</span>
                            <span className="text-xs text-slate-500">{latest.range}</span>
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                            {new Date(latest.date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: '2-digit' })}
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {latest.document_id && (
                            <button
                                onClick={(e) => openPdf(latest.document_id, e, t('documents.pdfOpenError'), t('documents.vaultLocked'), onPdfError)}
                                className="p-2 text-primary-600 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
                                title={t('documents.viewPdf')}
                            >
                                <Eye size={16} />
                            </button>
                        )}
                        {latest.status === 'normal' ? (
                            <span className="inline-block w-3 h-3 bg-teal-500 rounded-full" title={t('biomarkers.normal')} />
                        ) : (
                            <span className="inline-flex items-center justify-center w-6 h-6 bg-rose-100 rounded-full text-rose-600" title={latest.status === 'high' ? t('biomarkers.high') : t('biomarkers.low')}>
                                {latest.status === 'high' ? <ArrowUp size={14} strokeWidth={3} /> : <ArrowDown size={14} strokeWidth={3} />}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Expanded history rows - Desktop */}
            {isExpanded && group.history.slice(1).map((bio, idx) => (
                <div
                    key={bio.id}
                    className={cn(
                        "hidden md:grid grid-cols-12 gap-4 p-2 pl-6 items-center bg-slate-50/30 border-l-2 border-slate-200 ml-4 text-sm",
                        showOnlyIssues && bio.status === 'normal' && "!hidden"
                    )}
                >
                    <div className="col-span-4 pl-8 text-slate-500 flex items-center gap-2">
                        <History size={12} className="text-slate-400" />
                        <span className="truncate text-xs">{bio.name !== group.canonical_name ? bio.name : ''}</span>
                    </div>
                    <div className="col-span-2 text-slate-700 flex items-baseline gap-1">
                        {bio.value} <span className="text-slate-400 text-xs">{bio.unit}</span>
                    </div>
                    <div className="col-span-2 text-xs text-slate-400">
                        {bio.range}
                    </div>
                    <div className="col-span-2 text-xs text-slate-400">
                        {new Date(bio.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' })}
                    </div>
                    <div className="col-span-1 text-center">
                        {bio.document_id && (
                            <button
                                onClick={(e) => openPdf(bio.document_id, e, t('documents.pdfOpenError'), t('documents.vaultLocked'), onPdfError)}
                                className="inline-flex items-center justify-center p-1 text-slate-400 hover:text-primary-600 rounded transition-colors"
                            >
                                <Eye size={12} />
                            </button>
                        )}
                    </div>
                    <div className="col-span-1 text-right pr-2">
                        {bio.status === 'normal' ? (
                            <span className="inline-block w-1.5 h-1.5 bg-teal-400 rounded-full" />
                        ) : (
                            <span className={cn("text-xs", bio.status === 'high' ? "text-rose-500" : "text-blue-500")}>
                                {bio.status === 'high' ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                            </span>
                        )}
                    </div>
                </div>
            ))}

            {/* Expanded history rows - Mobile */}
            {isExpanded && group.history.slice(1).map((bio, idx) => (
                <div
                    key={`mobile-${bio.id}`}
                    className={cn(
                        "md:hidden p-2 pl-6 bg-slate-50/30 border-l-2 border-slate-200 ml-3 text-sm",
                        showOnlyIssues && bio.status === 'normal' && "hidden"
                    )}
                >
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 text-slate-500 mb-1">
                                <History size={12} className="text-slate-400 flex-shrink-0" />
                                {bio.name !== group.canonical_name && (
                                    <span className="truncate text-xs">{bio.name}</span>
                                )}
                            </div>
                            <div className="flex items-baseline gap-2 flex-wrap">
                                <span className="font-medium text-slate-700">{bio.value}</span>
                                <span className="text-slate-400 text-xs">{bio.unit}</span>
                                <span className="text-slate-400" aria-hidden="true">•</span>
                                <span className="text-xs text-slate-400">{bio.range}</span>
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5">
                                {new Date(bio.date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: '2-digit' })}
                            </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                            {bio.document_id && (
                                <button
                                    onClick={(e) => openPdf(bio.document_id, e, t('documents.pdfOpenError'), t('documents.vaultLocked'), onPdfError)}
                                    className="p-1.5 text-slate-400 hover:text-primary-600 rounded transition-colors"
                                >
                                    <Eye size={14} />
                                </button>
                            )}
                            {bio.status === 'normal' ? (
                                <span className="inline-block w-2 h-2 bg-teal-400 rounded-full" />
                            ) : (
                                <span className={cn("text-xs", bio.status === 'high' ? "text-rose-500" : "text-blue-500")}>
                                    {bio.status === 'high' ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </>
    );
};

const CategorySection = ({ categoryKey, biomarkerGroups, expanded, onToggle, t, expandedHistory, onToggleHistory, showOnlyIssues, onPdfError }) => {
    const category = CATEGORIES[categoryKey];
    const colors = COLOR_CLASSES[category.color];
    const Icon = category.icon;
    const issueCount = biomarkerGroups.filter(g => g.latest?.status !== 'normal').length;

    // When filtering for issues, only count biomarkers with actual issues
    const visibleCount = showOnlyIssues ? issueCount : biomarkerGroups.length;

    return (
        <div className="card overflow-hidden">
            <button
                onClick={onToggle}
                className={cn(
                    "w-full p-4 flex items-center justify-between transition-colors",
                    expanded ? colors.bg : "hover:bg-slate-50"
                )}
            >
                <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg", colors.bg, colors.border, "border")}>
                        <Icon size={20} className={colors.icon} />
                    </div>
                    <div className="text-left">
                        <h3 className="font-semibold text-slate-800">{t(category.nameKey)}</h3>
                        <p className="text-xs text-slate-500">{visibleCount} {t('biomarkers.tests')}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {issueCount > 0 && (
                        <span className="px-2 py-1 bg-rose-100 text-rose-700 text-xs font-bold rounded-full">
                            {issueCount} {issueCount > 1 ? t('biomarkers.issuesCount') : t('biomarkers.issue')}
                        </span>
                    )}
                    {expanded ? <ChevronDown size={20} className="text-slate-400" /> : <ChevronRight size={20} className="text-slate-400" />}
                </div>
            </button>

            {expanded && (
                <div className="border-t border-slate-100">
                    {/* Desktop header */}
                    <div className="hidden md:grid grid-cols-12 gap-4 p-3 bg-slate-50/50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                        <div className="col-span-4 pl-2">{t('biomarkers.testName')}</div>
                        <div className="col-span-2">{t('biomarkers.value')}</div>
                        <div className="col-span-2">{t('biomarkers.refRange')}</div>
                        <div className="col-span-2">{t('biomarkers.date')}</div>
                        <div className="col-span-1 text-center">PDF</div>
                        <div className="col-span-1 text-right pr-2">Status</div>
                    </div>
                    {/* Mobile header */}
                    <div className="md:hidden p-3 bg-slate-50/50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                        {t('biomarkers.testResults')}
                    </div>
                    <div className="divide-y divide-slate-100 md:divide-slate-50">
                        {biomarkerGroups.map((group) => (
                            <BiomarkerRow
                                key={group.canonical_name}
                                group={group}
                                t={t}
                                expandedHistory={expandedHistory}
                                onToggleHistory={onToggleHistory}
                                showOnlyIssues={showOnlyIssues}
                                onPdfError={onPdfError}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const Biomarkers = () => {
    const { t } = useTranslation();
    const [searchParams, setSearchParams] = useSearchParams();
    const docId = searchParams.get('doc');

    const [biomarkerGroups, setBiomarkerGroups] = useState([]);
    const [documentBiomarkers, setDocumentBiomarkers] = useState([]);
    const [documentInfo, setDocumentInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [pdfError, setPdfError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState('all');
    const [sortBy, setSortBy] = useState('issues');
    const [expandedCategories, setExpandedCategories] = useState(new Set());
    const [expandedHistory, setExpandedHistory] = useState(new Set());

    useEffect(() => {
        if (docId) {
            fetchDocumentBiomarkers(docId);
        } else {
            fetchBiomarkers();
        }
    }, [docId]);

    const fetchBiomarkers = async () => {
        setLoading(true);
        setDocumentInfo(null);
        setError('');
        try {
            const res = await api.get('/dashboard/biomarkers-grouped');
            setBiomarkerGroups(res.data);
        } catch (e) {
            console.error("Failed to fetch biomarkers", e);
            if (e.response?.status === 503) {
                setError(t('documents.vaultLocked'));
            } else {
                setError(t('common.error'));
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchDocumentBiomarkers = async (id) => {
        setLoading(true);
        try {
            const res = await api.get(`/documents/${id}/biomarkers`);
            // Convert document biomarkers to grouped format
            const groups = {};
            for (const bio of res.data.biomarkers) {
                const name = bio.name;
                if (!groups[name]) {
                    groups[name] = {
                        canonical_name: name,
                        latest: null,
                        history: [],
                        has_issues: false
                    };
                }
                groups[name].history.push({
                    ...bio,
                    date: res.data.document.date || 'Unknown'
                });
                if (bio.status !== 'normal') groups[name].has_issues = true;
                if (!groups[name].latest) {
                    groups[name].latest = { ...bio, date: res.data.document.date || 'Unknown' };
                }
            }
            setBiomarkerGroups(Object.values(groups));
            setDocumentInfo(res.data.document);
        } catch (e) {
            console.error("Failed to fetch document biomarkers", e);
        } finally {
            setLoading(false);
        }
    };

    const clearDocumentFilter = () => {
        setSearchParams({});
    };

    const toggleCategory = (key) => {
        setExpandedCategories(prev => {
            const next = new Set(prev);
            if (next.has(key)) {
                next.delete(key);
            } else {
                next.add(key);
            }
            return next;
        });
    };

    const toggleHistory = (canonicalName) => {
        setExpandedHistory(prev => {
            const next = new Set(prev);
            if (next.has(canonicalName)) {
                next.delete(canonicalName);
            } else {
                next.add(canonicalName);
            }
            return next;
        });
    };

    const expandAll = () => setExpandedCategories(new Set(Object.keys(CATEGORIES)));
    const collapseAll = () => setExpandedCategories(new Set());

    const groupedByCategory = useMemo(() => {
        // Filter groups based on search and filter
        const filtered = biomarkerGroups.filter(g => {
            const matchesSearch = g.canonical_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                g.history.some(h => h.name?.toLowerCase().includes(searchTerm.toLowerCase()));
            const matchesFilter = filter === 'all' || (filter === 'out_of_range' && g.has_issues);
            return matchesSearch && matchesFilter;
        });

        // Group by category
        const categories = {};
        for (const group of filtered) {
            const cat = categorize(group.canonical_name);
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push(group);
        }

        // Sort each category
        for (const cat in categories) {
            categories[cat].sort((a, b) => {
                if (sortBy === 'issues') {
                    const aIsIssue = a.has_issues ? 0 : 1;
                    const bIsIssue = b.has_issues ? 0 : 1;
                    if (aIsIssue !== bIsIssue) return aIsIssue - bIsIssue;
                }
                return (b.latest_date || '').localeCompare(a.latest_date || '');
            });
        }

        return categories;
    }, [biomarkerGroups, searchTerm, filter, sortBy]);

    const totalFiltered = Object.values(groupedByCategory).flat().length;
    const totalIssues = Object.values(groupedByCategory).flat().filter(g => g.has_issues).length;

    return (
        <div>
            {/* Error Banner */}
            {(error || pdfError) && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <AlertTriangle size={20} className="text-red-500" />
                        <p className="text-red-700 font-medium">{error || pdfError}</p>
                    </div>
                    <button
                        onClick={() => { setError(''); setPdfError(''); }}
                        className="p-1 text-red-500 hover:bg-red-100 rounded-lg"
                    >
                        <X size={16} />
                    </button>
                </div>
            )}

            {/* Document Filter Banner */}
            {documentInfo && (
                <div className="mb-6 p-4 bg-primary-50 border border-primary-100 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <FileText size={20} className="text-primary-600" />
                        <div>
                            <p className="text-sm font-medium text-primary-900">
                                {t('biomarkers.showingFrom')}: <span className="font-bold">{documentInfo.filename}</span>
                            </p>
                            <p className="text-xs text-primary-600">
                                {documentInfo.provider} • {documentInfo.date ? new Date(documentInfo.date).toLocaleDateString() : t('documents.unknown')}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={clearDocumentFilter}
                        className="p-2 text-primary-600 hover:bg-primary-100 rounded-lg transition-colors"
                        title={t('common.all')}
                    >
                        <X size={18} />
                    </button>
                </div>
            )}

            {/* Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:flex-none group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-500 transition-colors" size={18} />
                        <input
                            type="text"
                            placeholder={t('biomarkers.searchTests')}
                            className="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all w-full md:w-80 shadow-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200/50">
                        <button
                            onClick={() => setFilter('all')}
                            className={cn(
                                "px-4 py-2 text-sm font-medium rounded-lg transition-all",
                                filter === 'all' ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                            )}
                        >
                            {t('common.all')}
                        </button>
                        <button
                            onClick={() => setFilter('out_of_range')}
                            className={cn(
                                "px-4 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-1.5",
                                filter === 'out_of_range' ? "bg-white text-rose-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
                            )}
                        >
                            <AlertTriangle size={14} />
                            {t('biomarkers.issues')}
                        </button>
                    </div>
                    <div className="flex items-center gap-2">
                        <ArrowUpDown size={14} className="text-slate-400" />
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 shadow-sm"
                        >
                            <option value="issues">{t('biomarkers.issuesFirst')}</option>
                            <option value="recent">{t('biomarkers.mostRecent')}</option>
                        </select>
                    </div>
                </div>
                <div className="flex gap-2 text-sm">
                    <button onClick={expandAll} className="text-primary-600 hover:text-primary-700 font-medium">{t('biomarkers.expandAll')}</button>
                    <span className="text-slate-300">|</span>
                    <button onClick={collapseAll} className="text-primary-600 hover:text-primary-700 font-medium">{t('biomarkers.collapseAll')}</button>
                </div>
            </div>

            {/* Summary */}
            <div className="mb-6 flex items-center gap-4 text-sm text-slate-600">
                <span><strong>{totalFiltered}</strong> {t('biomarkers.biomarkersCount')}</span>
                {totalIssues > 0 && (
                    <span className="text-rose-600"><strong>{totalIssues}</strong> {t('biomarkers.outOfRange')}</span>
                )}
            </div>

            {/* Loading */}
            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="animate-spin text-primary-500" size={32} />
                </div>
            ) : (
                /* Category Sections */
                <div className="space-y-4">
                    {Object.entries(CATEGORIES).map(([key]) => {
                        const catGroups = groupedByCategory[key];
                        if (!catGroups || catGroups.length === 0) return null;

                        return (
                            <CategorySection
                                key={key}
                                categoryKey={key}
                                biomarkerGroups={catGroups}
                                expanded={expandedCategories.has(key)}
                                onToggle={() => toggleCategory(key)}
                                t={t}
                                expandedHistory={expandedHistory}
                                onToggleHistory={toggleHistory}
                                showOnlyIssues={filter === 'out_of_range'}
                                onPdfError={setPdfError}
                            />
                        );
                    })}

                    {totalFiltered === 0 && (
                        <div className="card p-12 text-center">
                            <Activity size={40} className="mx-auto mb-3 text-slate-300" />
                            <p className="text-lg font-medium text-slate-600">{t('biomarkers.noBiomarkers')}</p>
                            <p className="text-sm text-slate-400 mt-1">{t('biomarkers.adjustFilters')}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Biomarkers;
