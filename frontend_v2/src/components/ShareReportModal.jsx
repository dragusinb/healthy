import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Share2, Copy, Check, Lock, Clock, X, Link as LinkIcon, Eye } from 'lucide-react';
import api from '../api/client';

export default function ShareReportModal({ onClose, reportIds = [] }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [shareData, setShareData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expiresDays, setExpiresDays] = useState(7);
  const [password, setPassword] = useState('');
  const [usePassword, setUsePassword] = useState(false);

  const handleCreate = async () => {
    setLoading(true);
    try {
      const res = await api.post('/sharing/create', {
        report_ids: reportIds,
        expires_days: expiresDays,
        password: usePassword ? password : null
      });
      setShareData(res.data);
    } catch (e) {
      console.error('Failed to create share link', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!shareData) return;
    const url = `${window.location.origin}/shared/${shareData.token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 duration-300">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Share2 size={20} className="text-primary-600" />
            {t('sharing.title')}
          </h3>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
            <X size={18} />
          </button>
        </div>

        {!shareData ? (
          <>
            <p className="text-sm text-slate-600 mb-6">{t('sharing.description')}</p>

            {/* Expiry */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                <Clock size={14} className="inline mr-1" /> {t('sharing.expiresIn')}
              </label>
              <select value={expiresDays} onChange={(e) => setExpiresDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
              >
                <option value={1}>1 {t('sharing.day')}</option>
                <option value={3}>3 {t('sharing.days')}</option>
                <option value={7}>7 {t('sharing.days')}</option>
                <option value={14}>14 {t('sharing.days')}</option>
                <option value={30}>30 {t('sharing.days')}</option>
              </select>
            </div>

            {/* Password protection */}
            <div className="mb-6">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2 cursor-pointer">
                <input
                  type="checkbox" checked={usePassword}
                  onChange={(e) => setUsePassword(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <Lock size={14} /> {t('sharing.passwordProtect')}
              </label>
              {usePassword && (
                <input
                  type="text" value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('sharing.passwordPlaceholder')}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mt-2"
                />
              )}
            </div>

            <button
              onClick={handleCreate}
              disabled={loading || (usePassword && !password)}
              className="w-full py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <LinkIcon size={16} /> {t('sharing.createLink')}
                </>
              )}
            </button>
          </>
        ) : (
          <>
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Check size={32} className="text-emerald-600" />
              </div>
              <p className="font-medium text-slate-800">{t('sharing.linkCreated')}</p>
            </div>

            {/* Link display */}
            <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg mb-4">
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/shared/${shareData.token}`}
                className="flex-1 bg-transparent text-sm text-slate-600 outline-none"
              />
              <button onClick={handleCopy}
                className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-1"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? t('sharing.copied') : t('sharing.copy')}
              </button>
            </div>

            <div className="space-y-2 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <Clock size={14} />
                <span>{t('sharing.expiresOn')} {new Date(shareData.expires_at).toLocaleDateString()}</span>
              </div>
              {shareData.has_password && (
                <div className="flex items-center gap-2">
                  <Lock size={14} />
                  <span>{t('sharing.passwordRequired')}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Eye size={14} />
                <span>{shareData.report_count} {t('sharing.reportsIncluded')}</span>
              </div>
            </div>

            <button onClick={onClose}
              className="w-full mt-6 py-2.5 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
            >
              {t('common.close')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
