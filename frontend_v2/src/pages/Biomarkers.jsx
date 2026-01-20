import React, { useEffect, useState } from 'react';
import api from '../api/client';
import { Activity, Search, AlertTriangle, ArrowUp, ArrowDown, Calendar, Filter } from 'lucide-react';
import { cn } from '../lib/utils';
import { Link } from 'react-router-dom';

const Biomarkers = () => {
    const [biomarkers, setBiomarkers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState('all'); // all, out_of_range

    useEffect(() => {
        fetchBiomarkers();
    }, []);

    const fetchBiomarkers = async () => {
        setLoading(true);
        try {
            const res = await api.get('/dashboard/biomarkers');
            setBiomarkers(res.data);
        } catch (e) {
            console.error("Failed to fetch biomarkers", e);
        } finally {
            setLoading(false);
        }
    };

    const mockBiomarkers = [
        { id: 1, name: 'Hemoglobina', value: 14.5, unit: 'g/dL', range: '12-16', date: '2023-10-15', provider: 'Synevo', status: 'normal' },
        { id: 2, name: 'Glucoza', value: 105, unit: 'mg/dL', range: '70-99', date: '2023-10-15', provider: 'Synevo', status: 'high' },
        { id: 3, name: 'Colesterol Total', value: 240, unit: 'mg/dL', range: '<200', date: '2023-12-01', provider: 'Regina Maria', status: 'high' },
        { id: 4, name: 'VSH', value: 10, unit: 'mm/h', range: '<20', date: '2023-12-01', provider: 'Regina Maria', status: 'normal' },
        { id: 5, name: 'Creatinina', value: 0.8, unit: 'mg/dL', range: '0.6-1.1', date: '2023-12-01', provider: 'Regina Maria', status: 'normal' },
        { id: 6, name: 'TGP', value: 45, unit: 'U/L', range: '<40', date: '2023-12-01', provider: 'Regina Maria', status: 'high' },
    ];

    // Use state data instead of mock
    const filteredBiomarkers = biomarkers.filter(b =>
        b.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        (filter === 'all' || (filter === 'out_of_range' && b.status !== 'normal'))
    );

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:flex-none group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-500 transition-colors" size={18} />
                        <input
                            type="text"
                            placeholder="Search tests..."
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
                                filter === 'all' ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
                            )}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setFilter('out_of_range')}
                            className={cn(
                                "px-4 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-1.5",
                                filter === 'out_of_range' ? "bg-white text-rose-600 shadow-sm" : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
                            )}
                        >
                            <AlertTriangle size={14} />
                            Issues
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="grid grid-cols-12 gap-4 p-5 border-b border-slate-100 bg-slate-50/50 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <div className="col-span-4 pl-2">Test Name</div>
                    <div className="col-span-2">Value</div>
                    <div className="col-span-2">Ref. Range</div>
                    <div className="col-span-2">Date</div>
                    <div className="col-span-2 text-right pr-2">Status</div>
                </div>

                <div className="divide-y divide-slate-50">
                    {filteredBiomarkers.map((bio) => (
                        <div key={bio.id} className="grid grid-cols-12 gap-4 p-5 items-center hover:bg-slate-50/80 transition-all duration-200 group">
                            <div className="col-span-4 font-semibold text-slate-900 flex items-center gap-3 pl-2">
                                <Link to={`/evolution/${encodeURIComponent(bio.name)}`} className="flex items-center gap-3 hover:text-primary-600 transition-colors">
                                    <div className={cn(
                                        "p-2 rounded-lg border shadow-sm",
                                        bio.status === 'normal' ? "bg-teal-50 border-teal-100 text-teal-600" : "bg-rose-50 border-rose-100 text-rose-600"
                                    )}>
                                        <Activity size={18} />
                                    </div>
                                    {bio.name}
                                </Link>
                            </div>

                            <div className="col-span-2 font-bold text-slate-800 flex items-baseline gap-1">
                                {bio.value} <span className="text-slate-400 text-xs font-medium">{bio.unit}</span>
                            </div>

                            <div className="col-span-2 text-sm text-slate-500 font-medium bg-slate-50 px-2 py-1 rounded inline-block w-fit">
                                {bio.range}
                            </div>

                            <div className="col-span-2 text-sm text-slate-500 flex items-center gap-1.5">
                                <Calendar size={14} className="text-slate-400" />
                                {new Date(bio.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                            </div>

                            <div className="col-span-2 text-right pr-2">
                                {bio.status === 'normal' ? (
                                    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-100 shadow-sm">
                                        Normal
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-100 shadow-sm">
                                        {bio.value > 100 ? <ArrowUp size={12} strokeWidth={3} /> : <ArrowDown size={12} strokeWidth={3} />}
                                        Out of Range
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer info */}
                <div className="p-4 bg-slate-50 border-t border-slate-100 text-center text-xs text-slate-400 font-medium">
                    Showing {filteredBiomarkers.length} results based on your filters
                </div>
            </div>
        </div>
    );
};

export default Biomarkers;
