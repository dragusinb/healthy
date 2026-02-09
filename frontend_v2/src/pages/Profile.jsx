import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import {
    User, Loader2, CheckCircle, AlertCircle,
    Calendar, Ruler, Scale, Droplets, Heart, Pill,
    Activity, Wine, Cigarette, AlertTriangle, Sparkles, Users
} from 'lucide-react';
import { cn } from '../lib/utils';

const ProfileField = ({ icon: Icon, label, children, className, htmlFor }) => (
    <div className={cn("space-y-2", className)}>
        <label htmlFor={htmlFor} className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Icon size={16} className="text-slate-400" aria-hidden="true" />
            {label}
        </label>
        {children}
    </div>
);

const Profile = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [scanStage, setScanStage] = useState(0);
    const [message, setMessage] = useState(null);
    const [multiPatientWarning, setMultiPatientWarning] = useState(null);
    const scanIntervalRef = useRef(null);

    // Cleanup scan interval on unmount
    useEffect(() => {
        return () => {
            if (scanIntervalRef.current) {
                clearInterval(scanIntervalRef.current);
            }
        };
    }, []);

    // Scan progress stages for user feedback
    const scanStages = [
        t('profile.scanStages.loading') || 'Loading documents...',
        t('profile.scanStages.reading') || 'Reading PDF content...',
        t('profile.scanStages.analyzing') || 'AI analyzing data...',
        t('profile.scanStages.extracting') || 'Extracting profile info...',
        t('profile.scanStages.matching') || 'Matching patient data...',
    ];
    const [profile, setProfile] = useState({
        full_name: '',
        date_of_birth: '',
        gender: '',
        height_cm: '',
        weight_kg: '',
        blood_type: '',
        allergies: [],
        chronic_conditions: [],
        current_medications: [],
        smoking_status: '',
        alcohol_consumption: '',
        physical_activity: ''
    });

    // For array fields (tags input)
    const [allergyInput, setAllergyInput] = useState('');
    const [conditionInput, setConditionInput] = useState('');
    const [medicationInput, setMedicationInput] = useState('');

    useEffect(() => {
        fetchProfile();
    }, []);

    // Auto-save with debounce
    useEffect(() => {
        // Skip auto-save during initial load
        if (loading) return;

        const timeoutId = setTimeout(() => {
            autoSave();
        }, 1000); // 1 second debounce

        return () => clearTimeout(timeoutId);
    }, [profile]);

    const autoSave = async () => {
        setSaving(true);
        setSaved(false);
        try {
            // Convert empty strings to null for numeric fields
            const profileData = {
                ...profile,
                height_cm: profile.height_cm === '' ? null : parseFloat(profile.height_cm) || null,
                weight_kg: profile.weight_kg === '' ? null : parseFloat(profile.weight_kg) || null,
            };
            await api.put('/users/profile', profileData);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (e) {
            console.error('Auto-save failed', e);
            setMessage({ type: 'error', text: t('profile.autoSaveFailed') || 'Auto-save failed' });
            setTimeout(() => setMessage(null), 3000);
        } finally {
            setSaving(false);
        }
    };

    // Helper to extract date in YYYY-MM-DD format from ISO datetime
    const formatDateForInput = (dateStr) => {
        if (!dateStr) return '';
        // Handle ISO datetime format "1984-09-27T00:00:00" or just "1984-09-27"
        return dateStr.split('T')[0];
    };

    const fetchProfile = async () => {
        try {
            const res = await api.get('/users/profile');
            setProfile({
                full_name: res.data.full_name || '',
                date_of_birth: formatDateForInput(res.data.date_of_birth),
                gender: res.data.gender || '',
                height_cm: res.data.height_cm || '',
                weight_kg: res.data.weight_kg || '',
                blood_type: res.data.blood_type || '',
                allergies: res.data.allergies || [],
                chronic_conditions: res.data.chronic_conditions || [],
                current_medications: res.data.current_medications || [],
                smoking_status: res.data.smoking_status || '',
                alcohol_consumption: res.data.alcohol_consumption || '',
                physical_activity: res.data.physical_activity || ''
            });
        } catch (e) {
            console.error('Failed to fetch profile', e);
            setMessage({ type: 'error', text: t('common.error') });
        } finally {
            setLoading(false);
        }
    };

    const handleScanFromDocuments = async () => {
        setScanning(true);
        setScanStage(0);
        setMessage(null);
        setMultiPatientWarning(null);

        // Cycle through stages to show progress
        scanIntervalRef.current = setInterval(() => {
            setScanStage(prev => (prev + 1) % scanStages.length);
        }, 2500); // Change stage every 2.5 seconds

        try {
            const res = await api.post('/users/scan-profile');
            if (scanIntervalRef.current) {
                clearInterval(scanIntervalRef.current);
                scanIntervalRef.current = null;
            }

            // Check for multi-patient warning
            if (res.data.multi_patient_warning) {
                setMultiPatientWarning({
                    patients: res.data.patients_found || [],
                    message: res.data.warning_message
                });
            }

            if (res.data.status === 'success') {
                // Update local profile state with new data
                setProfile(prev => ({
                    ...prev,
                    full_name: res.data.profile.full_name || prev.full_name,
                    date_of_birth: formatDateForInput(res.data.profile.date_of_birth) || prev.date_of_birth,
                    gender: res.data.profile.gender || prev.gender,
                }));
                setMessage({
                    type: 'success',
                    text: t('profile.scanSuccess') || `Found and updated: ${res.data.updates.join(', ')}`
                });
            } else if (res.data.status === 'no_new_data') {
                setMessage({
                    type: 'info',
                    text: t('profile.scanNoNewData') || 'No new profile data found (fields already filled or no data in documents)'
                });
            } else {
                setMessage({
                    type: 'info',
                    text: res.data.message || 'No profile data found in documents'
                });
            }
            setTimeout(() => setMessage(null), 5000);
        } catch (e) {
            if (scanIntervalRef.current) {
                clearInterval(scanIntervalRef.current);
                scanIntervalRef.current = null;
            }
            console.error('Failed to scan profile', e);
            setMessage({ type: 'error', text: e.response?.data?.detail || t('common.error') });
        } finally {
            setScanning(false);
            setScanStage(0);
        }
    };

    const addArrayItem = (field, value, setter) => {
        if (value.trim() && !profile[field].includes(value.trim())) {
            setProfile(prev => ({
                ...prev,
                [field]: [...prev[field], value.trim()]
            }));
            setter('');
        }
    };

    const removeArrayItem = (field, value) => {
        setProfile(prev => ({
            ...prev,
            [field]: prev[field].filter(item => item !== value)
        }));
    };

    const calculateBMI = () => {
        if (profile.height_cm && profile.weight_kg) {
            const height_m = profile.height_cm / 100;
            const bmi = profile.weight_kg / (height_m * height_m);
            return bmi.toFixed(1);
        }
        return null;
    };

    const getBMICategory = (bmi) => {
        if (bmi < 18.5) return { label: t('profile.bmiUnderweight') || 'Underweight', color: 'text-amber-600' };
        if (bmi < 25) return { label: t('profile.bmiNormal') || 'Normal', color: 'text-teal-600' };
        if (bmi < 30) return { label: t('profile.bmiOverweight') || 'Overweight', color: 'text-amber-600' };
        return { label: t('profile.bmiObese') || 'Obese', color: 'text-rose-600' };
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-primary-500" size={32} />
            </div>
        );
    }

    const bmi = calculateBMI();

    return (
        <div className="max-w-3xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-primary-100 rounded-xl">
                        <User size={24} className="text-primary-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800">{t('profile.title') || 'Your Profile'}</h1>
                        <p className="text-slate-500 text-sm">{t('profile.subtitle') || 'This information helps AI provide better health insights'}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {/* Auto-save status */}
                    <div className="flex items-center gap-1.5 text-sm">
                        {saving ? (
                            <>
                                <Loader2 size={14} className="animate-spin text-slate-400" />
                                <span className="text-slate-500">{t('profile.saving') || 'Saving...'}</span>
                            </>
                        ) : saved ? (
                            <>
                                <CheckCircle size={14} className="text-teal-500" />
                                <span className="text-teal-600">{t('profile.saved') || 'Saved'}</span>
                            </>
                        ) : null}
                    </div>
                    <button
                        onClick={handleScanFromDocuments}
                        disabled={scanning}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all min-w-[200px]",
                            scanning
                                ? "bg-violet-100 text-violet-600 cursor-wait"
                                : "bg-violet-100 text-violet-700 hover:bg-violet-200"
                        )}
                        title={t('profile.scanTooltip') || 'Scan your medical documents to auto-fill profile data'}
                    >
                        {scanning ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                        <span className={scanning ? "animate-pulse" : ""}>
                            {scanning ? scanStages[scanStage] : (t('profile.scanFromDocs') || 'Scan from Documents')}
                        </span>
                    </button>
                </div>
            </div>

            {/* Message */}
            {message && (
                <div className={cn(
                    "mb-6 p-4 rounded-xl flex items-center gap-3 border",
                    message.type === 'error' ? "bg-rose-50 border-rose-200 text-rose-700" :
                    message.type === 'info' ? "bg-blue-50 border-blue-200 text-blue-700" :
                    "bg-teal-50 border-teal-200 text-teal-700"
                )}>
                    {message.type === 'error' ? <AlertCircle size={20} /> :
                     message.type === 'info' ? <Sparkles size={20} /> :
                     <CheckCircle size={20} />}
                    {message.text}
                </div>
            )}

            {/* Multi-Patient Warning */}
            {multiPatientWarning && (
                <div className="mb-6 p-4 rounded-xl bg-amber-50 border-2 border-amber-300 shadow-sm">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-amber-100 rounded-lg shrink-0">
                            <Users size={20} className="text-amber-600" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-amber-800 mb-1">
                                {t('profile.multiPatientWarning') || 'Multiple Patients Detected'}
                            </h3>
                            <p className="text-amber-700 text-sm mb-3">
                                {t('profile.multiPatientDesc') || 'Your documents contain data for different patients. Make sure your profile reflects your own information.'}
                            </p>
                            <div className="flex flex-wrap gap-2">
                                <span className="text-xs text-amber-600 font-medium">
                                    {t('profile.patientsFound') || 'Patients found'}:
                                </span>
                                {multiPatientWarning.patients.map((name, i) => (
                                    <span
                                        key={i}
                                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full text-xs font-medium border border-amber-200"
                                    >
                                        <User size={10} />
                                        {name}
                                    </span>
                                ))}
                            </div>
                        </div>
                        <button
                            onClick={() => setMultiPatientWarning(null)}
                            className="p-1 hover:bg-amber-100 rounded-lg text-amber-600 transition-colors"
                        >
                            <AlertCircle size={16} />
                        </button>
                    </div>
                </div>
            )}

            <div className="space-y-6">
                {/* Basic Info Card */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">{t('profile.basicInfo') || 'Basic Information'}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <ProfileField icon={User} label={t('profile.fullName') || 'Full Name'} htmlFor="full_name">
                            <input
                                id="full_name"
                                type="text"
                                value={profile.full_name}
                                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                                className="input"
                                placeholder="John Doe"
                            />
                        </ProfileField>

                        <ProfileField icon={Calendar} label={t('profile.dateOfBirth') || 'Date of Birth'} htmlFor="date_of_birth">
                            <input
                                id="date_of_birth"
                                type="date"
                                value={profile.date_of_birth}
                                onChange={(e) => setProfile({ ...profile, date_of_birth: e.target.value })}
                                className="input"
                            />
                        </ProfileField>

                        <ProfileField icon={User} label={t('profile.gender') || 'Gender'} htmlFor="gender">
                            <select
                                id="gender"
                                value={profile.gender}
                                onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                                className="input"
                            >
                                <option value="">{t('profile.selectGender') || 'Select...'}</option>
                                <option value="male">{t('profile.male') || 'Male'}</option>
                                <option value="female">{t('profile.female') || 'Female'}</option>
                                <option value="other">{t('profile.other') || 'Other'}</option>
                            </select>
                        </ProfileField>

                        <ProfileField icon={Droplets} label={t('profile.bloodType') || 'Blood Type'} htmlFor="blood_type">
                            <select
                                id="blood_type"
                                value={profile.blood_type}
                                onChange={(e) => setProfile({ ...profile, blood_type: e.target.value })}
                                className="input"
                            >
                                <option value="">{t('profile.selectBloodType') || 'Select...'}</option>
                                <option value="A+">A+</option>
                                <option value="A-">A-</option>
                                <option value="B+">B+</option>
                                <option value="B-">B-</option>
                                <option value="AB+">AB+</option>
                                <option value="AB-">AB-</option>
                                <option value="O+">O+</option>
                                <option value="O-">O-</option>
                            </select>
                        </ProfileField>
                    </div>
                </div>

                {/* Body Measurements Card */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">{t('profile.bodyMeasurements') || 'Body Measurements'}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ProfileField icon={Ruler} label={t('profile.height') || 'Height (cm)'} htmlFor="height_cm">
                            <input
                                id="height_cm"
                                type="number"
                                value={profile.height_cm}
                                onChange={(e) => setProfile({ ...profile, height_cm: parseFloat(e.target.value) || '' })}
                                className="input"
                                placeholder="175"
                                min="50"
                                max="250"
                            />
                        </ProfileField>

                        <ProfileField icon={Scale} label={t('profile.weight') || 'Weight (kg)'} htmlFor="weight_kg">
                            <input
                                id="weight_kg"
                                type="number"
                                value={profile.weight_kg}
                                onChange={(e) => setProfile({ ...profile, weight_kg: parseFloat(e.target.value) || '' })}
                                className="input"
                                placeholder="70"
                                min="20"
                                max="500"
                            />
                        </ProfileField>

                        <ProfileField icon={Heart} label={t('profile.bmi') || 'BMI'}>
                            <div className="flex items-center gap-2 h-[42px] px-3 bg-slate-100 rounded-lg border border-slate-200">
                                {bmi ? (
                                    <>
                                        <span className="font-semibold text-slate-700">{bmi}</span>
                                        <span className={cn("text-sm", getBMICategory(parseFloat(bmi)).color)}>
                                            ({getBMICategory(parseFloat(bmi)).label})
                                        </span>
                                    </>
                                ) : (
                                    <span className="text-slate-400 text-sm">{t('profile.enterHeightWeight') || 'Enter height & weight'}</span>
                                )}
                            </div>
                        </ProfileField>
                    </div>
                </div>

                {/* Lifestyle Card */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">{t('profile.lifestyle') || 'Lifestyle'}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <ProfileField icon={Cigarette} label={t('profile.smoking') || 'Smoking'}>
                            <select
                                value={profile.smoking_status}
                                onChange={(e) => setProfile({ ...profile, smoking_status: e.target.value })}
                                className="input"
                            >
                                <option value="">{t('profile.select') || 'Select...'}</option>
                                <option value="never">{t('profile.smokingNever') || 'Never smoked'}</option>
                                <option value="former">{t('profile.smokingFormer') || 'Former smoker'}</option>
                                <option value="current">{t('profile.smokingCurrent') || 'Current smoker'}</option>
                            </select>
                        </ProfileField>

                        <ProfileField icon={Wine} label={t('profile.alcohol') || 'Alcohol'}>
                            <select
                                value={profile.alcohol_consumption}
                                onChange={(e) => setProfile({ ...profile, alcohol_consumption: e.target.value })}
                                className="input"
                            >
                                <option value="">{t('profile.select') || 'Select...'}</option>
                                <option value="none">{t('profile.alcoholNone') || 'None'}</option>
                                <option value="occasional">{t('profile.alcoholOccasional') || 'Occasional'}</option>
                                <option value="moderate">{t('profile.alcoholModerate') || 'Moderate'}</option>
                                <option value="heavy">{t('profile.alcoholHeavy') || 'Heavy'}</option>
                            </select>
                        </ProfileField>

                        <ProfileField icon={Activity} label={t('profile.physicalActivity') || 'Physical Activity'}>
                            <select
                                value={profile.physical_activity}
                                onChange={(e) => setProfile({ ...profile, physical_activity: e.target.value })}
                                className="input"
                            >
                                <option value="">{t('profile.select') || 'Select...'}</option>
                                <option value="sedentary">{t('profile.activitySedentary') || 'Sedentary'}</option>
                                <option value="light">{t('profile.activityLight') || 'Light (1-2 days/week)'}</option>
                                <option value="moderate">{t('profile.activityModerate') || 'Moderate (3-4 days/week)'}</option>
                                <option value="active">{t('profile.activityActive') || 'Active (5+ days/week)'}</option>
                                <option value="very_active">{t('profile.activityVeryActive') || 'Very Active (athlete)'}</option>
                            </select>
                        </ProfileField>
                    </div>
                </div>

                {/* Medical History Card */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">{t('profile.medicalHistory') || 'Medical History'}</h2>

                    {/* Allergies */}
                    <ProfileField icon={AlertTriangle} label={t('profile.allergies') || 'Allergies'} className="mb-4">
                        <div className="flex gap-2 mb-2">
                            <input
                                type="text"
                                value={allergyInput}
                                onChange={(e) => setAllergyInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addArrayItem('allergies', allergyInput, setAllergyInput))}
                                className="input flex-1"
                                placeholder={t('profile.allergiesPlaceholder') || 'Type and press Enter...'}
                            />
                            <button
                                type="button"
                                onClick={() => addArrayItem('allergies', allergyInput, setAllergyInput)}
                                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
                            >
                                {t('common.add') || 'Add'}
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {profile.allergies.map((allergy, i) => (
                                <span key={i} className="inline-flex items-center gap-1 px-3 py-1 bg-rose-50 text-rose-700 rounded-full text-sm border border-rose-200">
                                    {allergy}
                                    <button onClick={() => removeArrayItem('allergies', allergy)} className="hover:text-rose-900">×</button>
                                </span>
                            ))}
                        </div>
                    </ProfileField>

                    {/* Chronic Conditions */}
                    <ProfileField icon={Heart} label={t('profile.chronicConditions') || 'Chronic Conditions'} className="mb-4">
                        <div className="flex gap-2 mb-2">
                            <input
                                type="text"
                                value={conditionInput}
                                onChange={(e) => setConditionInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addArrayItem('chronic_conditions', conditionInput, setConditionInput))}
                                className="input flex-1"
                                placeholder={t('profile.conditionsPlaceholder') || 'Type and press Enter...'}
                            />
                            <button
                                type="button"
                                onClick={() => addArrayItem('chronic_conditions', conditionInput, setConditionInput)}
                                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
                            >
                                {t('common.add') || 'Add'}
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {profile.chronic_conditions.map((condition, i) => (
                                <span key={i} className="inline-flex items-center gap-1 px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-sm border border-amber-200">
                                    {condition}
                                    <button onClick={() => removeArrayItem('chronic_conditions', condition)} className="hover:text-amber-900">×</button>
                                </span>
                            ))}
                        </div>
                    </ProfileField>

                    {/* Current Medications */}
                    <ProfileField icon={Pill} label={t('profile.medications') || 'Current Medications'}>
                        <div className="flex gap-2 mb-2">
                            <input
                                type="text"
                                value={medicationInput}
                                onChange={(e) => setMedicationInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addArrayItem('current_medications', medicationInput, setMedicationInput))}
                                className="input flex-1"
                                placeholder={t('profile.medicationsPlaceholder') || 'Type and press Enter...'}
                            />
                            <button
                                type="button"
                                onClick={() => addArrayItem('current_medications', medicationInput, setMedicationInput)}
                                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
                            >
                                {t('common.add') || 'Add'}
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {profile.current_medications.map((med, i) => (
                                <span key={i} className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200">
                                    {med}
                                    <button onClick={() => removeArrayItem('current_medications', med)} className="hover:text-blue-900">×</button>
                                </span>
                            ))}
                        </div>
                    </ProfileField>
                </div>

                {/* Info Note */}
                <div className="flex items-start gap-3 p-4 bg-primary-50 rounded-xl text-sm text-primary-700 border border-primary-100">
                    <Heart size={20} className="shrink-0 mt-0.5" />
                    <p>
                        {t('profile.infoNote') || 'Your profile information is used by the AI to provide more personalized health insights. The more complete your profile, the better recommendations you\'ll receive.'}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Profile;
