import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api, { VAULT_LOCKED_EVENT } from '../api/client';

const AuthContext = createContext();

// Google OAuth configuration
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [googleLoaded, setGoogleLoaded] = useState(false);

    // Google OAuth flow state
    const [pendingGoogleSetup, setPendingGoogleSetup] = useState(null); // {needs_password_setup, needs_vault_unlock}

    // Vault locked state - triggers unlock modal on 503 errors
    const [vaultLocked, setVaultLocked] = useState(false);

    useEffect(() => {
        checkUser();
        loadGoogleScript();

        // Listen for vault locked events from API client
        const handleVaultLocked = () => {
            // Only trigger if user is logged in
            if (sessionStorage.getItem('token')) {
                setVaultLocked(true);
            }
        };
        window.addEventListener(VAULT_LOCKED_EVENT, handleVaultLocked);
        return () => window.removeEventListener(VAULT_LOCKED_EVENT, handleVaultLocked);
    }, []);

    const loadGoogleScript = () => {
        if (!GOOGLE_CLIENT_ID) {
            console.warn('Google Client ID not configured');
            return;
        }

        // Check if already loaded
        if (window.google?.accounts) {
            setGoogleLoaded(true);
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => setGoogleLoaded(true);
        document.body.appendChild(script);
    };

    const checkUser = async () => {
        const token = sessionStorage.getItem('token');
        if (token) {
            try {
                const res = await api.get('/users/me');
                // Ensure is_admin is included
                setUser({
                    ...res.data,
                    is_admin: res.data.is_admin || false
                });
            } catch (e) {
                sessionStorage.removeItem('token');
                setUser(null);
            }
        }
        setLoading(false);
    };

    const login = async (email, password) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const res = await api.post('/auth/token', formData);
        sessionStorage.setItem('token', res.data.access_token);
        await checkUser();
        // Return response data so caller can check for recovery_key (legacy user migration)
        return res.data;
    };

    const register = async (email, password, acceptedTerms = false) => {
        const res = await api.post('/auth/register', {
            email,
            password,
            accepted_terms: acceptedTerms,
            terms_version: '1.0',
            privacy_version: '1.0'
        });
        // If registration_pending, email already exists - return generic message without login
        if (res.data.registration_pending) {
            return res.data;
        }
        sessionStorage.setItem('token', res.data.access_token);
        await checkUser();
        // Return the response so caller can access recovery_key
        return res.data;
    };

    const loginWithGoogle = useCallback(() => {
        return new Promise((resolve, reject) => {
            if (!GOOGLE_CLIENT_ID) {
                reject(new Error('Google Sign-In not configured. Please add VITE_GOOGLE_CLIENT_ID to your .env file.'));
                return;
            }

            if (!googleLoaded || !window.google?.accounts) {
                reject(new Error('Google Sign-In is still loading. Please try again.'));
                return;
            }

            try {
                const client = window.google.accounts.oauth2.initTokenClient({
                    client_id: GOOGLE_CLIENT_ID,
                    scope: 'email profile',
                    callback: async (response) => {
                        if (response.error) {
                            reject(new Error(response.error));
                            return;
                        }

                        try {
                            // Send the access token to our backend
                            const res = await api.post('/auth/google', {
                                access_token: response.access_token
                            });
                            sessionStorage.setItem('token', res.data.access_token);

                            // Check if user needs to complete setup or unlock data
                            if (res.data.needs_password_setup) {
                                // New Google user - needs to set password
                                setPendingGoogleSetup({ type: 'setup_password' });
                                await checkUser();
                                resolve({ needsSetup: true });
                            } else if (res.data.needs_vault_unlock) {
                                // Returning Google user - needs to unlock data
                                setPendingGoogleSetup({ type: 'unlock_data' });
                                await checkUser();
                                resolve({ needsUnlock: true });
                            } else {
                                // No encryption setup (shouldn't happen with new flow)
                                await checkUser();
                                resolve({});
                            }
                        } catch (err) {
                            reject(new Error(err.response?.data?.detail || 'Google authentication failed'));
                        }
                    },
                });

                client.requestAccessToken();
            } catch (err) {
                reject(new Error('Failed to initialize Google Sign-In'));
            }
        });
    }, [googleLoaded]);

    const setupPassword = async (password) => {
        const res = await api.post('/auth/setup-password', { password });
        setPendingGoogleSetup(null);
        return res.data; // Contains recovery_key
    };

    const unlockData = async (password) => {
        await api.post('/auth/unlock-data', { password });
        setPendingGoogleSetup(null);
        setVaultLocked(false);
    };

    // Unlock vault when session was lost (e.g., server restart)
    const unlockVault = async (password) => {
        await api.post('/auth/unlock-data', { password });
        setVaultLocked(false);
    };

    const triggerVaultUnlock = () => {
        setVaultLocked(true);
    };

    const dismissVaultUnlock = () => {
        setVaultLocked(false);
    };

    const clearPendingSetup = () => {
        setPendingGoogleSetup(null);
    };

    const logout = () => {
        sessionStorage.removeItem('token');
        setUser(null);
    };

    // Show a global loading spinner while the initial auth check is in progress.
    // This prevents a white flash before the app knows if the user is logged in.
    if (loading) {
        return (
            <AuthContext.Provider value={{
                user: null, login, register, loginWithGoogle, logout, loading: true,
                pendingGoogleSetup, setupPassword, unlockData, clearPendingSetup,
                vaultLocked, unlockVault, triggerVaultUnlock, dismissVaultUnlock
            }}>
                <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-3" />
                    </div>
                </div>
            </AuthContext.Provider>
        );
    }

    return (
        <AuthContext.Provider value={{
            user,
            login,
            register,
            loginWithGoogle,
            logout,
            loading,
            // Google OAuth flow
            pendingGoogleSetup,
            setupPassword,
            unlockData,
            clearPendingSetup,
            // Vault session recovery
            vaultLocked,
            unlockVault,
            triggerVaultUnlock,
            dismissVaultUnlock
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
