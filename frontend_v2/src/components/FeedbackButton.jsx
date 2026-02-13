import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { MessageSquare, X, Camera, Send, Loader2, CheckCircle, ExternalLink } from 'lucide-react';
import api from '../api/client';

export default function FeedbackButton() {
    const { t } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const [description, setDescription] = useState('');
    const [screenshot, setScreenshot] = useState(null);
    const [screenshotPreview, setScreenshotPreview] = useState(null);
    const [isCapturing, setIsCapturing] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState(null);

    const pageUrl = window.location.href;

    const loadHtml2Canvas = () => {
        return new Promise((resolve, reject) => {
            if (typeof window.html2canvas === 'function') {
                resolve(window.html2canvas);
                return;
            }

            // Try to load dynamically if not already loaded
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            script.onload = () => {
                if (typeof window.html2canvas === 'function') {
                    resolve(window.html2canvas);
                } else {
                    reject(new Error('html2canvas failed to initialize'));
                }
            };
            script.onerror = () => reject(new Error('Failed to load html2canvas'));
            document.head.appendChild(script);
        });
    };

    const captureScreenshot = async () => {
        setIsCapturing(true);
        setError(null);

        const feedbackModal = document.getElementById('feedback-modal');
        const backdrop = feedbackModal?.parentElement;

        try {
            // Hide the entire modal overlay temporarily
            if (backdrop) backdrop.style.visibility = 'hidden';

            // Wait for DOM to update
            await new Promise(resolve => setTimeout(resolve, 200));

            // Load html2canvas
            const html2canvas = await loadHtml2Canvas();

            // Capture the main content area instead of body for better results
            const mainContent = document.querySelector('main') || document.body;

            const canvas = await html2canvas(mainContent, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                scale: window.devicePixelRatio > 1 ? 0.5 : 0.8,
                backgroundColor: '#f8fafc',
                removeContainer: true,
                ignoreElements: (element) => {
                    // Ignore problematic elements
                    const tag = element.tagName?.toLowerCase();
                    return tag === 'iframe' ||
                           tag === 'video' ||
                           tag === 'canvas' ||
                           element.id === 'feedback-modal' ||
                           element.classList?.contains('fixed');
                }
            });

            // Convert to base64 with compression
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            setScreenshot(dataUrl);
            setScreenshotPreview(dataUrl);

        } catch (err) {
            console.error('Screenshot capture failed:', err);
            setError(t('feedback.screenshotFailed') + ' (' + err.message + ')');
        } finally {
            // Always show modal again
            if (backdrop) backdrop.style.visibility = '';
            setIsCapturing(false);
        }
    };

    const handleSubmit = async () => {
        if (!description.trim()) {
            setError(t('feedback.descriptionRequired'));
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            await api.post('/support/snapshot', {
                description: description.trim(),
                page_url: pageUrl,
                screenshot: screenshot
            });

            setSubmitted(true);

            // Reset after showing success
            setTimeout(() => {
                setIsOpen(false);
                setDescription('');
                setScreenshot(null);
                setScreenshotPreview(null);
                setSubmitted(false);
            }, 2000);

        } catch (err) {
            console.error('Submit feedback failed:', err);
            setError(t('feedback.submitFailed'));
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        setIsOpen(false);
        setDescription('');
        setScreenshot(null);
        setScreenshotPreview(null);
        setError(null);
        setSubmitted(false);
    };

    const removeScreenshot = () => {
        setScreenshot(null);
        setScreenshotPreview(null);
    };

    return (
        <>
            {/* Floating Feedback Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center group"
                title={t('feedback.buttonTitle')}
            >
                <MessageSquare size={24} className="group-hover:scale-110 transition-transform" />
            </button>

            {/* Feedback Modal */}
            {isOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div
                        id="feedback-modal"
                        className="bg-white rounded-2xl shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in duration-300"
                    >
                        {/* Header */}
                        <div className="bg-primary-600 px-6 py-5 text-white flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <MessageSquare size={24} />
                                <h2 className="text-xl font-bold">{t('feedback.title')}</h2>
                            </div>
                            <button
                                onClick={handleClose}
                                className="p-2 hover:bg-white/20 rounded-full transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6">
                            {submitted ? (
                                <div className="text-center py-8">
                                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <CheckCircle size={32} className="text-green-600" />
                                    </div>
                                    <h3 className="text-xl font-semibold text-gray-800 mb-2">
                                        {t('feedback.thankYou')}
                                    </h3>
                                    <p className="text-gray-500 mb-4">{t('feedback.submitted')}</p>
                                    <Link
                                        to="/support"
                                        onClick={handleClose}
                                        className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 font-medium"
                                    >
                                        {t('feedback.viewTickets')}
                                        <ExternalLink size={16} />
                                    </Link>
                                </div>
                            ) : (
                                <>
                                    {/* Page URL Display */}
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-600 mb-1">
                                            {t('feedback.page')}
                                        </label>
                                        <div className="px-3 py-2 bg-gray-50 rounded-lg text-sm text-gray-500 truncate">
                                            {pageUrl}
                                        </div>
                                    </div>

                                    {/* Description */}
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-600 mb-1">
                                            {t('feedback.description')} *
                                        </label>
                                        <textarea
                                            value={description}
                                            onChange={(e) => setDescription(e.target.value)}
                                            rows={4}
                                            className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                                            placeholder={t('feedback.descriptionPlaceholder')}
                                        />
                                    </div>

                                    {/* Screenshot Section */}
                                    <div className="mb-4">
                                        <label className="block text-sm font-medium text-gray-600 mb-2">
                                            {t('feedback.screenshot')}
                                        </label>

                                        {screenshotPreview ? (
                                            <div className="relative">
                                                <img
                                                    src={screenshotPreview}
                                                    alt="Screenshot"
                                                    className="w-full h-40 object-cover rounded-lg border border-gray-200"
                                                />
                                                <button
                                                    onClick={removeScreenshot}
                                                    className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={captureScreenshot}
                                                disabled={isCapturing}
                                                className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-200 rounded-lg text-gray-500 hover:border-primary-300 hover:text-primary-600 transition-colors disabled:opacity-50"
                                            >
                                                {isCapturing ? (
                                                    <>
                                                        <Loader2 size={20} className="animate-spin" />
                                                        {t('feedback.capturing')}
                                                    </>
                                                ) : (
                                                    <>
                                                        <Camera size={20} />
                                                        {t('feedback.captureScreenshot')}
                                                    </>
                                                )}
                                            </button>
                                        )}
                                    </div>

                                    {/* Error Message */}
                                    {error && (
                                        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                            {error}
                                        </div>
                                    )}

                                    {/* Actions */}
                                    <div className="flex gap-3">
                                        <button
                                            onClick={handleClose}
                                            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors font-medium"
                                        >
                                            {t('common.cancel')}
                                        </button>
                                        <button
                                            onClick={handleSubmit}
                                            disabled={isSubmitting || !description.trim()}
                                            className="flex-1 px-4 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isSubmitting ? (
                                                <>
                                                    <Loader2 size={18} className="animate-spin" />
                                                    {t('feedback.sending')}
                                                </>
                                            ) : (
                                                <>
                                                    <Send size={18} />
                                                    {t('feedback.send')}
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
