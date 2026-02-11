import React, { createContext, useContext, useState, useEffect } from "react";
import { AutoInternClient, TokenResponse, UserResponse } from "@autointern/client";

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  register: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  apiClient: AutoInternClient;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children, apiClient }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load user on mount if authenticated
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (apiClient.isAuthenticated()) {
          const currentUser = await apiClient.getCurrentUser();
          setUser(currentUser);
        }
      } catch (err: any) {
        console.error("Failed to load user:", err);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, [apiClient]);

  const register = async (email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      const userData = await apiClient.register({ email, password });
      setUser(userData);
    } catch (err: any) {
      const errorMsg = err.detail || "Registration failed";
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      await apiClient.login({ email, password });
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch (err: any) {
      const errorMsg = err.detail || "Login failed";
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      await apiClient.logout();
      setUser(null);
    } catch (err: any) {
      console.error("Logout error:", err);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    register,
    login,
    logout,
    error,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
