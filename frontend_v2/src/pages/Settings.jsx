import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Bell, Mail, Clock, Check, AlertCircle, Download, Trash2, Shield, Loader2, AlertTriangle } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // GDPR states
  const [exporting, setExporting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const response = await api.get('/notifications/preferences');
      setPreferences(response.data);
    } catch (err) {
      setError('Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      // Use the GDPR export endpoint which returns a ZIP file
      const response = await api.get('/gdpr/export', {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analize_online_export_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(t('settings.exportFailed') || 'Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword || !deleteConfirm) return;

    setDeleting(true);
    setDeleteError(null);

    try {
      await api.post('/gdpr/delete-account', {
        password: deletePassword,
        confirm_text: 'DELETE MY ACCOUNT'
      });
      // Account deleted - logout and redirect
      logout();
      navigate('/login');
    } catch (err) {
      setDeleteError(err.response?.data?.detail || t('settings.deleteFailed') || 'Failed to delete account');
    } finally {
      setDeleting(false);
    }
  };

  const updatePreference = async (key, value) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    setSaving(true);
    setSuccess(false);

    try {
      await api.put('/notifications/preferences', { [key]: value });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      setError('Failed to save');
      // Revert on error
      fetchPreferences();
    } finally {
      setSaving(false);
    }
  };

  const Toggle = ({ checked, onChange, disabled }) => (
    <button
      onClick={() => onChange(!checked)}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-cyan-500' : 'bg-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Bell className="w-8 h-8 text-cyan-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{t('notifications.preferences')}</h1>
          <p className="text-gray-600">{t('notifications.preferencesDesc')}</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700">
          <Check className="w-5 h-5" />
          {t('common.success')}
        </div>
      )}

      {/* Email Notification Toggles */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-800">{t('notifications.emailSettings')}</h2>
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {/* New Documents */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('notifications.newDocuments')}</p>
              <p className="text-sm text-gray-500">{t('notifications.newDocumentsDesc')}</p>
            </div>
            <Toggle
              checked={preferences?.email_new_documents}
              onChange={(v) => updatePreference('email_new_documents', v)}
              disabled={saving}
            />
          </div>

          {/* Abnormal Biomarkers */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('notifications.abnormalBiomarkers')}</p>
              <p className="text-sm text-gray-500">{t('notifications.abnormalBiomarkersDesc')}</p>
            </div>
            <Toggle
              checked={preferences?.email_abnormal_biomarkers}
              onChange={(v) => updatePreference('email_abnormal_biomarkers', v)}
              disabled={saving}
            />
          </div>

          {/* Analysis Complete */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('notifications.analysisComplete')}</p>
              <p className="text-sm text-gray-500">{t('notifications.analysisCompleteDesc')}</p>
            </div>
            <Toggle
              checked={preferences?.email_analysis_complete}
              onChange={(v) => updatePreference('email_analysis_complete', v)}
              disabled={saving}
            />
          </div>

          {/* Sync Failed */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('notifications.syncFailed')}</p>
              <p className="text-sm text-gray-500">{t('notifications.syncFailedDesc')}</p>
            </div>
            <Toggle
              checked={preferences?.email_sync_failed}
              onChange={(v) => updatePreference('email_sync_failed', v)}
              disabled={saving}
            />
          </div>

          {/* Reminders */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('notifications.reminders')}</p>
              <p className="text-sm text-gray-500">{t('notifications.remindersDesc')}</p>
            </div>
            <Toggle
              checked={preferences?.email_reminders}
              onChange={(v) => updatePreference('email_reminders', v)}
              disabled={saving}
            />
          </div>
        </div>
      </div>

      {/* Frequency Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-800">{t('notifications.frequency')}</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">{t('notifications.frequencyDesc')}</p>
        </div>

        <div className="px-6 py-4">
          <div className="flex gap-3">
            {['immediate', 'daily', 'weekly'].map((freq) => (
              <button
                key={freq}
                onClick={() => updatePreference('email_frequency', freq)}
                disabled={saving}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  preferences?.email_frequency === freq
                    ? 'bg-cyan-500 text-white border-cyan-500'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-cyan-300'
                } ${saving ? 'opacity-50' : ''}`}
              >
                {t(`notifications.${freq}`)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">{t('notifications.quietHours')}</h2>
          <p className="text-sm text-gray-500 mt-1">{t('notifications.quietHoursDesc')}</p>
        </div>

        <div className="px-6 py-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">{t('notifications.from')}</label>
              <select
                value={preferences?.quiet_hours_start ?? ''}
                onChange={(e) => updatePreference('quiet_hours_start', e.target.value ? parseInt(e.target.value) : null)}
                disabled={saving}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="">--</option>
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, '0')}:00</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">{t('notifications.to')}</label>
              <select
                value={preferences?.quiet_hours_end ?? ''}
                onChange={(e) => updatePreference('quiet_hours_end', e.target.value ? parseInt(e.target.value) : null)}
                disabled={saving}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="">--</option>
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, '0')}:00</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy & Data (GDPR) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mt-6">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-800">{t('settings.privacyData') || 'Privacy & Data'}</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">{t('settings.privacyDataDesc') || 'Manage your personal data'}</p>
        </div>

        <div className="divide-y divide-gray-100">
          {/* Export Data */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{t('settings.exportData') || 'Export My Data'}</p>
              <p className="text-sm text-gray-500">{t('settings.exportDataDesc') || 'Download all your personal data as JSON'}</p>
            </div>
            <button
              onClick={handleExportData}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50"
            >
              {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {exporting ? (t('common.loading') || 'Loading...') : (t('settings.download') || 'Download')}
            </button>
          </div>

          {/* Delete Account */}
          <div className="px-6 py-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-rose-600">{t('settings.deleteAccount') || 'Delete Account'}</p>
              <p className="text-sm text-gray-500">{t('settings.deleteAccountDesc') || 'Permanently delete your account and all data'}</p>
            </div>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-rose-100 text-rose-600 rounded-lg hover:bg-rose-200 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              {t('settings.delete') || 'Delete'}
            </button>
          </div>
        </div>
      </div>

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-rose-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-rose-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-800">{t('settings.deleteAccountTitle') || 'Delete Account'}</h3>
                <p className="text-sm text-gray-500">{t('settings.deleteAccountWarning') || 'This action cannot be undone'}</p>
              </div>
            </div>

            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
              {t('settings.deleteAccountInfo') || 'All your documents, biomarkers, health reports, and personal data will be permanently deleted.'}
            </div>

            {deleteError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
                <AlertCircle className="w-4 h-4" />
                {deleteError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('settings.enterPassword') || 'Enter your password to confirm'}
                </label>
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose-500"
                  placeholder="Password"
                />
              </div>

              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.checked)}
                  className="mt-1 w-4 h-4 text-rose-600 rounded focus:ring-rose-500"
                />
                <span className="text-sm text-gray-700">
                  {t('settings.confirmDelete') || 'I understand that this will permanently delete all my data'}
                </span>
              </label>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletePassword('');
                  setDeleteConfirm(false);
                  setDeleteError(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                {t('common.cancel') || 'Cancel'}
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={!deletePassword || !deleteConfirm || deleting}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deleting ? (t('common.deleting') || 'Deleting...') : (t('settings.deleteForever') || 'Delete Forever')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
