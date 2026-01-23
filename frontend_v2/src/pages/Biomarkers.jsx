import React, { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { Activity, Search, AlertTriangle, ArrowUp, ArrowDown, Calendar, X, FileText, ChevronDown, ChevronRight, Heart, Droplets, FlaskConical, Stethoscope, Pill, Dna, Loader2, ArrowUpDown, Eye } from 'lucide-react';
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

const CategorySection = ({ categoryKey, biomarkers, expanded, onToggle, t }) => {
    const category = CATEGORIES[categoryKey];
    const colors = COLOR_CLASSES[category.color];
    const Icon = category.icon;
    const issueCount = biomarkers.filter(b => b.status !== 'normal').length;

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
                        <p className="text-xs text-slate-500">{biomarkers.length} {t('biomarkers.tests')}</p>
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
                    <div className="grid grid-cols-12 gap-4 p-3 bg-slate-50/50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                        <div className="col-span-4 pl-2">{t('biomarkers.testName')}</div>
                        <div className="col-span-2">{t('biomarkers.value')}</div>
                        <div className="col-span-2">{t('biomarkers.refRange')}</div>
                        <div className="col-span-2">{t('biomarkers.date')}</div>
                        <div className="col-span-1 text-center">{t('biomarkers.pdf')}</div>
                        <div className="col-span-1 text-right pr-2">Status</div>
                    </div>
                    <div className="divide-y divide-slate-50">
                        {biomarkers.map((bio) => (
                            <div
                                key={bio.id}
                                className="grid grid-cols-12 gap-4 p-3 items-center hover:bg-slate-50/80 transition-all duration-200 group"
                            >
                                <Link
                                    to={`/evolution/${encodeURIComponent(bio.name)}`}
                                    className="col-span-4 font-medium text-slate-800 pl-2 group-hover:text-primary-600 transition-colors truncate"
                                >
                                    {bio.name}
                                </Link>
                                <div className="col-span-2 font-bold text-slate-800 flex items-baseline gap-1">
                                    {bio.value} <span className="text-slate-400 text-xs font-medium">{bio.unit}</span>
                                </div>
                                <div className="col-span-2 text-xs text-slate-500 font-medium">
                                    {bio.range}
                                </div>
                                <div className="col-span-2 text-xs text-slate-500">
                                    {new Date(bio.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' })}
                                </div>
                                <div className="col-span-1 text-center">
                                    {bio.document_id && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); openPdf(bio.document_id); }}
                                            className="inline-flex items-center justify-center p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                                            title={t('documents.viewPdf')}
                                        >
                                            <Eye size={14} />
                                        </button>
                                    )}
                                </div>
                                <div className="col-span-1 text-right pr-2">
                                    {bio.status === 'normal' ? (
                                        <span className="inline-block w-2 h-2 bg-teal-500 rounded-full" title={t('biomarkers.normal')} />
                                    ) : (
                                        <span className="inline-flex items-center text-rose-600" title={bio.status === 'high' ? t('biomarkers.high') : t('biomarkers.low')}>
                                            {bio.status === 'high' ? <ArrowUp size={14} strokeWidth={3} /> : <ArrowDown size={14} strokeWidth={3} />}
                                        </span>
                                    )}
                                </div>
                            </div>
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

    const [biomarkers, setBiomarkers] = useState([]);
    const [documentInfo, setDocumentInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState('all');
    const [sortBy, setSortBy] = useState('issues');
    const [expandedCategories, setExpandedCategories] = useState(new Set());

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
        try {
            const res = await api.get('/dashboard/biomarkers');
            setBiomarkers(res.data);
        } catch (e) {
            console.error("Failed to fetch biomarkers", e);
        } finally {
            setLoading(false);
        }
    };

    const fetchDocumentBiomarkers = async (id) => {
        setLoading(true);
        try {
            const res = await api.get(`/documents/${id}/biomarkers`);
            setBiomarkers(res.data.biomarkers);
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

    const expandAll = () => setExpandedCategories(new Set(Object.keys(CATEGORIES)));
    const collapseAll = () => setExpandedCategories(new Set());

    const groupedBiomarkers = useMemo(() => {
        const filtered = biomarkers.filter(b =>
            b.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
            (filter === 'all' || (filter === 'out_of_range' && b.status !== 'normal'))
        );

        const groups = {};
        for (const bio of filtered) {
            const cat = categorize(bio.name);
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(bio);
        }

        for (const cat in groups) {
            groups[cat].sort((a, b) => {
                if (sortBy === 'issues') {
                    const aIsIssue = a.status !== 'normal' ? 0 : 1;
                    const bIsIssue = b.status !== 'normal' ? 0 : 1;
                    if (aIsIssue !== bIsIssue) return aIsIssue - bIsIssue;
                }
                return new Date(b.date) - new Date(a.date);
            });
        }

        return groups;
    }, [biomarkers, searchTerm, filter, sortBy]);

    const totalFiltered = Object.values(groupedBiomarkers).flat().length;
    const totalIssues = Object.values(groupedBiomarkers).flat().filter(b => b.status !== 'normal').length;

    return (
        <div>
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
                        const catBiomarkers = groupedBiomarkers[key];
                        if (!catBiomarkers || catBiomarkers.length === 0) return null;

                        return (
                            <CategorySection
                                key={key}
                                categoryKey={key}
                                biomarkers={catBiomarkers}
                                expanded={expandedCategories.has(key)}
                                onToggle={() => toggleCategory(key)}
                                t={t}
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
