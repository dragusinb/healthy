import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext();

// Google OAuth configuration
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [googleLoaded, setGoogleLoaded] = useState(false);

    useEffect(() => {
        checkUser();
        loadGoogleScript();
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
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const res = await api.get('/users/me');
                setUser(res.data);
            } catch (e) {
                localStorage.removeItem('token');
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
        localStorage.setItem('token', res.data.access_token);
        await checkUser();
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
                            localStorage.setItem('token', res.data.access_token);
                            await checkUser();
                            resolve();
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

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, loginWithGoogle, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
