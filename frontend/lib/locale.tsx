"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Locale = "fr" | "en" | "ar";

export const LOCALES: Locale[] = ["fr", "en", "ar"];
const RTL_LOCALES: ReadonlySet<Locale> = new Set<Locale>(["ar"]);
const STORAGE_KEY = "scintia_locale";

// UI-chrome strings only. Clinical wording stays server-side (FR), where the
// no-invention rules apply; Arabic medical terminology must be reviewed by a
// professional before any clinical wording is localized.
type Entry = Record<Locale, string>;
const DICT: Record<string, Entry> = {
  "lang.label": { fr: "Langue", en: "Language", ar: "اللغة" },
  "login.title": { fr: "Connexion", en: "Sign in", ar: "تسجيل الدخول" },
  "login.title_bootstrap": {
    fr: "Créer le premier administrateur",
    en: "Create the first administrator",
    ar: "إنشاء المسؤول الأول",
  },
  "login.subtitle": {
    fr: "Aide à la décision en médecine nucléaire — accès réservé.",
    en: "Nuclear-medicine decision support — restricted access.",
    ar: "دعم القرار في الطب النووي — وصول مقيّد.",
  },
  "login.fullname": { fr: "Nom complet", en: "Full name", ar: "الاسم الكامل" },
  "login.email": { fr: "E-mail", en: "Email", ar: "البريد الإلكتروني" },
  "login.password": { fr: "Mot de passe", en: "Password", ar: "كلمة المرور" },
  "login.submit": { fr: "Se connecter", en: "Sign in", ar: "تسجيل الدخول" },
  "login.submit_bootstrap": {
    fr: "Créer et se connecter",
    en: "Create and sign in",
    ar: "إنشاء وتسجيل الدخول",
  },
  "login.busy": { fr: "Veuillez patienter…", en: "Please wait…", ar: "يرجى الانتظار…" },
  "login.to_bootstrap": {
    fr: "Première installation : créer un administrateur",
    en: "First run: create an administrator",
    ar: "أول تشغيل: إنشاء مسؤول",
  },
  "login.to_login": {
    fr: "← Revenir à la connexion",
    en: "← Back to sign in",
    ar: "← العودة إلى تسجيل الدخول",
  },
  "nav.viewer": { fr: "Visualiseur DICOM →", en: "DICOM viewer →", ar: "عارض DICOM →" },
  "viewer.title": { fr: "Visualiseur DICOM", en: "DICOM viewer", ar: "عارض DICOM" },
  "viewer.back": { fr: "← Résultats", en: "← Results", ar: "← النتائج" },
  "viewer.slice": { fr: "Coupe", en: "Slice", ar: "مقطع" },
  "viewer.window": { fr: "Fenêtre (W)", en: "Window (W)", ar: "النافذة (W)" },
  "viewer.level": { fr: "Niveau (L)", en: "Level (L)", ar: "المستوى (L)" },
  "common.loading": { fr: "Chargement…", en: "Loading…", ar: "جارٍ التحميل…" },
};

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: "fr",
  setLocale: () => undefined,
  t: (key) => DICT[key]?.fr ?? key,
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as Locale | null;
    if (stored && LOCALES.includes(stored)) setLocaleState(stored);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = RTL_LOCALES.has(locale) ? "rtl" : "ltr";
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const t = useCallback((key: string) => DICT[key]?.[locale] ?? DICT[key]?.fr ?? key, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useT(): (key: string) => string {
  return useContext(LocaleContext).t;
}

export function useLocale(): { locale: Locale; setLocale: (locale: Locale) => void } {
  const { locale, setLocale } = useContext(LocaleContext);
  return { locale, setLocale };
}
