import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, FileText, Activity, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';

export default function DocumentDetails({ documentId, onClose }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/documents/${documentId}`);
                setData(response.data);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch document details:", err);
                setError("Failed to load document details.");
                setLoading(false);
            }
        };

        if (documentId) {
            fetchDetails();
        }
    }, [documentId]);

    if (!documentId) return null;

    return (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
                            <FileText size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-slate-800">
                                {loading ? 'Loading...' : data?.filename || 'Document Details'}
                            </h2>
                            <p className="text-sm text-slate-500">
                                {data?.date ? new Date(data.date).toLocaleDateString() : 'Unknown Date'} • {data?.provider || 'Unknown Provider'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="overflow-y-auto p-6 flex-1">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-400 animate-pulse">
                            <Activity size={48} className="mb-4 opacity-50" />
                            <p>Analyzing biomarkers...</p>
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center h-64 text-red-500">
                            <AlertCircle size={48} className="mb-4" />
                            <p>{error}</p>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            <BiomarkerGroups results={data.results} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

const getFlagStyle = (flag) => {
    switch (flag) {
        case 'HIGH': return 'bg-red-50 text-red-700 font-bold border border-red-100 px-2 py-1 rounded-md inline-block';
        case 'LOW': return 'bg-yellow-50 text-yellow-700 font-bold border border-yellow-100 px-2 py-1 rounded-md inline-block';
        case 'NORMAL': return 'text-teal-700 font-semibold';
        default: return 'text-slate-900 font-semibold';
    }
};

function BiomarkerGroups({ results }) {
    if (!results || results.length === 0) {
        return (
            <div className="text-center py-12 text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                <p>No biomarkers found in this document.</p>
            </div>
        );
    }

    // Group by category
    const groups = results.reduce((acc, curr) => {
        const cat = curr.category || 'General';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(curr);
        return acc;
    }, {});

    return (
        <div className="space-y-8">
            {Object.entries(groups).map(([category, items]) => (
                <div key={category} className="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm">
                    <div className="px-6 py-3 bg-slate-50 border-b border-gray-100 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-teal-500"></div>
                        <h3 className="font-semibold text-slate-700 uppercase tracking-wide text-sm">
                            {category}
                        </h3>
                        <span className="text-xs text-slate-400 ml-auto font-mono">
                            {items.length} Tests
                        </span>
                    </div>
                    <table className="w-full text-sm text-left">
                        <thead className="bg-white text-slate-500 border-b border-gray-50">
                            <tr>
                                <th className="px-6 py-3 font-medium w-1/3">Test Name</th>
                                <th className="px-6 py-3 font-medium w-1/4">Result</th>
                                <th className="px-6 py-3 font-medium w-1/4">Units</th>
                                <th className="px-6 py-3 font-medium text-right">Reference</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {items.map((result, idx) => (
                                <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-3 font-medium text-slate-700">
                                        {result.test_name}
                                    </td>
                                    <td className="px-6 py-3">
                                        <span className={getFlagStyle(result.flags)}>
                                            {result.value}
                                        </span>
                                    </td>
                                    <td className="px-6 py-3 text-slate-500">
                                        {result.unit}
                                    </td>
                                    <td className="px-6 py-3 text-right text-slate-400 font-mono text-xs">
                                        {result.reference_range}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ))}
        </div>
    );
}
