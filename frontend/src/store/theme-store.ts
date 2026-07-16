import { create } from "zustand";

interface ThemeState {
  language: "es" | "en" | "pt";
  sidebarCollapsed: boolean;
  setLanguage: (lang: "es" | "en" | "pt") => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  language: "es",
  sidebarCollapsed: false,
  setLanguage: (language) => set({ language }),
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
}));
