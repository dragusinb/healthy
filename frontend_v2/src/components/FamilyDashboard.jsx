import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  Users, User, AlertTriangle, FileText, Activity,
  ChevronRight, Lock, Unlock, TrendingUp, TrendingDown,
  Calendar, Heart, RefreshCw, Eye
} from 'lucide-react';
import api from '../api/client';

export default function FamilyDashboard() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const isRomanian = i18n.language === 'ro';

  const [members, setMembers] = useState([]);
  const [healthSummary, setHealthSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasFamily, setHasFamily] = useState(false);
  const [familyName, setFamilyName] = useState('');
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberBiomarkers, setMemberBiomarkers] = useState(null);
  const [loadingBiomarkers, setLoadingBiomarkers] = useState(false);

  useEffect(() => {
    fetchFamilyData();
  }, []);

  const fetchFamilyData = async () => {
    setLoading(true);
    try {
      const [membersRes, summaryRes] = await Promise.all([
        api.get('/subscription/family/members-with-data'),
        api.get('/subscription/family/health-summary')
      ]);

      setMembers(membersRes.data.members || []);
      setHasFamily(membersRes.data.has_family);
      setFamilyName(membersRes.data.family_name || '');
      setHealthSummary(summaryRes.data.summary || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load family data');
    } finally {
      setLoading(false);
    }
  };

  const fetchMemberBiomarkers = async (userId) => {
    setLoadingBiomarkers(true);
    try {
      const response = await api.get(`/subscription/family/members/${userId}/biomarkers-grouped`);
      setMemberBiomarkers(response.data);
    } catch (err) {
      console.error('Failed to load biomarkers:', err);
    } finally {
      setLoadingBiomarkers(false);
    }
  };

  const handleMemberClick = (member) => {
    if (member.is_current_user) {
      navigate('/biomarkers');
      return;
    }
    setSelectedMember(member);
    fetchMemberBiomarkers(member.id);
  };

  const getMemberSummary = (userId) => {
    return healthSummary.find(s => s.user_id === userId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (!hasFamily) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
        <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          {isRomanian ? 'Nu faci parte dintr-o familie' : 'Not in a family group'}
        </h3>
        <p className="text-slate-600 mb-4">
          {isRomanian
            ? 'Alătură-te unei familii sau creează una pentru a vedea datele membrilor.'
            : 'Join a family or create one to view member data.'}
        </p>
        <button
          onClick={() => navigate('/billing')}
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          {isRomanian ? 'Gestionare Familie' : 'Manage Family'}
        </button>
      </div>
    );
  }

  // Member detail view
  if (selectedMember) {
    return (
      <div className="space-y-6">
        {/* Back button */}
        <button
          onClick={() => {
            setSelectedMember(null);
            setMemberBiomarkers(null);
          }}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors"
        >
          <ChevronRight className="w-5 h-5 rotate-180" />
          {isRomanian ? 'Înapoi la familie' : 'Back to family'}
        </button>

        {/* Member header */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center">
              <User className="w-8 h-8 text-purple-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-slate-800">
                {selectedMember.full_name || selectedMember.email}
              </h2>
              <p className="text-slate-500">{selectedMember.email}</p>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <span className="flex items-center gap-1">
                  <FileText className="w-4 h-4" />
                  {selectedMember.document_count} {isRomanian ? 'documente' : 'documents'}
                </span>
                <span className="flex items-center gap-1">
                  <Activity className="w-4 h-4" />
                  {selectedMember.biomarker_count} {isRomanian ? 'biomarkeri' : 'biomarkers'}
                </span>
                {selectedMember.alerts_count > 0 && (
                  <span className="flex items-center gap-1 text-amber-600">
                    <AlertTriangle className="w-4 h-4" />
                    {selectedMember.alerts_count} {isRomanian ? 'alerte' : 'alerts'}
                  </span>
                )}
              </div>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              selectedMember.vault_active
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'
            }`}>
              {selectedMember.vault_active ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
              {selectedMember.vault_active
                ? (isRomanian ? 'Online' : 'Online')
                : (isRomanian ? 'Offline' : 'Offline')}
            </div>
          </div>

          {!selectedMember.vault_active && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
              <AlertTriangle className="w-4 h-4 inline mr-2" />
              {isRomanian
                ? 'Membrul nu este conectat. Valorile biomarkerilor vor fi disponibile când se va conecta.'
                : 'Member is not logged in. Biomarker values will be available when they log in.'}
            </div>
          )}
        </div>

        {/* Biomarkers */}
        {loadingBiomarkers ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 text-primary-600 animate-spin" />
          </div>
        ) : memberBiomarkers ? (
          <div className="space-y-4">
            {memberBiomarkers.categories?.map((category) => (
              <div key={category.name} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="font-semibold text-slate-800">{category.name}</h3>
                  {category.alerts_count > 0 && (
                    <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full">
                      {category.alerts_count} {isRomanian ? 'alerte' : 'alerts'}
                    </span>
                  )}
                </div>
                <div className="divide-y divide-slate-100">
                  {category.biomarkers.map((bio) => (
                    <div
                      key={bio.id}
                      className="px-6 py-3 flex items-center justify-between hover:bg-slate-50"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-slate-800">{bio.canonical_name || bio.test_name}</p>
                        {bio.document_date && (
                          <p className="text-xs text-slate-500">
                            {new Date(bio.document_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        {bio.values_available ? (
                          <p className={`font-semibold ${
                            bio.flags === 'HIGH' ? 'text-red-600' :
                            bio.flags === 'LOW' ? 'text-blue-600' :
                            'text-slate-800'
                          }`}>
                            {bio.value || bio.numeric_value} {bio.unit}
                          </p>
                        ) : (
                          <p className="text-slate-400 text-sm flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            {isRomanian ? 'Indisponibil' : 'Unavailable'}
                          </p>
                        )}
                        {bio.reference_range && (
                          <p className="text-xs text-slate-500">{bio.reference_range}</p>
                        )}
                      </div>
                      <div className="ml-4 w-6 flex justify-center">
                        {bio.flags === 'HIGH' && <TrendingUp className="w-5 h-5 text-red-500" />}
                        {bio.flags === 'LOW' && <TrendingDown className="w-5 h-5 text-blue-500" />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {memberBiomarkers.categories?.length === 0 && (
              <div className="text-center py-8 text-slate-500">
                {isRomanian ? 'Nu există biomarkeri' : 'No biomarkers found'}
              </div>
            )}
          </div>
        ) : null}
      </div>
    );
  }

  // Family overview
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-8 h-8" />
          <h2 className="text-2xl font-bold">{familyName}</h2>
        </div>
        <p className="text-purple-100">
          {isRomanian
            ? `${members.length} membri în familie`
            : `${members.length} family members`}
        </p>
      </div>

      {/* Members grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {members.map((member) => {
          const summary = getMemberSummary(member.id);

          return (
            <div
              key={member.id}
              onClick={() => handleMemberClick(member)}
              className={`bg-white rounded-2xl border shadow-sm p-5 cursor-pointer transition-all hover:shadow-md hover:border-purple-300 ${
                member.is_current_user ? 'border-purple-200 bg-purple-50/30' : 'border-slate-200'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    member.is_current_user ? 'bg-purple-100' : 'bg-slate-100'
                  }`}>
                    <User className={`w-6 h-6 ${member.is_current_user ? 'text-purple-600' : 'text-slate-600'}`} />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">
                      {member.full_name || member.email.split('@')[0]}
                    </p>
                    <p className="text-xs text-slate-500">
                      {member.role === 'owner' ? (isRomanian ? 'Proprietar' : 'Owner') : (isRomanian ? 'Membru' : 'Member')}
                      {member.is_current_user && (
                        <span className="ml-1 text-purple-600">({isRomanian ? 'Tu' : 'You'})</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className={`p-1 rounded-full ${
                  member.vault_active ? 'bg-green-100' : 'bg-slate-100'
                }`}>
                  {member.vault_active
                    ? <Unlock className="w-4 h-4 text-green-600" />
                    : <Lock className="w-4 h-4 text-slate-400" />
                  }
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="text-center p-2 bg-slate-50 rounded-lg">
                  <p className="text-lg font-semibold text-slate-800">{member.document_count}</p>
                  <p className="text-xs text-slate-500">{isRomanian ? 'Documente' : 'Docs'}</p>
                </div>
                <div className="text-center p-2 bg-slate-50 rounded-lg">
                  <p className="text-lg font-semibold text-slate-800">{member.biomarker_count}</p>
                  <p className="text-xs text-slate-500">{isRomanian ? 'Biomarkeri' : 'Biomarkers'}</p>
                </div>
                <div className={`text-center p-2 rounded-lg ${
                  member.alerts_count > 0 ? 'bg-amber-50' : 'bg-slate-50'
                }`}>
                  <p className={`text-lg font-semibold ${
                    member.alerts_count > 0 ? 'text-amber-600' : 'text-slate-800'
                  }`}>{member.alerts_count}</p>
                  <p className="text-xs text-slate-500">{isRomanian ? 'Alerte' : 'Alerts'}</p>
                </div>
              </div>

              {/* Recent alerts */}
              {summary?.alerts?.length > 0 && (
                <div className="space-y-1">
                  {summary.alerts.slice(0, 2).map((alert, idx) => (
                    <div
                      key={idx}
                      className={`text-xs px-2 py-1 rounded flex items-center justify-between ${
                        alert.flags === 'HIGH' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'
                      }`}
                    >
                      <span className="truncate">{alert.test_name}</span>
                      {alert.values_available && (
                        <span className="font-medium ml-2">
                          {alert.value} {alert.unit}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Last activity */}
              {member.last_activity && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {isRomanian ? 'Ultima activitate' : 'Last activity'}
                  </span>
                  <span>{new Date(member.last_activity).toLocaleDateString()}</span>
                </div>
              )}

              {/* View button */}
              <div className="mt-3 flex items-center justify-center gap-2 text-sm text-purple-600 font-medium">
                <Eye className="w-4 h-4" />
                {member.is_current_user
                  ? (isRomanian ? 'Vezi datele tale' : 'View your data')
                  : (isRomanian ? 'Vezi detalii' : 'View details')
                }
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
