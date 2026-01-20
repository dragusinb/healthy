import React, { useState, useEffect } from 'react';
import { Search, Filter, AlertCircle, CheckCircle } from 'lucide-react';
import { clsx } from 'clsx';

export default function ResultsList({ results, initialFilterAbnormal = false, onTestClick }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [showAbnormalOnly, setShowAbnormalOnly] = useState(initialFilterAbnormal);

    useEffect(() => {
        setShowAbnormalOnly(initialFilterAbnormal);
    }, [initialFilterAbnormal]);

    // 1. Filter
    const filteredResults = results.filter(item => {
        const matchesSearch = item.test_name.toLowerCase().includes(searchTerm.toLowerCase());
        const isAbnormal = item.flags === 'HIGH' || item.flags === 'LOW';

        if (showAbnormalOnly && !isAbnormal) return false;
        return matchesSearch;
    });

    // 2. Sort Chronologically (Newest First)
    filteredResults.sort((a, b) => {
        const dateA = a.date ? new Date(a.date) : new Date(0);
        const dateB = b.date ? new Date(b.date) : new Date(0);
        return dateB - dateA;
    });

    // 3. Group by Date -> Category
    const groupedByDate = filteredResults.reduce((acc, curr) => {
        const dateStr = curr.date ? new Date(curr.date).toLocaleDateString(undefined, {
            year: 'numeric', month: 'long', day: 'numeric'
        }) : 'Unknown Date';

        if (!acc[dateStr]) {
            acc[dateStr] = {
                dateObj: curr.date ? new Date(curr.date) : new Date(0),
                categories: {}
            };
        }

        const cat = curr.category || 'General';
        if (!acc[dateStr].categories[cat]) {
            acc[dateStr].categories[cat] = [];
        }
        acc[dateStr].categories[cat].push(curr);
        return acc;
    }, {});

    // Helper for styles
    const getFlagStyle = (flag) => {
        switch (flag) {
            case 'HIGH': return 'bg-red-50 text-red-700 font-bold border border-red-100 px-2 py-0.5 rounded text-xs';
            case 'LOW': return 'bg-yellow-50 text-yellow-700 font-bold border border-yellow-100 px-2 py-0.5 rounded text-xs';
            case 'NORMAL': return 'text-teal-700 font-medium text-sm';
            default: return 'text-slate-700 font-medium text-sm';
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Controls */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-wrap gap-4 items-center justify-between sticky top-20 z-30">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                        type="text"
                        placeholder="Search biomarkers..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 w-full bg-slate-50 border-transparent focus:bg-white focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 rounded-lg text-sm transition-all outline-none"
                    />
                </div>

                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer select-none px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-200">
                        <input
                            type="checkbox"
                            checked={showAbnormalOnly}
                            onChange={(e) => setShowAbnormalOnly(e.target.checked)}
                            className="w-4 h-4 text-teal-600 rounded focus:ring-teal-500 border-gray-300"
                        />
                        <span className="text-sm font-medium text-slate-700 flex items-center gap-2">
                            <AlertCircle size={16} className={showAbnormalOnly ? "text-amber-500" : "text-slate-400"} />
                            Show Abnormal Only
                        </span>
                    </label>
                </div>
            </div>

            {/* Timeline View */}
            {Object.keys(groupedByDate).length === 0 ? (
                <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-300">
                    <p className="text-slate-500">No results found matching your criteria.</p>
                </div>
            ) : (
                <div className="space-y-12">
                    {Object.entries(groupedByDate).map(([dateStr, group]) => (
                        <div key={dateStr} className="relative pl-8 border-l-2 border-slate-200 ml-4 pb-8 last:pb-0">
                            {/* Timeline Dot */}
                            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-4 border-teal-500"></div>

                            {/* Date Header */}
                            <div className="mb-6">
                                <h2 className="text-xl font-bold text-slate-900 leading-none">{dateStr}</h2>
                                <p className="text-sm text-slate-400 mt-1">Medical Report</p>
                            </div>

                            {/* Categories Grid */}
                            <div className="grid grid-cols-1 gap-6">
                                {Object.entries(group.categories).map(([category, items]) => (
                                    <div key={category} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                                        <div className="px-5 py-3 bg-slate-50/80 border-b border-gray-100 flex items-center gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-slate-400"></div>
                                            <h3 className="font-semibold text-slate-700 uppercase tracking-wide text-xs">
                                                {category}
                                            </h3>
                                        </div>

                                        <div className="divide-y divide-gray-50">
                                            {items.map((result, idx) => (
                                                <div
                                                    key={idx}
                                                    onClick={() => onTestClick && onTestClick(result.test_name)}
                                                    className="p-4 hover:bg-slate-50/50 transition-colors flex items-center justify-between group cursor-pointer"
                                                >
                                                    <div className="flex-1 min-w-0 pr-4">
                                                        <p className="font-medium text-slate-700 truncate group-hover:text-teal-600 transition-colors">
                                                            {result.test_name}
                                                        </p>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-xs text-slate-400 font-mono">
                                                                Ref: {result.reference_range || '-'}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <div className="text-right">
                                                        <div className="flex items-center justify-end gap-2">
                                                            <span className="font-bold text-slate-900">{result.value}</span>
                                                            <span className="text-xs text-slate-500">{result.unit}</span>
                                                        </div>
                                                        <div className="mt-1 h-5">
                                                            <span className={getFlagStyle(result.flags)}>
                                                                {result.flags !== 'NORMAL' ? result.flags : ''}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
