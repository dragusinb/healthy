import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Gift, Copy, Send, CheckCircle, Users, Crown, ExternalLink, Mail
} from 'lucide-react';
import api from '../api/client';
import usePageTitle from '../hooks/usePageTitle';

export default function Referral() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';
  usePageTitle('referral.title', 'Invite Friends');

  const [referralCode, setReferralCode] = useState('');
  const [referralUrl, setReferralUrl] = useState('');
  const [stats, setStats] = useState({ invited: 0, rewarded: 0 });
  const [referrals, setReferrals] = useState([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [codeRes, statsRes] = await Promise.all([
        api.get('/referral/my-code'),
        api.get('/referral/stats')
      ]);
      setReferralCode(codeRes.data.referral_code);
      setReferralUrl(codeRes.data.referral_url);
      setStats(codeRes.data.stats);
      setReferrals(statsRes.data.referrals || []);
    } catch (err) {
      console.error('Failed to fetch referral data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(referralUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const input = document.createElement('input');
      input.value = referralUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSendInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail) return;

    setSending(true);
    setError('');
    setSuccess('');

    try {
      await api.post('/referral/send-invite', { email: inviteEmail });
      setSuccess(isRomanian ? 'Invitația a fost trimisă!' : 'Invite sent!');
      setInviteEmail('');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || (isRomanian ? 'Eroare la trimitere' : 'Failed to send'));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-48 mb-4" />
        <div className="h-64 bg-slate-200 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-base sm:text-2xl font-bold text-slate-800">
          {isRomanian ? 'Invită prieteni' : 'Invite Friends'}
        </h2>
        <p className="text-sm sm:text-base text-slate-600">
          {isRomanian
            ? 'Invită un prieten și amândoi primiți 1 lună de Premium gratuit!'
            : 'Invite a friend and both of you get 1 free month of Premium!'}
        </p>
      </div>

      {/* Reward Banner */}
      <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 rounded-2xl border border-amber-200 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-amber-500 rounded-xl">
            <Gift className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">
              {isRomanian ? '1 lună Premium gratuit' : '1 free month of Premium'}
            </h3>
            <p className="text-sm text-slate-600">
              {isRomanian
                ? 'Pentru tine și pentru fiecare prieten care se înregistrează'
                : 'For you and every friend who signs up'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-white/70 rounded-lg p-3 text-center">
            <Crown className="w-5 h-5 text-amber-500 mx-auto mb-1" />
            <p className="text-xs text-slate-600">
              {isRomanian ? '8+ specialiști AI' : '8+ AI specialists'}
            </p>
          </div>
          <div className="bg-white/70 rounded-lg p-3 text-center">
            <Users className="w-5 h-5 text-amber-500 mx-auto mb-1" />
            <p className="text-xs text-slate-600">
              {isRomanian ? '30 analize/lună' : '30 analyses/mo'}
            </p>
          </div>
          <div className="bg-white/70 rounded-lg p-3 text-center">
            <Gift className="w-5 h-5 text-amber-500 mx-auto mb-1" />
            <p className="text-xs text-slate-600">
              {isRomanian ? 'Nutriție + Fitness' : 'Nutrition + Fitness'}
            </p>
          </div>
        </div>
      </div>

      {/* Share Link */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <h3 className="font-semibold text-slate-800 mb-3">
          {isRomanian ? 'Link-ul tău de invitație' : 'Your invite link'}
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={referralUrl}
            readOnly
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 truncate"
          />
          <button
            onClick={handleCopy}
            className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors ${
              copied
                ? 'bg-green-100 text-green-700'
                : 'bg-cyan-50 text-cyan-700 hover:bg-cyan-100'
            }`}
          >
            {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
            {copied ? (isRomanian ? 'Copiat!' : 'Copied!') : (isRomanian ? 'Copiază' : 'Copy')}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          {isRomanian ? `Codul tău: ${referralCode}` : `Your code: ${referralCode}`}
        </p>
      </div>

      {/* Send Invite by Email */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <h3 className="font-semibold text-slate-800 mb-3">
          {isRomanian ? 'Trimite o invitație pe email' : 'Send invite by email'}
        </h3>

        {success && (
          <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2">
            <CheckCircle size={16} />
            {success}
          </div>
        )}
        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSendInvite} className="flex gap-2">
          <div className="relative flex-1">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder={isRomanian ? 'email@prieten.ro' : 'friend@email.com'}
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
              required
            />
          </div>
          <button
            type="submit"
            disabled={sending}
            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg font-medium text-sm flex items-center gap-2 hover:from-amber-600 hover:to-orange-600 disabled:opacity-50"
          >
            <Send size={16} />
            {sending
              ? (isRomanian ? 'Se trimite...' : 'Sending...')
              : (isRomanian ? 'Trimite' : 'Send')}
          </button>
        </form>
      </div>

      {/* Stats */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <h3 className="font-semibold text-slate-800 mb-4">
          {isRomanian ? 'Statisticile tale' : 'Your stats'}
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-slate-800">{stats.invited}</p>
            <p className="text-sm text-slate-600">
              {isRomanian ? 'Prieteni invitați' : 'Friends invited'}
            </p>
          </div>
          <div className="bg-amber-50 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-amber-600">{stats.rewarded}</p>
            <p className="text-sm text-slate-600">
              {isRomanian ? 'Luni Premium câștigate' : 'Premium months earned'}
            </p>
          </div>
        </div>

        {/* Referral history */}
        {referrals.length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-4">
            <p className="text-sm font-medium text-slate-600 mb-2">
              {isRomanian ? 'Istoric invitații' : 'Invite history'}
            </p>
            <div className="space-y-2">
              {referrals.map((ref, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-slate-700">{ref.email || '—'}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    ref.status === 'rewarded'
                      ? 'bg-green-100 text-green-700'
                      : ref.status === 'registered'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {ref.status === 'rewarded'
                      ? (isRomanian ? 'Recompensat' : 'Rewarded')
                      : ref.status === 'registered'
                      ? (isRomanian ? 'Înregistrat' : 'Registered')
                      : (isRomanian ? 'În așteptare' : 'Pending')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
