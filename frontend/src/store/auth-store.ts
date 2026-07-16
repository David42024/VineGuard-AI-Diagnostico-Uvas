import { create } from "zustand";
import { User } from "@/lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  role: "admin" | "client" | null;
  setUser: (user: User) => void;
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  role: null,
  setUser: (user: User) =>
    set({ user, isAuthenticated: true, role: user.role }),
  login: (user: User) =>
    set({ user, isAuthenticated: true, role: user.role }),
  logout: () =>
    set({ user: null, isAuthenticated: false, role: null }),
}));
