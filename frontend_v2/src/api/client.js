import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Custom event for vault locked state
export const VAULT_LOCKED_EVENT = 'vault-locked';

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor - handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Only logout on 401 (Unauthorized = token invalid/expired)
        // Do NOT logout on 403 (Forbidden = authenticated but not authorized for this resource)
        if (error.response?.status === 401) {
            // Clear invalid token and redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            // Only redirect if not already on login page
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        // On 503 (vault locked), dispatch event to trigger unlock modal
        if (error.response?.status === 503) {
            window.dispatchEvent(new CustomEvent(VAULT_LOCKED_EVENT));
        }
        return Promise.reject(error);
    }
);

export default api;
