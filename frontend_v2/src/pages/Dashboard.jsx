import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { Activity, FileCheck, AlertTriangle, ArrowRight, TrendingUp, Plus, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';

const StatCard = ({ title, value, subtitle, icon: Icon, colorClass, delay }) => (
    <div className={cn("group card p-6 relative overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-backwards", delay)}>
        <div className="relative z-10 flex flex-col justify-between h-full">
            <div className="flex justify-between items-start mb-4">
                <div className={cn("p-3 rounded-2xl shadow-sm transition-colors", colorClass)}>
                    <Icon size={24} className="text-white" />
                </div>
                {/* Decorative background circle */}
                <div className={cn("absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-125", colorClass.replace('bg-', 'bg-text-'))} />
            </div>

            <div>
                <h3 className="text-4xl font-bold text-slate-800 tracking-tight">{value}</h3>
                <p className="text-slate-500 font-medium text-sm mt-1">{title}</p>
                {subtitle && <p className="text-xs text-slate-400 mt-2 font-medium">{subtitle}</p>}
            </div>
        </div>
    </div>
);

const Dashboard = () => {
    const [stats, setStats] = useState({ documents_count: 0, biomarkers_count: 0, alerts_count: 0 });
    const [recentBiomarkers, setRecentBiomarkers] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, recentRes, alertsRes] = await Promise.all([
                    api.get('/dashboard/stats'),
                    api.get('/dashboard/recent-biomarkers'),
                    api.get('/dashboard/alerts-count')
                ]);
                setStats({
                    ...statsRes.data,
                    alerts_count: alertsRes.data.alerts_count
                });
                setRecentBiomarkers(recentRes.data);
            } catch (e) {
                console.error("Failed to fetch dashboard data", e);
            }
        };
        fetchData();
    }, []);

    return (
        <div>
            {/* Quick Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <StatCard
                    title="Analyzed Documents"
                    value={stats.documents_count}
                    subtitle="Last upload 2 days ago"
                    icon={FileCheck}
                    colorClass="bg-primary-500"
                    delay="delay-0"
                />
                <StatCard
                    title="Biomarkers Tracked"
                    value={stats.biomarkers_count}
                    subtitle="Across 3 providers"
                    icon={Activity}
                    colorClass="bg-teal-500" // Using Teal for health
                    delay="delay-100"
                />
                <StatCard
                    title="Health Alerts"
                    value={stats.alerts_count}
                    subtitle={stats.alerts_count === 0 ? "All values within normal range" : "Values outside normal range"}
                    icon={stats.alerts_count > 0 ? AlertTriangle : ShieldCheck}
                    colorClass={stats.alerts_count > 0 ? "bg-rose-500" : "bg-indigo-500"}
                    delay="delay-200"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Evolution & Trends Column */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="card p-6 h-full">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                                <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg"><TrendingUp size={18} /></span>
                                Recent Analysis
                            </h3>
                            <Link to="/biomarkers" className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1 transition-colors">
                                View All <ArrowRight size={14} />
                            </Link>
                        </div>

                        <div className="space-y-3">
                            {recentBiomarkers.length === 0 ? (
                                <div className="text-center py-8 text-slate-400">
                                    <Activity size={32} className="mx-auto mb-2 opacity-50" />
                                    <p>No biomarkers yet. Sync your medical accounts to get started.</p>
                                </div>
                            ) : (
                                recentBiomarkers.map((bio, i) => (
                                    <Link
                                        key={i}
                                        to={`/evolution/${encodeURIComponent(bio.name)}`}
                                        className="group flex items-center justify-between p-4 rounded-xl border border-transparent hover:border-slate-100 hover:bg-slate-50 transition-all duration-200"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 border-white shadow-sm",
                                                bio.status === 'normal' ? 'bg-teal-50 text-teal-600' : 'bg-rose-50 text-rose-600'
                                            )}>
                                                {bio.name.charAt(0)}
                                            </div>
                                            <div>
                                                <p className="font-semibold text-slate-800 group-hover:text-primary-700 transition-colors">{bio.name}</p>
                                                <p className="text-xs text-slate-400">{bio.date}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="text-right">
                                                <p className="font-bold text-slate-700">{bio.lastValue}</p>
                                                <p className={cn("text-xs font-semibold uppercase tracking-wider", bio.status === 'normal' ? "text-teal-500" : "text-rose-500")}>
                                                    {bio.status === 'normal' ? 'Normal' : 'Attention'}
                                                </p>
                                            </div>
                                            <ArrowRight size={18} className="text-slate-300 group-hover:text-primary-500 group-hover:translate-x-1 transition-all" />
                                        </div>
                                    </Link>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Quick Actions Column */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Upload CTA */}
                    <Link to="/documents" className="card p-6 flex flex-col items-center text-center hover:ring-2 hover:ring-primary-500/20 group cursor-pointer border-dashed border-2 border-slate-200 hover:border-primary-300 bg-slate-50/50">
                        <div className="p-4 bg-white rounded-full shadow-sm mb-4 group-hover:scale-110 transition-transform duration-300">
                            <Plus size={32} className="text-primary-500" />
                        </div>
                        <h4 className="text-lg font-bold text-slate-800">Upload New Report</h4>
                        <p className="text-sm text-slate-500 mt-2 px-4">Drag and drop your PDF medical files here to analyze them instantly.</p>
                    </Link>

                    {/* Sync Account CTA */}
                    <div className="card p-6 bg-gradient-to-br from-slate-800 to-slate-900 text-white relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-10">
                            <Activity size={120} />
                        </div>
                        <div className="relative z-10">
                            <h4 className="text-lg font-bold">Connect Providers</h4>
                            <p className="text-slate-300 text-sm mt-2 mb-6">Sync directly with Regina Maria or Synevo.</p>
                            <button className="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg text-sm font-medium transition-colors w-full">
                                Manage Linked Accounts
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
