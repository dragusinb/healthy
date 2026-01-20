import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, AlertTriangle, TrendingUp, TrendingDown, CheckCircle, ArrowRight } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function DoctorDashboard({ onNavigate, onViewAlerts }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const response = await axios.get('http://localhost:8000/analysis/summary');
                setData(response.data);
                setLoading(false);
            } catch (err) {
                console.error(err);
                setLoading(false);
            }
        };
        fetchAnalysis();
    }, []);

    if (loading) return <div className="p-8 text-center text-slate-500">Loading Doctor's Analysis...</div>;
    if (!data) return <div className="p-8 text-center text-red-500">Failed to load analysis.</div>;

    const { counts, alerts, trends } = data;

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-900 mb-2">Health Summary</h1>
                <p className="text-slate-500">AI-powered analysis of your biomarker history.</p>
            </div>

            {/* Top Level Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard
                    title="Total Tests"
                    value={counts.total_tests}
                    icon={<Activity className="text-blue-500" />}
                    color="bg-blue-50"
                />
                <StatCard
                    title="Abnormalities"
                    value={counts.abnormal_findings}
                    label={counts.abnormal_findings > 0 ? "Needs Attention" : "All Good"}
                    icon={<AlertTriangle className={counts.abnormal_findings > 0 ? "text-amber-500" : "text-green-500"} />}
                    color={counts.abnormal_findings > 0 ? "bg-amber-50" : "bg-green-50"}
                    onClick={onViewAlerts}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                />
                <StatCard
                    title="Documents analyzed"
                    value={counts.total_documents}
                    icon={<CheckCircle className="text-teal-500" />}
                    color="bg-teal-50"
                />
            </div>

            {/* Medical Advice Section */}
            {data.advice && data.advice.length > 0 && (
                <div className="grid grid-cols-1 gap-4 animate-in fade-in slide-in-from-top-4">
                    {data.advice.map((card, idx) => (
                        <div key={idx} className={`p-6 rounded-xl border-l-4 shadow-sm flex flex-col md:flex-row gap-4 items-start ${card.type === 'warning' ? 'bg-amber-50 border-amber-400' : 'bg-green-50 border-green-400'}`}>
                            <div className={`p-3 rounded-full flex-shrink-0 ${card.type === 'warning' ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'}`}>
                                <Activity size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
                                    {card.role}
                                    <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-white/50 border border-black/5 text-slate-600">Automated Recommendation</span>
                                </h3>
                                <p className="text-slate-700 leading-relaxed italic">"{card.advice}"</p>
                                {card.triggers && (
                                    <div className="mt-3 flex gap-2 flex-wrap">
                                        {card.triggers.map((t, i) => (
                                            <span key={i} className="text-xs font-semibold px-2 py-1 bg-white rounded border border-black/10 text-slate-600">{t}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Immediate Attention - Red/Yellow Flags */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <AlertTriangle size={20} className="text-red-500" />
                        Recent Alerts
                    </h2>
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        {alerts.length === 0 ? (
                            <div className="p-8 text-center text-slate-400">No abnormal results found recently. Great job!</div>
                        ) : (
                            <div className="divide-y divide-gray-50">
                                {alerts.map((alert, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => onNavigate && onNavigate(alert.test_name)}
                                        className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors cursor-pointer group"
                                    >
                                        <div>
                                            <div className="font-semibold text-slate-800 group-hover:text-teal-600 transition-colors">{alert.test_name}</div>
                                            <div className="text-xs text-slate-400">{new Date(alert.date).toLocaleDateString()}</div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="text-right">
                                                <div className="font-bold text-slate-900">{alert.value} <span className="text-xs font-normal text-slate-400">{alert.unit}</span></div>
                                            </div>
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${alert.flag === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                {alert.flag}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Trends - Up/Down */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                        <TrendingUp size={20} className="text-blue-500" />
                        Key Trends
                    </h2>
                    <div className="space-y-4">
                        {trends.map((trend, idx) => (
                            <TrendCard key={idx} trend={trend} onClick={() => onNavigate && onNavigate(trend.test_name)} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, label, icon, color, onClick, className }) {
    return (
        <div
            onClick={onClick}
            className={`bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between ${className || ''}`}
        >
            <div>
                <p className="text-slate-500 text-sm font-medium mb-1">{title}</p>
                <div className="text-3xl font-bold text-slate-900">{value}</div>
                {label && <div className="text-xs text-slate-400 mt-1">{label}</div>}
            </div>
            <div className={`p-4 rounded-xl ${color}`}>
                {icon}
            </div>
        </div>
    );
}

export function TrendCard({ trend, onClick }) {
    // Generate mini sparkline data
    const data = trend.history.map((val, i) => ({ i, val }));
    const color = trend.direction === 'up' ? '#3b82f6' : trend.direction === 'down' ? '#f59e0b' : '#10b981';

    return (
        <div
            onClick={onClick}
            className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex items-center gap-4 cursor-pointer hover:bg-slate-50 transition-colors group"
        >
            <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center flex-shrink-0 group-hover:bg-white group-hover:shadow-md transition-all">
                {trend.direction === 'up' && <TrendingUp className="text-blue-500" />}
                {trend.direction === 'down' && <TrendingDown className="text-amber-500" />}
                {trend.direction === 'stable' && <ArrowRight className="text-teal-500" />}
            </div>

            <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-slate-800 truncate group-hover:text-teal-600 transition-colors">{trend.test_name}</h4>
                <div className="text-xs text-slate-500 flex items-center gap-1">
                    Is trending <span className="font-bold uppercase">{trend.direction}</span> ({trend.change_pct > 0 ? '+' : ''}{trend.change_pct}%)
                </div>
            </div>

            <div className="h-12 w-24">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <Area type="monotone" dataKey="val" stroke={color} fill={color} fillOpacity={0.1} strokeWidth={2} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <div className="text-right">
                <div className="font-bold text-slate-900">{trend.current_value}</div>
                <div className="text-xs text-slate-400">{trend.unit}</div>
            </div>
        </div>
    );
}
