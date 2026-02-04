import React from 'react';
import { Loader2 } from 'lucide-react';

const PageLoader = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
            <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-sm">Loading...</p>
        </div>
    </div>
);

export default PageLoader;
