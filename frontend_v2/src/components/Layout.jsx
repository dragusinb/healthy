import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileText, Activity, LogOut, User, HeartPulse, Link as LinkIcon, Brain } from 'lucide-react';
import { cn } from '../lib/utils';

const SidebarItem = ({ to, icon: Icon, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) => cn(
            "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium text-sm group",
            isActive
                ? "bg-primary-50 text-primary-700 shadow-sm"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
        )}
    >
        {({ isActive }) => (
            <>
                <Icon size={20} className={isActive ? "text-primary-600" : "text-slate-400 group-hover:text-slate-600"} />
                <span>{label}</span>
            </>
        )}
    </NavLink>
);

const Layout = ({ children }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    // Page Title mapping based on path
    const getPageTitle = () => {
        const path = location.pathname;
        if (path === '/') return 'Dashboard';
        if (path.startsWith('/documents')) return 'Medical Documents';
        if (path.startsWith('/biomarkers')) return 'Biomarkers';
        if (path.startsWith('/evolution')) return 'Evolution & Trends';
        if (path.startsWith('/health')) return 'AI Health Analysis';
        if (path.startsWith('/linked-accounts')) return 'Connect Providers';
        return '';
    }

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            {/* Modern Sidebar */}
            <aside className="w-72 bg-white border-r border-slate-200 flex flex-col hidden md:flex h-full shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)] z-10">
                <div className="p-8 pb-4">
                    <div className="flex items-center gap-3 text-primary-600 mb-8">
                        <div className="p-2.5 bg-primary-100 rounded-xl">
                            <HeartPulse size={28} className="text-primary-600" />
                        </div>
                        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Healthy<span className="text-primary-500">.ai</span></h1>
                    </div>

                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">Menu</div>
                    <nav className="space-y-1.5">
                        <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
                        <SidebarItem to="/documents" icon={FileText} label="Documents" />
                        <SidebarItem to="/biomarkers" icon={Activity} label="Biomarkers" />
                        <SidebarItem to="/health" icon={Brain} label="AI Analysis" />
                        <div className="pt-4 mt-4 border-t border-slate-100"></div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">Settings</div>
                        <SidebarItem to="/linked-accounts" icon={LinkIcon} label="Linked Accounts" />
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-100">
                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 mb-2">
                        <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 overflow-hidden border-2 border-white shadow-sm">
                            <User size={20} />
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-sm font-semibold text-slate-700 truncate">{user?.email?.split('@')[0]}</p>
                            <p className="text-xs text-slate-400 truncate font-medium">Free Plan</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 mt-2 text-sm text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors font-medium"
                    >
                        <LogOut size={16} />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto relative scroll-smooth">
                {/* Top Header for Mobile & Title */}
                <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-4 flex items-center justify-between md:hidden">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-primary-50 rounded-lg">
                            <HeartPulse size={20} className="text-primary-600" />
                        </div>
                        <span className="font-bold text-slate-800">Healthy.ai</span>
                    </div>
                    <button onClick={handleLogout} className="p-2 text-slate-500">
                        <LogOut size={20} />
                    </button>
                </header>

                <div className="max-w-7xl mx-auto p-6 md:p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Dynamic Page Header */}
                    <div className="mb-8 hidden md:block">
                        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">{getPageTitle()}</h2>
                        <div className="h-1 w-20 bg-primary-500 rounded-full mt-2 opacity-20"></div>
                    </div>

                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
