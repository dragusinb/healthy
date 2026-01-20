import { FileText, Download, Calendar, Activity } from 'lucide-react';

export default function DocumentList({ documents }) {
    if (!documents.length) {
        return (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <FileText className="text-gray-400" />
                </div>
                <h3 className="text-gray-900 font-medium">No documents found</h3>
                <p className="text-gray-500 text-sm mt-1">Uploaded documents will appear here.</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-semibold text-slate-800">Recent Documents</h3>
                <span className="text-xs font-medium px-2.5 py-1 bg-teal-50 text-teal-700 rounded-full">
                    {documents.length} Files
                </span>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-slate-50 text-slate-700 font-medium border-b border-gray-100">
                        <tr>
                            <th className="px-6 py-3">Document Name</th>
                            <th className="px-6 py-3">Date</th>
                            <th className="px-6 py-3">Provider</th>
                            <th className="px-6 py-3">Type</th>
                            <th className="px-6 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {documents.map((doc) => (
                            <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                                <td className="px-6 py-3 font-medium text-slate-900 flex items-center gap-3">
                                    <div className="p-2 bg-red-50 rounded text-red-500">
                                        <FileText size={18} />
                                    </div>
                                    {doc.filename}
                                </td>
                                <td className="px-6 py-3">
                                    <div className="flex items-center gap-2">
                                        <Calendar size={14} className="text-gray-400" />
                                        {new Date(doc.date).toLocaleDateString()}
                                    </div>
                                </td>
                                <td className="px-6 py-3">
                                    <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium 
                                        ${doc.provider === 'regina_maria' ? 'bg-blue-50 text-blue-700' :
                                            doc.provider === 'synevo' ? 'bg-orange-50 text-orange-700' : 'bg-gray-100 text-gray-700'}`}>
                                        {doc.provider === 'regina_maria' ? 'Regina Maria' : doc.provider}
                                    </span>
                                </td>
                                <td className="px-6 py-3 text-slate-500">{doc.category || 'Medical Report'}</td>
                                <td className="px-6 py-3 text-right">
                                    <button className="text-slate-400 hover:text-teal-600 transition-colors">
                                        <Download size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
