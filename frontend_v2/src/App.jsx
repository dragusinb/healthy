import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SubscriptionProvider } from './context/SubscriptionContext';
import { AnalysisProvider } from './context/AnalysisContext';
import ErrorBoundary from './components/ErrorBoundary';
import PageLoader from './components/PageLoader';
import CookieConsent from './components/CookieConsent';

// Critical path - loaded immediately (needed for initial render)
import Login from './pages/Login';
import Home from './pages/Home';

// Lazy loaded pages - code split into separate chunks
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const VaultUnlock = lazy(() => import('./pages/VaultUnlock'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Documents = lazy(() => import('./pages/Documents'));
const Biomarkers = lazy(() => import('./pages/Biomarkers'));
const Evolution = lazy(() => import('./pages/Evolution'));
const LinkedAccounts = lazy(() => import('./pages/LinkedAccounts'));
const HealthReports = lazy(() => import('./pages/HealthReports'));
const Screenings = lazy(() => import('./pages/Screenings'));
const Lifestyle = lazy(() => import('./pages/Lifestyle'));
const Profile = lazy(() => import('./pages/Profile'));
const Settings = lazy(() => import('./pages/Settings'));
const Admin = lazy(() => import('./pages/Admin'));
const Pricing = lazy(() => import('./pages/Pricing'));
const Billing = lazy(() => import('./pages/Billing'));
const Terms = lazy(() => import('./pages/Terms'));
const Privacy = lazy(() => import('./pages/Privacy'));
const JoinFamily = lazy(() => import('./pages/JoinFamily'));
const Family = lazy(() => import('./pages/Family'));
const SupportTickets = lazy(() => import('./pages/SupportTickets'));
const Layout = lazy(() => import('./components/Layout'));
const NotFound = lazy(() => import('./pages/NotFound'));

// Inline loader for layout-wrapped components
const LayoutLoader = () => (
    <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
);

const PrivateRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return <PageLoader />;
    if (!user) return <Navigate to="/login" />;

    return children;
};

// Wrapper that shows Layout for logged-in users, standalone for guests
const OptionalLayoutRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return <PageLoader />;

    if (user) {
        return (
            <Suspense fallback={<PageLoader />}>
                <Layout>{children}</Layout>
            </Suspense>
        );
    }

    return children;
};

// Private route with Layout
const PrivateLayoutRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return <PageLoader />;
    if (!user) return <Navigate to="/login" />;

    return (
        <Suspense fallback={<PageLoader />}>
            <Layout>
                <Suspense fallback={<LayoutLoader />}>
                    {children}
                </Suspense>
            </Layout>
        </Suspense>
    );
};

// Home page for guests, Dashboard for logged-in users
const HomeOrDashboard = () => {
    const { user, loading } = useAuth();

    if (loading) return <PageLoader />;

    if (user) {
        return (
            <Suspense fallback={<PageLoader />}>
                <Layout>
                    <Suspense fallback={<LayoutLoader />}>
                        <Dashboard />
                    </Suspense>
                </Layout>
            </Suspense>
        );
    }

    return <Home />;
};

const App = () => {
    return (
        <ErrorBoundary>
            <AuthProvider>
                <SubscriptionProvider>
                    <AnalysisProvider>
                    <Router>
                        <CookieConsent />
                        <Suspense fallback={<PageLoader />}>
                            <Routes>
                                {/* Public routes */}
                                <Route path="/login" element={<Login />} />
                                <Route path="/verify-email" element={<VerifyEmail />} />
                                <Route path="/forgot-password" element={<ForgotPassword />} />
                                <Route path="/reset-password" element={<ResetPassword />} />
                                <Route path="/vault-unlock" element={<VaultUnlock />} />
                                <Route path="/pricing" element={<Pricing />} />
                                <Route path="/join-family" element={<JoinFamily />} />

                                {/* Home / Dashboard */}
                                <Route path="/" element={<HomeOrDashboard />} />

                                {/* Private routes with Layout */}
                                <Route path="/documents" element={
                                    <PrivateLayoutRoute><Documents /></PrivateLayoutRoute>
                                } />
                                <Route path="/biomarkers" element={
                                    <PrivateLayoutRoute><Biomarkers /></PrivateLayoutRoute>
                                } />
                                <Route path="/evolution/:name" element={
                                    <PrivateLayoutRoute><Evolution /></PrivateLayoutRoute>
                                } />
                                <Route path="/linked-accounts" element={
                                    <PrivateLayoutRoute><LinkedAccounts /></PrivateLayoutRoute>
                                } />
                                <Route path="/profile" element={
                                    <PrivateLayoutRoute><Profile /></PrivateLayoutRoute>
                                } />
                                <Route path="/health" element={
                                    <PrivateLayoutRoute><HealthReports /></PrivateLayoutRoute>
                                } />
                                <Route path="/screenings" element={
                                    <PrivateLayoutRoute><Screenings /></PrivateLayoutRoute>
                                } />
                                <Route path="/lifestyle" element={
                                    <PrivateLayoutRoute><Lifestyle /></PrivateLayoutRoute>
                                } />
                                <Route path="/admin" element={
                                    <PrivateLayoutRoute><Admin /></PrivateLayoutRoute>
                                } />
                                <Route path="/settings" element={
                                    <PrivateLayoutRoute><Settings /></PrivateLayoutRoute>
                                } />
                                <Route path="/billing" element={
                                    <PrivateLayoutRoute><Billing /></PrivateLayoutRoute>
                                } />
                                <Route path="/family" element={
                                    <PrivateLayoutRoute><Family /></PrivateLayoutRoute>
                                } />
                                <Route path="/support" element={
                                    <PrivateLayoutRoute><SupportTickets /></PrivateLayoutRoute>
                                } />

                                {/* Optional layout routes (show layout for logged-in users) */}
                                <Route path="/terms" element={
                                    <OptionalLayoutRoute><Terms /></OptionalLayoutRoute>
                                } />
                                <Route path="/privacy" element={
                                    <OptionalLayoutRoute><Privacy /></OptionalLayoutRoute>
                                } />

                                {/* 404 catch-all route */}
                                <Route path="*" element={<NotFound />} />
                            </Routes>
                        </Suspense>
                    </Router>
                    </AnalysisProvider>
                </SubscriptionProvider>
            </AuthProvider>
        </ErrorBoundary>
    );
};

export default App;
