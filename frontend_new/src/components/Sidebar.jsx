import { Activity, FileText, BarChart2, Settings, Heart, Stethoscope } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
    const menuItems = [
        { id: 'dashboard', label: 'Overview', icon: Heart },
        { id: 'analysis', label: 'Descifrare Analize', icon: Stethoscope },
        { id: 'results', label: 'Results List', icon: FileText },
        { id: 'documents', label: 'Documents', icon: FileText },
        { id: 'trends', label: 'Trends', icon: BarChart2 },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <aside className="fixed left-0 top-0 w-64 h-screen bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 z-50">
            <div className="p-6 flex items-center gap-3">
                <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center shadow-lg shadow-teal-500/20">
                    <Activity className="text-white w-5 h-5" />
                </div>
                <h1 className="text-xl font-bold text-white tracking-tight">Healthy.ai</h1>
            </div>

            <nav className="flex-1 px-4 py-4 space-y-2">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${isActive
                                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
                                : 'hover:bg-slate-800 hover:text-white border border-transparent'
                                }`}
                        >
                            <Icon size={20} className={`transition-colors ${isActive ? 'text-teal-400' : 'text-slate-400 group-hover:text-white'}`} />
                            <span className="font-medium">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center gap-3 px-4 py-2 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer">
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white ring-2 ring-slate-800">
                        BD
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">Bogdan Dragusin</p>
                        <p className="text-xs text-slate-500">Premium Plan</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
