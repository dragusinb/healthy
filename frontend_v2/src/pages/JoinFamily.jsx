import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Users, Check, AlertCircle, ArrowLeft, RefreshCw, UserPlus, LogIn } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function JoinFamily() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const inviteCode = searchParams.get('code');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [manualCode, setManualCode] = useState(inviteCode || '');

  const handleJoin = async (code) => {
    if (!code?.trim()) {
      setError(isRomanian ? 'Introdu codul de invitație' : 'Enter invite code');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.post(`/subscription/family/join/${code.trim()}`);
      setSuccess(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.includes('already in a family')) {
        setError(isRomanian ? 'Ești deja într-un grup de familie' : 'You are already in a family group');
      } else if (detail?.includes('Invalid invite code')) {
        setError(isRomanian ? 'Cod de invitație invalid sau expirat' : 'Invalid or expired invite code');
      } else if (detail?.includes('full')) {
        setError(isRomanian ? 'Grupul familiei este plin' : 'Family group is full');
      } else {
        setError(detail || (isRomanian ? 'Eroare la alăturare' : 'Failed to join'));
      }
    } finally {
      setLoading(false);
    }
  };

  // Auto-join if user is logged in and has code in URL
  useEffect(() => {
    if (user && inviteCode && !success && !error) {
      handleJoin(inviteCode);
    }
  }, [user, inviteCode]);

  // Not logged in
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-purple-100 rounded-2xl mx-auto mb-4 flex items-center justify-center">
              <Users size={32} className="text-purple-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-800 mb-2">
              {isRomanian ? 'Invitație în Familie' : 'Family Invitation'}
            </h1>
            <p className="text-slate-600">
              {isRomanian
                ? 'Ai fost invitat să te alături unui grup de familie cu acces Premium!'
                : 'You\'ve been invited to join a family group with Premium access!'}
            </p>
          </div>

          {inviteCode && (
            <div className="bg-purple-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-slate-600 mb-2">
                {isRomanian ? 'Codul de invitație:' : 'Invite code:'}
              </p>
              <p className="font-mono text-lg font-semibold text-purple-700 text-center">
                {inviteCode}
              </p>
            </div>
          )}

          <p className="text-slate-600 text-sm mb-6 text-center">
            {isRomanian
              ? 'Pentru a accepta invitația, trebuie să ai un cont.'
              : 'To accept the invitation, you need to have an account.'}
          </p>

          <div className="space-y-3">
            <Link
              to={`/login?redirect=/join-family?code=${inviteCode}`}
              className="w-full py-3 px-4 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
            >
              <LogIn size={18} />
              {isRomanian ? 'Autentifică-te' : 'Sign In'}
            </Link>
            <Link
              to={`/login?redirect=/join-family?code=${inviteCode}&register=true`}
              className="w-full py-3 px-4 border border-purple-200 text-purple-600 rounded-xl font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
            >
              <UserPlus size={18} />
              {isRomanian ? 'Creează Cont' : 'Create Account'}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <Check size={32} className="text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            {isRomanian ? 'Te-ai alăturat cu succes!' : 'Successfully Joined!'}
          </h1>
          <p className="text-slate-600 mb-6">
            {isRomanian
              ? 'Acum ai acces la toate funcționalitățile Premium.'
              : 'You now have access to all Premium features.'}
          </p>

          <div className="bg-purple-50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 text-purple-700 font-medium mb-2">
              <Users size={18} />
              {isRomanian ? 'Beneficii Premium Activate' : 'Premium Benefits Activated'}
            </div>
            <ul className="text-sm text-purple-600 space-y-1 text-left">
              <li>• {isRomanian ? '500 documente' : '500 documents'}</li>
              <li>• {isRomanian ? '30 analize AI/lună' : '30 AI analyses/month'}</li>
              <li>• {isRomanian ? 'Toți specialiștii AI' : 'All AI specialists'}</li>
              <li>• {isRomanian ? 'Export PDF, partajare cu medicii' : 'PDF export, doctor sharing'}</li>
            </ul>
          </div>

          <button
            onClick={() => navigate('/')}
            className="w-full py-3 px-4 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors"
          >
            {isRomanian ? 'Mergi la Dashboard' : 'Go to Dashboard'}
          </button>
        </div>
      </div>
    );
  }

  // Main join form (logged in, no auto-join yet or error)
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-2 text-slate-600 hover:text-slate-800"
        >
          <ArrowLeft size={18} />
          {isRomanian ? 'Înapoi' : 'Back'}
        </button>

        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-purple-100 rounded-2xl mx-auto mb-4 flex items-center justify-center">
            <Users size={32} className="text-purple-600" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            {isRomanian ? 'Alătură-te Familiei' : 'Join Family'}
          </h1>
          <p className="text-slate-600">
            {isRomanian
              ? 'Introdu codul de invitație pentru a obține acces Premium gratuit.'
              : 'Enter the invite code to get free Premium access.'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {isRomanian ? 'Cod de Invitație' : 'Invite Code'}
            </label>
            <input
              type="text"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              placeholder={isRomanian ? 'ex: abc123xyz' : 'e.g., abc123xyz'}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none font-mono text-center text-lg"
            />
          </div>

          <button
            onClick={() => handleJoin(manualCode)}
            disabled={loading || !manualCode.trim()}
            className="w-full py-3 px-4 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <RefreshCw size={18} className="animate-spin" />
            ) : (
              <UserPlus size={18} />
            )}
            {loading
              ? (isRomanian ? 'Se procesează...' : 'Processing...')
              : (isRomanian ? 'Alătură-te Acum' : 'Join Now')}
          </button>
        </div>
      </div>
    </div>
  );
}
