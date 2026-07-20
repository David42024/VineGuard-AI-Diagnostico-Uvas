import { useThemeStore } from "@/store/theme-store";
import es from "./es.json";
import en from "./en.json";
import pt from "./pt.json";

const translations: Record<string, Record<string, string>> = { es, en, pt };

export function t(key: string, lang?: "es" | "en" | "pt"): string {
  const language = lang || useThemeStore.getState().language;
  return translations[language]?.[key] || translations["es"]?.[key] || key;
}

export function useTranslation() {
  const language = useThemeStore((state) => state.language);

  return function tWithLang(key: string): string {
    return translations[language]?.[key] || translations["es"]?.[key] || key;
  };
}
