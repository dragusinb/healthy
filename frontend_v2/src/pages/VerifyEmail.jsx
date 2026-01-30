import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/client';
import { CheckCircle, XCircle, Loader2, Mail } from 'lucide-react';

const VerifyEmail = () => {
    const { t } = useTranslation();
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState('verifying'); // verifying, success, error
    const [message, setMessage] = useState('');

    useEffect(() => {
        const token = searchParams.get('token');
        if (!token) {
            setStatus('error');
            setMessage(t('auth.invalidVerificationLink') || 'Invalid verification link');
            return;
        }

        verifyEmail(token);
    }, [searchParams]);

    const verifyEmail = async (token) => {
        try {
            const response = await api.post('/auth/verify-email', { token });
            setStatus('success');
            setMessage(response.data.message);
        } catch (error) {
            setStatus('error');
            setMessage(error.response?.data?.detail || t('auth.verificationFailed') || 'Verification failed');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
                {status === 'verifying' && (
                    <>
                        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-800 mb-2">
                            {t('auth.verifyingEmail') || 'Verifying your email...'}
                        </h1>
                        <p className="text-slate-500">
                            {t('auth.pleaseWait') || 'Please wait'}
                        </p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle className="w-8 h-8 text-teal-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-800 mb-2">
                            {t('auth.emailVerified') || 'Email Verified!'}
                        </h1>
                        <p className="text-slate-500 mb-6">
                            {t('auth.emailVerifiedDesc') || 'Your email has been verified successfully. You can now use all features.'}
                        </p>
                        <Link
                            to="/login"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
                        >
                            {t('auth.goToLogin') || 'Go to Login'}
                        </Link>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <XCircle className="w-8 h-8 text-rose-600" />
                        </div>
                        <h1 className="text-2xl font-bold text-slate-800 mb-2">
                            {t('auth.verificationFailed') || 'Verification Failed'}
                        </h1>
                        <p className="text-slate-500 mb-6">{message}</p>
                        <div className="space-y-3">
                            <Link
                                to="/login"
                                className="block w-full px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
                            >
                                {t('auth.goToLogin') || 'Go to Login'}
                            </Link>
                            <p className="text-sm text-slate-400">
                                {t('auth.needNewLink') || 'Need a new verification link? Login and request one from your profile.'}
                            </p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default VerifyEmail;
