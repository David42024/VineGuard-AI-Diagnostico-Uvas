import { create } from "zustand";

interface ThemeState {
  language: "es" | "en" | "pt";
  sidebarCollapsed: boolean;
  setLanguage: (lang: "es" | "en" | "pt") => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  hydrate: () => void;
}

const STORAGE_KEY = "themeState";

// Persistencia sólo en cliente (nunca en SSR para evitar errores de hidratación)
function persistState(language: ThemeState["language"], sidebarCollapsed: boolean) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ language, sidebarCollapsed }));
  } catch {
    // Ignorar errores (modo privado, cuota llena, etc.)
  }
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  language: "es",
  sidebarCollapsed: false,
  setLanguage: (language) => {
    set({ language });
    persistState(language, get().sidebarCollapsed);
  },
  toggleSidebar: () => {
    const sidebarCollapsed = !get().sidebarCollapsed;
    set({ sidebarCollapsed });
    persistState(get().language, sidebarCollapsed);
  },
  setSidebarCollapsed: (sidebarCollapsed) => {
    set({ sidebarCollapsed });
    persistState(get().language, sidebarCollapsed);
  },
  // Se invoca únicamente tras el montaje en el cliente (ver StoreHydrator)
  hydrate: () => {
    if (typeof window === "undefined") return;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return;
      const parsed = JSON.parse(saved);
      set({
        language: (parsed.language as "es" | "en" | "pt") || "es",
        sidebarCollapsed: parsed.sidebarCollapsed ?? false,
      });
    } catch {
      // Ignorar almacenamiento corrupto
    }
  },
}));
