import { useThemeStore } from "@/store/theme-store";
import es from "./es.json";
import en from "./en.json";
import pt from "./pt.json";

const translations: Record<string, Record<string, string>> = { es, en, pt };

export function t(key: string): string {
  const lang = useThemeStore.getState().language;
  return translations[lang]?.[key] || translations["es"]?.[key] || key;
}

export function useTranslation(): (key: string) => string {
  return t;
}
