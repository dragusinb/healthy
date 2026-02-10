import React, { createContext, useContext, useState, useRef, useCallback } from 'react';
import api from '../api/client';

const AnalysisContext = createContext(null);

// Analysis steps for Doctor AI
const HEALTH_ANALYSIS_STEPS = [
    { key: 'loading', duration: 800 },
    { key: 'analyzing', duration: 1500 },
    { key: 'general', duration: 4000 },
    { key: 'specialists', duration: 8000 },
    { key: 'compiling', duration: 3000 },
    { key: 'finishing', duration: 1500 },
];

export const AnalysisProvider = ({ children }) => {
    // Doctor AI (Health Reports) state
    const [healthAnalyzing, setHealthAnalyzing] = useState(false);
    const [healthStep, setHealthStep] = useState(0);
    const [healthError, setHealthError] = useState(null);
    const healthTimeoutRef = useRef(null);
    const healthPromiseRef = useRef(null);

    // Screenings state
    const [screeningsAnalyzing, setScreeningsAnalyzing] = useState(false);
    const [screeningsError, setScreeningsError] = useState(null);
    const screeningsPromiseRef = useRef(null);

    // Callbacks to notify components when analysis completes
    const healthCallbackRef = useRef(null);
    const screeningsCallbackRef = useRef(null);

    // Run health analysis step animation
    const runHealthSteps = useCallback(() => {
        let currentStep = 0;
        let cancelled = false;

        const runStep = () => {
            if (cancelled) return;
            if (currentStep < HEALTH_ANALYSIS_STEPS.length) {
                setHealthStep(currentStep);
                const delay = HEALTH_ANALYSIS_STEPS[currentStep].duration;
                currentStep++;
                healthTimeoutRef.current = setTimeout(runStep, delay);
            }
        };
        runStep();

        return () => {
            cancelled = true;
            if (healthTimeoutRef.current) {
                clearTimeout(healthTimeoutRef.current);
            }
        };
    }, []);

    // Start Doctor AI analysis
    const startHealthAnalysis = useCallback(async (onComplete) => {
        // If already analyzing, just register the callback
        if (healthAnalyzing && healthPromiseRef.current) {
            healthCallbackRef.current = onComplete;
            return healthPromiseRef.current;
        }

        setHealthAnalyzing(true);
        setHealthError(null);
        setHealthStep(0);
        healthCallbackRef.current = onComplete;

        // Start step animation
        const cancelSteps = runHealthSteps();

        // Start API call
        healthPromiseRef.current = api.post('/health/analyze')
            .then((result) => {
                cancelSteps();
                setHealthAnalyzing(false);
                setHealthStep(0);
                healthPromiseRef.current = null;
                if (healthCallbackRef.current) {
                    healthCallbackRef.current(null, result);
                }
                return result;
            })
            .catch((error) => {
                cancelSteps();
                setHealthAnalyzing(false);
                setHealthStep(0);
                const errorMsg = error.response?.data?.detail || "Analysis failed. Please try again.";
                setHealthError(errorMsg);
                healthPromiseRef.current = null;
                if (healthCallbackRef.current) {
                    healthCallbackRef.current(errorMsg, null);
                }
                throw error;
            });

        return healthPromiseRef.current;
    }, [healthAnalyzing, runHealthSteps]);

    // Start Screenings analysis
    const startScreeningsAnalysis = useCallback(async (onComplete) => {
        // If already analyzing, just register the callback
        if (screeningsAnalyzing && screeningsPromiseRef.current) {
            screeningsCallbackRef.current = onComplete;
            return screeningsPromiseRef.current;
        }

        setScreeningsAnalyzing(true);
        setScreeningsError(null);
        screeningsCallbackRef.current = onComplete;

        screeningsPromiseRef.current = api.post('/health/gap-analysis')
            .then((result) => {
                setScreeningsAnalyzing(false);
                screeningsPromiseRef.current = null;
                if (screeningsCallbackRef.current) {
                    screeningsCallbackRef.current(null, result);
                }
                return result;
            })
            .catch((error) => {
                setScreeningsAnalyzing(false);
                const errorMsg = error.response?.data?.detail || "Analysis failed. Please try again.";
                setScreeningsError(errorMsg);
                screeningsPromiseRef.current = null;
                if (screeningsCallbackRef.current) {
                    screeningsCallbackRef.current(errorMsg, null);
                }
                throw error;
            });

        return screeningsPromiseRef.current;
    }, [screeningsAnalyzing]);

    // Register callback for ongoing analysis (when returning to page)
    const registerHealthCallback = useCallback((callback) => {
        healthCallbackRef.current = callback;
    }, []);

    const registerScreeningsCallback = useCallback((callback) => {
        screeningsCallbackRef.current = callback;
    }, []);

    // Clear errors
    const clearHealthError = useCallback(() => setHealthError(null), []);
    const clearScreeningsError = useCallback(() => setScreeningsError(null), []);

    const value = {
        // Health Reports (Doctor AI)
        healthAnalyzing,
        healthStep,
        healthError,
        healthSteps: HEALTH_ANALYSIS_STEPS,
        startHealthAnalysis,
        registerHealthCallback,
        clearHealthError,

        // Screenings
        screeningsAnalyzing,
        screeningsError,
        startScreeningsAnalysis,
        registerScreeningsCallback,
        clearScreeningsError,
    };

    return (
        <AnalysisContext.Provider value={value}>
            {children}
        </AnalysisContext.Provider>
    );
};

export const useAnalysis = () => {
    const context = useContext(AnalysisContext);
    if (!context) {
        throw new Error('useAnalysis must be used within an AnalysisProvider');
    }
    return context;
};

export default AnalysisContext;
