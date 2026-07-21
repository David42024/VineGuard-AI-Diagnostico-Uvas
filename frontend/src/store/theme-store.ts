import { create } from "zustand";

interface ThemeState {
  language: "es" | "en" | "pt";
  sidebarCollapsed: boolean;
  setLanguage: (lang: "es" | "en" | "pt") => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

// Obtener estado inicial de localStorage
const getInitialState = (): Partial<ThemeState> => {
  if (typeof window === "undefined") return {};
  const saved = localStorage.getItem("themeState");
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      return {};
    }
  }
  return {};
};

const initialState = getInitialState();

export const useThemeStore = create<ThemeState>((set, get) => {
  // Guardar estado en localStorage cada vez que cambie
  const saveState = () => {
    const state = get();
    localStorage.setItem("themeState", JSON.stringify({
      language: state.language,
      sidebarCollapsed: state.sidebarCollapsed
    }));
  };

  return {
    language: (initialState.language as "es" | "en" | "pt") || "es",
    sidebarCollapsed: initialState.sidebarCollapsed ?? false,
    setLanguage: (language) => {
      set({ language });
      saveState();
    },
    toggleSidebar: () => {
      set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      saveState();
    },
    setSidebarCollapsed: (sidebarCollapsed) => {
      set({ sidebarCollapsed });
      saveState();
    },
  };
});
