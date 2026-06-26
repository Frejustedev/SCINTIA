import { fr } from "./fr";

/** Default locale. Planned: fr (default), ar (RTL), en. */
export const defaultLocale = "fr" as const;

const dictionaries = { fr };

export type Dictionary = typeof fr;

export function getDictionary(locale: string = defaultLocale): Dictionary {
  return dictionaries[locale as keyof typeof dictionaries] ?? fr;
}
