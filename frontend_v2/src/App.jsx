import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import VerifyEmail from './pages/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Biomarkers from './pages/Biomarkers';
import Evolution from './pages/Evolution';
import LinkedAccounts from './pages/LinkedAccounts';
import HealthReports from './pages/HealthReports';
import Screenings from './pages/Screenings';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import Layout from './components/Layout';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  return children;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/" element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/documents" element={
            <PrivateRoute>
              <Layout>
                <Documents />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/biomarkers" element={
            <PrivateRoute>
              <Layout>
                <Biomarkers />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/evolution/:name" element={
            <PrivateRoute>
              <Layout>
                <Evolution />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/linked-accounts" element={
            <PrivateRoute>
              <Layout>
                <LinkedAccounts />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/profile" element={
            <PrivateRoute>
              <Layout>
                <Profile />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/health" element={
            <PrivateRoute>
              <Layout>
                <HealthReports />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/screenings" element={
            <PrivateRoute>
              <Layout>
                <Screenings />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/admin" element={
            <PrivateRoute>
              <Layout>
                <Admin />
              </Layout>
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
