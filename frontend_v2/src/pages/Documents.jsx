import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { FileText, Upload, Calendar, Building, CheckCircle, Clock, AlertCircle, Loader2, Download, Activity, Eye, Trash2, X, Brain } from 'lucide-react';
import { cn } from '../lib/utils';

const UPLOAD_STEPS = [
    { key: 'uploading', label: 'Uploading file...', duration: 500 },
    { key: 'reading', label: 'Reading PDF content...', duration: 1000 },
    { key: 'analyzing', label: 'AI analyzing biomarkers...', duration: 3000 },
    { key: 'extracting', label: 'Extracting test results...', duration: 2000 },
    { key: 'saving', label: 'Saving to database...', duration: 500 },
];

const Documents = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [uploadStep, setUploadStep] = useState(0);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(null); // doc to delete
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchDocuments();
    }, []);

    // Simulate upload progress steps
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
            setError("Failed to open PDF");
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
            setError("Failed to load documents. Please try again later.");
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
            setSuccess("Document uploaded and analyzed successfully! AI extracted biomarkers from your PDF.");
            fetchDocuments();
            setTimeout(() => setSuccess(null), 5000);
        } catch (error) {
            console.error("Upload failed", error);
            setError("Failed to upload document.");
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
            setSuccess("Document deleted. Health reports have been cleared - run a new analysis when ready.");
            setDeleteConfirm(null);
            fetchDocuments();
            setTimeout(() => setSuccess(null), 5000);
        } catch (error) {
            console.error("Delete failed", error);
            setError("Failed to delete document.");
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    {/* Mobile header compensation in Layout handles title, but we can add breadcrumbs here if needed */}
                </div>

                <div className="flex gap-3 w-full md:w-auto">
                    {/* Hidden Search Bar potential */}

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
                            {uploading ? 'Processing...' : 'Upload Report'}
                        </label>
                    </div>
                </div>
            </div>

            {/* Upload Progress */}
            {uploading && (
                <div className="mb-6 bg-primary-50 border border-primary-200 rounded-xl p-6">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 bg-primary-100 rounded-full">
                            <Brain size={24} className="text-primary-600 animate-pulse" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-primary-800">Processing Your Document</h3>
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
                    <div className="col-span-4 pl-2">Document Details</div>
                    <div className="col-span-2">Test Date</div>
                    <div className="col-span-2">Provider</div>
                    <div className="col-span-2">Status</div>
                    <div className="col-span-2 text-right pr-2">Actions</div>
                </div>

                {loading ? (
                    <div className="h-64 flex justify-center items-center text-slate-400">
                        <Loader2 className="animate-spin text-primary-500" size={32} />
                    </div>
                ) : documents.length === 0 ? (
                    <div className="h-64 flex flex-col items-center justify-center text-center p-8">
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 text-slate-400">
                            <FileText size={32} />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900">No documents yet</h3>
                        <p className="text-slate-500 mt-2 max-w-sm">
                            Upload your medical PDFs to get instant insights using our AI analysis.
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-50">
                        {documents.map((doc) => (
                            <div key={doc.id} className="grid grid-cols-12 gap-4 p-5 items-center hover:bg-slate-50/80 transition-all duration-200 group">
                                <div className="col-span-4 flex items-center gap-4 pl-2">
                                    <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center text-primary-600 shrink-0 border border-primary-100 shadow-sm">
                                        <FileText size={20} />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-semibold text-slate-900 truncate text-sm" title={doc.filename}>{doc.filename}</p>
                                        <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 font-mono">PDF</span>
                                    </div>
                                </div>

                                <div className="col-span-2 flex items-center gap-2 text-slate-600 text-sm">
                                    <Calendar size={14} className="text-slate-400 hidden sm:block" />
                                    {doc.document_date ? new Date(doc.document_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Unknown'}
                                </div>

                                <div className="col-span-2 flex items-center gap-2 text-slate-600 text-sm">
                                    <Building size={14} className="text-slate-400 hidden sm:block" />
                                    <span className="truncate">{doc.provider || 'Upload'}</span>
                                </div>

                                <div className="col-span-2">
                                    {doc.is_processed ? (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-100">
                                            <CheckCircle size={10} /> Done
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
                                            <Clock size={10} /> Pending
                                        </span>
                                    )}
                                </div>

                                <div className="col-span-2 flex items-center justify-end gap-1 pr-2">
                                    <button
                                        onClick={() => handleViewPdf(doc.id, doc.filename)}
                                        className="p-2 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                                        title="View PDF"
                                    >
                                        <Eye size={18} />
                                    </button>
                                    <Link
                                        to={`/biomarkers?doc=${doc.id}`}
                                        className="p-2 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                                        title="View Biomarkers"
                                    >
                                        <Activity size={18} />
                                    </Link>
                                    <button
                                        onClick={() => setDeleteConfirm(doc)}
                                        className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                        title="Delete Document"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            {deleteConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => !deleting && setDeleteConfirm(null)}>
                    <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-rose-100 rounded-full">
                                <Trash2 size={24} className="text-rose-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-800">Delete Document?</h3>
                                <p className="text-sm text-slate-500">This action cannot be undone</p>
                            </div>
                        </div>

                        <p className="text-slate-600 mb-2">
                            Are you sure you want to delete <strong>{deleteConfirm.filename}</strong>?
                        </p>
                        <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg mb-6">
                            This will also delete all extracted biomarkers from this document and clear your health reports.
                            You'll need to run a new AI analysis afterward.
                        </p>

                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setDeleteConfirm(null)}
                                disabled={deleting}
                                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors font-medium"
                            >
                                Cancel
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
                                        Deleting...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 size={16} />
                                        Delete Document
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
