"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    _hasHydrated: boolean;
    setUser: (user: User | null) => void;
    setTokens: (accessToken: string, refreshToken: string) => void;
    clearAuth: () => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    logout: () => void;
    setHasHydrated: (has: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            _hasHydrated: false,

            setUser: (user) => set({ user, isAuthenticated: !!user }),
            setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken, isAuthenticated: true }),
            clearAuth: () => set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false, error: null }),
            setLoading: (isLoading) => set({ isLoading }),
            setError: (error) => set({ error }),
            logout: () => set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false, error: null }),
            setHasHydrated: (has) => set({ _hasHydrated: has }),
        }),
        {
            name: "auth-store",
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated(true);
            },
        }
    )
);
