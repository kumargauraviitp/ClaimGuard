import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
  status: string;
  mfa_enabled: boolean;
  force_password_change: boolean;
  phone?: string;
  customer_id?: string;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: Tokens) => void;
  clearAuth: () => void;
  updateUser: (user: Partial<User>) => void;
  updateTokens: (tokens: Tokens) => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      
      setAuth: (user, tokens) => set({ user, tokens, isAuthenticated: true }),
      
      clearAuth: () => set({ user: null, tokens: null, isAuthenticated: false }),
      
      updateUser: (updatedFields) => set((state) => ({
        user: state.user ? { ...state.user, ...updatedFields } : null
      })),

      updateTokens: (tokens) => set({ tokens }),

      hasPermission: (permission) => {
        const state = get();
        if (!state.user) return false;
        return state.user.permissions.includes('*') || state.user.permissions.includes(permission);
      },

      hasRole: (role) => {
        const state = get();
        if (!state.user) return false;
        return state.user.roles.includes(role);
      }
    }),
    {
      name: 'auth-storage', // local storage key
    }
  )
);
