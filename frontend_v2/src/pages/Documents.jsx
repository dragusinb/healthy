import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { FileText, Upload, Calendar, Building, CheckCircle, Clock, AlertCircle, Loader2, Download, Activity, Eye, Trash2, X, Brain, User, RefreshCw } from 'lucide-react';
import { cn } from '../lib/utils';

const Documents = () => {
    const { t } = useTranslation();
    const [documents, setDocuments] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [uploadStep, setUploadStep] = useState(0);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const [patientFilter, setPatientFilter] = useState('all');
    const [rescanning, setRescanning] = useState(false);

    // Get unique patients for filter (group by CNP prefix only)
    const patients = useMemo(() => {
        const patientMap = new Map(); // key: cnp_prefix, value: { id, displayName }

        documents.forEach(doc => {
            // Only group by CNP prefix - this is the unique patient identifier
            if (!doc.patient_cnp_prefix) return;

            if (!patientMap.has(doc.patient_cnp_prefix)) {
                patientMap.set(doc.patient_cnp_prefix, {
                    id: doc.patient_cnp_prefix,
                    displayName: doc.patient_name || 'Unknown'
                });
            }
        });

        return Array.from(patientMap.values()).sort((a, b) =>
            a.displayName.localeCompare(b.displayName)
        );
    }, [documents]);

    // Filter documents by patient (using CNP prefix)
    const filteredDocuments = useMemo(() => {
        if (patientFilter === 'all') return documents;
        return documents.filter(doc => doc.patient_cnp_prefix === patientFilter);
    }, [documents, patientFilter]);

    const UPLOAD_STEPS = [
        { key: 'uploading', label: t('documents.uploadSteps.uploading'), duration: 500 },
        { key: 'reading', label: t('documents.uploadSteps.reading'), duration: 1000 },
        { key: 'analyzing', label: t('documents.uploadSteps.analyzing'), duration: 3000 },
        { key: 'extracting', label: t('documents.uploadSteps.extracting'), duration: 2000 },
        { key: 'saving', label: t('documents.uploadSteps.saving'), duration: 500 },
    ];

    useEffect(() => {
        fetchDocuments();
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const res = await api.get('/documents/stats');
            setStats(res.data);
        } catch (e) {
            console.error("Failed to fetch stats", e);
        }
    };

    useEffect(() => {
        if (!uploading) {
            setUploadStep(0);
            return;
        }

        let currentStep = 0;
        const runSteps = () => {
            if (currentStep < UPLOAD_STEPS.length && uploading) {
                setUploadStep(currentStep);
                const delay = UPLOAD_STEPS[currentStep].duration;
                currentStep++;
                setTimeout(runSteps, delay);
            }
        };
        runSteps();
    }, [uploading]);

    const handleViewPdf = async (docId, filename) => {
        try {
            const response = await api.get(`/documents/${docId}/download`, {
                responseType: 'blob'
            });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (e) {
            console.error("Failed to download PDF", e);
            // Check for vault locked (503) error
            if (e.response?.status === 503) {
                setError(t('documents.vaultLocked'));
            } else if (e.response?.data?.detail) {
                setError(e.response.data.detail);
            } else {
                setError(t('common.error'));
            }
        }
    };

    const fetchDocuments = async () => {
        setLoading(true);
        try {
            const res = await api.get('/documents/');
            setDocuments(res.data);
            setError(null);
        } catch (e) {
            console.error("Failed to fetch documents", e);
            setError(t('common.error'));
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post('/documents/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setSuccess(t('documents.uploadSuccess'));
            fetchDocuments();
            fetchStats();
            setTimeout(() => setSuccess(null), 5000);
        } catch (error) {
            console.error("Upload failed", error);
            setError(t('common.error'));
        } finally {
            setUploading(false);
            e.target.value = null;
        }
    };

    const handleDelete = async (doc) => {
        setDeleting(true);
        setError(null);
        try {
            await api.delete(`/documents/${doc.id}?regenerate_reports=true`);
            setSuccess(t('documents.deleteSuccess'));
            setDeleteConfirm(null);
            fetchDocuments();
            fetchStats();
            setTimeout(() => setSuccess(null), 5000);
        } catch (error) {
            console.error("Delete failed", error);
            setError(t('common.error'));
        } finally {
            setDeleting(false);
        }
    };

    const handleRescanPatientNames = async () => {
        setRescanning(true);
        setError(null);
        try {
            const res = await api.post('/documents/rescan-patient-names');
            if (res.data.updated > 0) {
                setSuccess(t('documents.rescanSuccess', { count: res.data.updated }));
                fetchDocuments();
            } else {
                setSuccess(t('documents.rescanNoUpdates'));
            }
            setTimeout(() => setSuccess(null), 5000);
        } catch (error) {
            console.error("Rescan failed", error);
            setError(t('common.error'));
        } finally {
            setRescanning(false);
        }
    };

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                {/* Patient Filter */}
                <div className="flex items-center gap-3">
                    {patients.length > 1 && (
                        <div className="flex items-center gap-2">
                            <User size={16} className="text-slate-400" />
                            <select
                                value={patientFilter}
                                onChange={(e) => setPatientFilter(e.target.value)}
                                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                            >
                                <option value="all">{t('documents.allPatients') || 'All Patients'}</option>
                                {patients.map(patient => (
                                    <option key={patient.id} value={patient.id}>{patient.displayName}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
                <div className="flex gap-3 w-full md:w-auto">
                    {/* Rescan button - only show if there are docs without patient names */}
                    {documents.some(d => !d.patient_name) && (
                        <button
                            onClick={handleRescanPatientNames}
                            disabled={rescanning}
                            className={cn(
                                "flex items-center gap-2 px-4 py-3 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200 transition-all border border-slate-200",
                                rescanning && "opacity-70 cursor-not-allowed"
                            )}
                            title={t('documents.rescanTooltip')}
                        >
                            {rescanning ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
                            <span className="hidden sm:inline">{rescanning ? t('documents.rescanning') : t('documents.rescanPatients')}</span>
                        </button>
                    )}
                    <div className="relative group">
                        <input
                            type="file"
                            id="file-upload"
                            className="hidden"
                            accept=".pdf"
                            onChange={handleUpload}
                            disabled={uploading}
                        />
                        <label
                            htmlFor="file-upload"
                            className={cn(
                                "flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium cursor-pointer hover:bg-primary-700 hover:shadow-lg transition-all shadow-md shadow-primary-500/30 active:scale-95 select-none",
                                uploading && "opacity-70 cursor-not-allowed"
                            )}
                        >
                            {uploading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
                            {uploading ? t('documents.processing') : t('documents.uploadReport')}
                        </label>
                    </div>
                </div>
            </div>

            {/* Stats Summary */}
            {stats && (
                <div className="mb-6 bg-gradient-to-r from-slate-50 to-slate-100 border border-slate-200 rounded-xl p-5">
                    <div className="flex flex-wrap items-center gap-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary-100 rounded-lg">
                                <FileText size={20} className="text-primary-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">{stats.total_documents}</p>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">{t('documents.totalDocuments') || 'Documents'}</p>
                            </div>
                        </div>
                        <div className="h-10 w-px bg-slate-200 hidden sm:block" />
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-teal-100 rounded-lg">
                                <Activity size={20} className="text-teal-600" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-slate-800">{stats.total_biomarkers}</p>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">{t('documents.totalBiomarkers') || 'Biomarkers'}</p>
                            </div>
                        </div>
                        {Object.keys(stats.by_provider || {}).length > 0 && (
                            <>
                                <div className="h-10 w-px bg-slate-200 hidden sm:block" />
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(stats.by_provider).map(([provider, count]) => (
                                        <span
                                            key={provider}
                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm shadow-sm"
                                        >
                                            <Building size={14} className="text-slate-400" />
                                            <span className="font-medium text-slate-700">{provider}</span>
                                            <span className="text-slate-400">·</span>
                                            <span className="font-bold text-primary-600">{count}</span>
                                        </span>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Upload Progress */}
            {uploading && (
                <div className="mb-6 bg-primary-50 border border-primary-200 rounded-xl p-6">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-primary-100 rounded-full">
                            <Brain size={24} className="text-primary-600 animate-pulse" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-primary-800">{t('documents.processingYourDocument')}</h3>
                            <p className="text-sm text-primary-600">{UPLOAD_STEPS[uploadStep]?.label}</p>
                        </div>
                    </div>
                    <div className="space-y-2">
                        {UPLOAD_STEPS.map((step, i) => (
                            <div key={step.key} className="flex items-center gap-3">
                                {i < uploadStep ? (
                                    <CheckCircle size={16} className="text-primary-600" />
                                ) : i === uploadStep ? (
                                    <Loader2 size={16} className="text-primary-600 animate-spin" />
                                ) : (
                                    <div className="w-4 h-4 rounded-full border-2 border-primary-300" />
                                )}
                                <span className={cn(
                                    "text-sm",
                                    i <= uploadStep ? "text-primary-700" : "text-primary-400"
                                )}>
                                    {step.label}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {error && (
                <div className="mb-6 p-4 bg-rose-50 border border-rose-100 text-rose-700 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                    <AlertCircle size={20} />
                    {error}
                </div>
            )}

            {success && (
                <div className="mb-6 p-4 bg-teal-50 border border-teal-100 text-teal-700 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                    <CheckCircle size={20} />
                    {success}
                </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden min-h-[400px]">
                {/* Table Header */}
                <div className="grid grid-cols-12 gap-4 p-5 border-b border-slate-100 bg-slate-50/50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="col-span-4 pl-2">{t('documents.documentDetails')}</div>
                    <div className="col-span-2">{t('documents.testDate')}</div>
                    <div className="col-span-2">{t('documents.provider')}</div>
                    <div className="col-span-2">{t('documents.status')}</div>
                    <div className="col-span-2 text-right pr-2">{t('documents.actions')}</div>
                </div>

                {loading ? (
                    <div className="h-64 flex justify-center items-center text-slate-400">
                        <Loader2 className="animate-spin text-primary-500" size={32} />
                    </div>
                ) : filteredDocuments.length === 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center text-center p-8">
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 text-slate-400">
                            <FileText size={32} />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900">{t('documents.noDocuments')}</h3>
                        <p className="text-slate-500 mt-2 max-w-sm">
                            {t('documents.uploadHint')}
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-50">
                        {filteredDocuments.map((doc) => (
                            <div key={doc.id} className="grid grid-cols-12 gap-4 p-5 items-center hover:bg-slate-50/80 transition-all duration-200 group">
                                <div className="col-span-4 flex items-center gap-4 pl-2">
                                    <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center text-primary-600 shrink-0 border border-primary-100 shadow-sm">
                                        <FileText size={20} />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-semibold text-slate-900 truncate text-sm" title={doc.filename}>{doc.filename}</p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 font-mono">PDF</span>
                                            {doc.patient_name && (
                                                <span className="text-xs text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100 flex items-center gap-1">
                                                    <User size={10} />
                                                    {doc.patient_name}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="col-span-2 flex items-center gap-2 text-slate-600 text-sm">
                                    <Calendar size={14} className="text-slate-400 hidden sm:block" />
                                    {doc.document_date ? new Date(doc.document_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : t('documents.unknown')}
                                </div>

                                <div className="col-span-2 flex items-center gap-2 text-slate-600 text-sm">
                                    <Building size={14} className="text-slate-400 hidden sm:block" />
                                    <span className="truncate">{doc.provider || 'Upload'}</span>
                                </div>

                                <div className="col-span-2">
                                    {doc.is_processed ? (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-100">
                                            <CheckCircle size={10} /> {t('documents.processed')}
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
                                            <Clock size={10} /> {t('documents.pending')}
                                        </span>
                                    )}
                                </div>

                                <div className="col-span-2 flex items-center justify-end gap-1 pr-2">
                                    <button
                                        onClick={() => handleViewPdf(doc.id, doc.filename)}
                                        className="p-2 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                                        title={t('documents.viewPdf')}
                                        aria-label={t('documents.viewPdf')}
                                    >
                                        <Eye size={18} aria-hidden="true" />
                                    </button>
                                    <Link
                                        to={`/biomarkers?doc=${doc.id}`}
                                        className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                                        title={t('documents.viewBiomarkers')}
                                        aria-label={t('documents.viewBiomarkers')}
                                    >
                                        <Activity size={18} aria-hidden="true" />
                                    </Link>
                                    <button
                                        onClick={() => setDeleteConfirm(doc)}
                                        className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                        title={t('documents.deleteDocument')}
                                        aria-label={t('documents.deleteDocument')}
                                    >
                                        <Trash2 size={18} aria-hidden="true" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            {deleteConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true" aria-labelledby="delete-modal-title" onClick={() => !deleting && setDeleteConfirm(null)}>
                    <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-rose-100 rounded-full">
                                <Trash2 size={24} className="text-rose-600" aria-hidden="true" />
                            </div>
                            <div>
                                <h3 id="delete-modal-title" className="text-lg font-bold text-slate-800">{t('documents.deleteConfirmTitle')}</h3>
                                <p className="text-sm text-slate-500">{t('documents.deleteConfirmText')}</p>
                            </div>
                        </div>

                        <p className="text-slate-600 mb-2">
                            {t('common.confirm')} <strong>{deleteConfirm.filename}</strong>?
                        </p>
                        <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg mb-6">
                            {t('documents.deleteWarning')}
                        </p>

                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setDeleteConfirm(null)}
                                disabled={deleting}
                                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors font-medium"
                            >
                                {t('common.cancel')}
                            </button>
                            <button
                                onClick={() => handleDelete(deleteConfirm)}
                                disabled={deleting}
                                className={cn(
                                    "px-4 py-2 bg-rose-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2",
                                    deleting ? "opacity-70 cursor-wait" : "hover:bg-rose-700"
                                )}
                            >
                                {deleting ? (
                                    <>
                                        <Loader2 size={16} className="animate-spin" />
                                        {t('documents.deleting')}
                                    </>
                                ) : (
                                    <>
                                        <Trash2 size={16} />
                                        {t('documents.deleteDocument')}
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Documents;
