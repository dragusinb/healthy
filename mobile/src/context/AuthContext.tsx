import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { TOKEN_KEY, USER_KEY, setToken, removeToken, setUser, removeUser, getToken, getUser } from '../api/client';

// Types
interface User {
  id: number;
  email: string;
  is_admin?: boolean;
  linked_accounts?: any[];
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  recovery_key?: string;
  needs_password_setup?: boolean;
  needs_vault_unlock?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResponse>;
  register: (email: string, password: string, acceptedTerms?: boolean) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await getToken();
      if (token) {
        // Verify token is still valid
        const response = await api.get('/users/me');
        const userData = {
          ...response.data,
          is_admin: response.data.is_admin || false,
        };
        setUserState(userData);
        await setUser(userData);
      } else {
        setUserState(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // Token invalid, clear it
      await removeToken();
      await removeUser();
      setUserState(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<LoginResponse> => {
    // Create form data for OAuth2 password flow
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post<LoginResponse>('/auth/token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    const { access_token, recovery_key } = response.data;

    // Store token
    await setToken(access_token);

    // Fetch and store user data
    const userResponse = await api.get('/users/me');
    const userData = {
      ...userResponse.data,
      is_admin: userResponse.data.is_admin || false,
    };
    setUserState(userData);
    await setUser(userData);

    return response.data;
  };

  const register = async (
    email: string,
    password: string,
    acceptedTerms: boolean = false
  ): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/register', {
      email,
      password,
      accepted_terms: acceptedTerms,
      terms_version: '1.0',
      privacy_version: '1.0',
    });

    const { access_token } = response.data;

    // Store token
    await setToken(access_token);

    // Fetch and store user data
    const userResponse = await api.get('/users/me');
    const userData = {
      ...userResponse.data,
      is_admin: userResponse.data.is_admin || false,
    };
    setUserState(userData);
    await setUser(userData);

    return response.data;
  };

  const logout = async () => {
    await removeToken();
    await removeUser();
    setUserState(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
