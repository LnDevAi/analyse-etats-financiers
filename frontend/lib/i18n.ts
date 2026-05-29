import i18next from "i18next";
import { initReactI18next } from "react-i18next";

const STORAGE_KEY = "analyse_fin_lang";

const fr = {
  sidebar: {
    subtitle: "Analyse Financière IA",
    nav: {
      dashboard: "Tableau de bord",
      documents: "Documents",
      analysis: "Analyses IA",
      ag_analysis: "Analyse AG",
      cross_check: "Cross-Checking",
      crm: "CRM Clients",
      billing: "Facturation",
      users: "Équipe",
      subscription: "Mon abonnement",
    },
    logout: "Déconnexion",
    logout_success: "Déconnexion réussie",
  },
};

const en = {
  sidebar: {
    subtitle: "AI Financial Analysis",
    nav: {
      dashboard: "Dashboard",
      documents: "Documents",
      analysis: "AI Analyses",
      ag_analysis: "GA Analysis",
      cross_check: "Cross-Checking",
      crm: "CRM Clients",
      billing: "Billing",
      users: "Team",
      subscription: "My subscription",
    },
    logout: "Sign out",
    logout_success: "Successfully signed out",
  },
};

const savedLang =
  typeof window !== "undefined"
    ? (localStorage.getItem(STORAGE_KEY) ?? "fr")
    : "fr";

i18next.use(initReactI18next).init({
  lng: savedLang,
  fallbackLng: "fr",
  resources: { fr: { translation: fr }, en: { translation: en } },
  interpolation: { escapeValue: false },
});

export function toggleLang() {
  const next = i18next.language === "fr" ? "en" : "fr";
  i18next.changeLanguage(next);
  if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, next);
}

export function currentLang() {
  return i18next.language as "fr" | "en";
}

export default i18next;
