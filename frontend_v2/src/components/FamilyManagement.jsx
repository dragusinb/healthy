import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Users, Copy, Check, UserPlus, UserMinus, LogOut,
  Crown, AlertCircle, RefreshCw, Link as LinkIcon
} from 'lucide-react';
import api from '../api/client';

export default function FamilyManagement({ familyInfo, tier, onRefresh }) {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';

  const [joinCode, setJoinCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [copied, setCopied] = useState(false);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  // Create family group (for family plan owners without a group)
  const handleCreateFamily = async () => {
    clearMessages();
    setLoading(true);
    try {
      await api.post('/subscription/family/create');
      setSuccess(isRomanian ? 'Grupul familiei a fost creat!' : 'Family group created!');
      onRefresh?.();
    } catch (err) {
      setError(err.response?.data?.detail || (isRomanian ? 'Eroare la creare' : 'Creation failed'));
    } finally {
      setLoading(false);
    }
  };

  // Join family with invite code
  const handleJoinFamily = async () => {
    if (!joinCode.trim()) {
      setError(isRomanian ? 'Introdu codul de invitație' : 'Enter invite code');
      return;
    }

    clearMessages();
    setLoading(true);
    try {
      await api.post(`/subscription/family/join/${joinCode.trim()}`);
      setSuccess(isRomanian ? 'Te-ai alăturat grupului familiei!' : 'Joined family group!');
      setJoinCode('');
      onRefresh?.();
    } catch (err) {
      setError(err.response?.data?.detail || (isRomanian ? 'Cod invalid' : 'Invalid code'));
    } finally {
      setLoading(false);
    }
  };

  // Leave family
  const handleLeaveFamily = async () => {
    const confirmMsg = isRomanian
      ? 'Sigur vrei să părăsești grupul familiei? Vei pierde accesul Premium.'
      : 'Are you sure you want to leave the family group? You will lose Premium access.';

    if (!window.confirm(confirmMsg)) return;

    clearMessages();
    setLoading(true);
    try {
      await api.post('/subscription/family/leave');
      setSuccess(isRomanian ? 'Ai părăsit grupul familiei' : 'Left family group');
      onRefresh?.();
    } catch (err) {
      setError(err.response?.data?.detail || (isRomanian ? 'Eroare' : 'Error'));
    } finally {
      setLoading(false);
    }
  };

  // Remove member (owner only)
  const handleRemoveMember = async (memberId, email) => {
    const confirmMsg = isRomanian
      ? `Sigur vrei să elimini ${email} din familie?`
      : `Are you sure you want to remove ${email} from the family?`;

    if (!window.confirm(confirmMsg)) return;

    clearMessages();
    setLoading(true);
    try {
      await api.delete(`/subscription/family/member/${memberId}`);
      setSuccess(isRomanian ? 'Membrul a fost eliminat' : 'Member removed');
      onRefresh?.();
    } catch (err) {
      setError(err.response?.data?.detail || (isRomanian ? 'Eroare' : 'Error'));
    } finally {
      setLoading(false);
    }
  };

  // Copy invite code/link
  const handleCopyInvite = () => {
    const inviteLink = `${window.location.origin}/join-family?code=${familyInfo?.invite_code}`;
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(familyInfo?.invite_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Status messages
  const renderMessages = () => (
    <>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700 text-sm">
          <Check size={16} />
          {success}
        </div>
      )}
    </>
  );

  // Case 1: User has family subscription but hasn't created a group yet
  if (tier === 'family' && !familyInfo?.has_family) {
    return (
      <div className="bg-white rounded-2xl border border-purple-200 shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-purple-100 rounded-xl">
            <Users className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-800">
              {isRomanian ? 'Planul Family' : 'Family Plan'}
            </h3>
            <p className="text-sm text-slate-500">
              {isRomanian ? 'Creează-ți grupul de familie' : 'Create your family group'}
            </p>
          </div>
        </div>

        {renderMessages()}

        <p className="text-slate-600 mb-4">
          {isRomanian
            ? 'Ai planul Family activ! Creează un grup de familie pentru a invita până la 5 membri care vor beneficia de acces Premium.'
            : 'You have the Family plan active! Create a family group to invite up to 5 members who will get Premium access.'}
        </p>

        <button
          onClick={handleCreateFamily}
          disabled={loading}
          className="w-full py-3 px-4 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <RefreshCw size={18} className="animate-spin" />
          ) : (
            <UserPlus size={18} />
          )}
          {isRomanian ? 'Creează Grupul Familiei' : 'Create Family Group'}
        </button>
      </div>
    );
  }

  // Case 2: User is family owner - show management
  if (familyInfo?.is_owner) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-purple-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-800">{familyInfo.name}</h3>
              <p className="text-sm text-slate-500">
                {isRomanian
                  ? `${familyInfo.members?.length || 1} / ${familyInfo.max_members} membri`
                  : `${familyInfo.members?.length || 1} / ${familyInfo.max_members} members`}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          {renderMessages()}

          {/* Invite Section */}
          <div className="bg-purple-50 rounded-xl p-4 mb-6">
            <h4 className="font-medium text-slate-800 mb-2 flex items-center gap-2">
              <LinkIcon size={16} className="text-purple-600" />
              {isRomanian ? 'Invită Membri' : 'Invite Members'}
            </h4>
            <p className="text-sm text-slate-600 mb-3">
              {isRomanian
                ? 'Trimite acest cod membrilor familiei pentru a se alătura grupului.'
                : 'Share this code with family members to join your group.'}
            </p>

            <div className="flex gap-2">
              <div className="flex-1 bg-white rounded-lg border border-purple-200 px-4 py-2 font-mono text-lg text-center text-purple-700 font-semibold">
                {familyInfo.invite_code}
              </div>
              <button
                onClick={handleCopyCode}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                {copied ? <Check size={18} /> : <Copy size={18} />}
                <span className="hidden sm:inline">
                  {copied ? (isRomanian ? 'Copiat!' : 'Copied!') : (isRomanian ? 'Copiază' : 'Copy')}
                </span>
              </button>
            </div>

            <button
              onClick={handleCopyInvite}
              className="mt-3 w-full py-2 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-100 rounded-lg transition-colors"
            >
              {isRomanian ? 'Copiază link-ul complet de invitație' : 'Copy full invite link'}
            </button>
          </div>

          {/* Members List */}
          <h4 className="font-medium text-slate-800 mb-3">
            {isRomanian ? 'Membri' : 'Members'}
          </h4>
          <div className="space-y-2">
            {familyInfo.members?.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    member.role === 'owner' ? 'bg-amber-100 text-amber-600' : 'bg-purple-100 text-purple-600'
                  }`}>
                    {member.role === 'owner' ? <Crown size={18} /> : <Users size={18} />}
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">{member.email}</p>
                    <p className="text-xs text-slate-500">
                      {member.role === 'owner'
                        ? (isRomanian ? 'Proprietar' : 'Owner')
                        : (isRomanian ? 'Membru' : 'Member')}
                      {member.joined_at && (
                        <span className="ml-2">
                          • {isRomanian ? 'Din' : 'Since'} {new Date(member.joined_at).toLocaleDateString()}
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {member.role !== 'owner' && (
                  <button
                    onClick={() => handleRemoveMember(member.id, member.email)}
                    disabled={loading}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title={isRomanian ? 'Elimină' : 'Remove'}
                  >
                    <UserMinus size={18} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Case 3: User is family member
  if (familyInfo?.has_family && !familyInfo?.is_owner) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-purple-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-800">{familyInfo.name}</h3>
              <p className="text-sm text-slate-500">
                {isRomanian ? 'Membru al grupului familiei' : 'Family group member'}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          {renderMessages()}

          <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 text-green-700 mb-2">
              <Check size={18} />
              <span className="font-medium">
                {isRomanian ? 'Acces Premium Activ' : 'Premium Access Active'}
              </span>
            </div>
            <p className="text-sm text-green-600">
              {isRomanian
                ? 'Beneficiezi de toate funcționalitățile Premium ca membru al acestei familii.'
                : 'You have access to all Premium features as a member of this family.'}
            </p>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl mb-4">
            <div>
              <p className="text-sm text-slate-500">{isRomanian ? 'Proprietar grup' : 'Group owner'}</p>
              <p className="font-medium text-slate-800">{familyInfo.owner_email}</p>
            </div>
            <Crown className="text-amber-500" size={24} />
          </div>

          <button
            onClick={handleLeaveFamily}
            disabled={loading}
            className="w-full py-3 px-4 border border-red-200 text-red-600 rounded-xl font-medium hover:bg-red-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw size={18} className="animate-spin" /> : <LogOut size={18} />}
            {isRomanian ? 'Părăsește Grupul' : 'Leave Group'}
          </button>
        </div>
      </div>
    );
  }

  // Case 4: Free user - show join option
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-purple-100 rounded-xl">
          <Users className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            {isRomanian ? 'Alătură-te unei Familii' : 'Join a Family'}
          </h3>
          <p className="text-sm text-slate-500">
            {isRomanian ? 'Obține acces Premium gratuit' : 'Get free Premium access'}
          </p>
        </div>
      </div>

      {renderMessages()}

      <p className="text-slate-600 mb-4">
        {isRomanian
          ? 'Ai un cod de invitație de la cineva cu planul Family? Introdu-l mai jos pentru a obține acces Premium.'
          : 'Have an invite code from someone with a Family plan? Enter it below to get Premium access.'}
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={joinCode}
          onChange={(e) => setJoinCode(e.target.value)}
          placeholder={isRomanian ? 'Introdu codul de invitație' : 'Enter invite code'}
          className="flex-1 px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
        />
        <button
          onClick={handleJoinFamily}
          disabled={loading || !joinCode.trim()}
          className="px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <RefreshCw size={18} className="animate-spin" /> : <UserPlus size={18} />}
          {isRomanian ? 'Alătură-te' : 'Join'}
        </button>
      </div>
    </div>
  );
}
