import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { FileText, Upload, Calendar, Building, CheckCircle, Clock, AlertCircle, Loader2, Download, Activity, Eye } from 'lucide-react';
import { cn } from '../lib/utils';

const Documents = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    useEffect(() => {
        fetchDocuments();
    }, []);

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
            setSuccess("Document uploaded successfully!");
            fetchDocuments();
            setTimeout(() => setSuccess(null), 3000);
        } catch (error) {
            console.error("Upload failed", error);
            setError("Failed to upload document.");
        } finally {
            setUploading(false);
            e.target.value = null;
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

                                <div className="col-span-2 flex items-center justify-end gap-2 pr-2">
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
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Documents;
