import { FileText, Download, Calendar, Eye } from 'lucide-react';
import { useState } from 'react';
import DocumentDetails from './DocumentDetails';

export default function DocumentList({ documents }) {
    const [selectedDocId, setSelectedDocId] = useState(null);

    if (!documents || !documents.length) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileText className="text-gray-400 w-8 h-8" />
                </div>
                <h3 className="text-gray-900 font-medium text-lg">No documents found</h3>
                <p className="text-gray-500 mt-2">Uploaded medical records will appear here.</p>
            </div>
        );
    }

    return (
        <>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-white">
                    <div>
                        <h3 className="font-semibold text-slate-900 text-lg">Medical Records</h3>
                        <p className="text-sm text-gray-500 mt-0.5">Manage and view your history</p>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-600 rounded-full border border-slate-200">
                        {documents.length} Files
                    </span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-600">
                        <thead className="bg-slate-50 text-slate-700 font-medium border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-4">Document Name</th>
                                <th className="px-6 py-4">Date</th>
                                <th className="px-6 py-4">Provider</th>
                                <th className="px-6 py-4">Type</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {documents.map((doc) => (
                                <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors group">
                                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-3">
                                        <div className="p-2 bg-red-50 rounded-lg text-red-500 group-hover:bg-red-100 transition-colors">
                                            <FileText size={18} />
                                        </div>
                                        <span className="font-semibold">{doc.filename}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2 text-slate-500">
                                            <Calendar size={14} />
                                            {new Date(doc.date).toLocaleDateString()}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                                            ${doc.provider === 'regina_maria' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                                                doc.provider === 'synevo' ? 'bg-orange-50 text-orange-700 border-orange-100' : 'bg-gray-50 text-gray-700 border-gray-100'}`}>
                                            {doc.provider === 'regina_maria' ? 'Regina Maria' : doc.provider}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">{doc.category || 'Analysis'}</td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => setSelectedDocId(doc.id)}
                                                className="text-teal-600 bg-teal-50 hover:bg-teal-100 transition-colors p-2 rounded-full"
                                                title="View Details"
                                            >
                                                <Eye size={18} />
                                            </button>
                                            <button
                                                onClick={() => window.open(`http://localhost:8000/documents/${doc.id}/download`, '_blank')}
                                                className="text-slate-400 hover:text-slate-600 transition-colors p-2 hover:bg-slate-100 rounded-full"
                                                title="Download PDF"
                                            >
                                                <Download size={18} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {selectedDocId && (
                <DocumentDetails
                    documentId={selectedDocId}
                    onClose={() => setSelectedDocId(null)}
                />
            )}
        </>
    );
}
