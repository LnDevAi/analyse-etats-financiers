import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import I18nProvider from "@/components/I18nProvider";

export const metadata: Metadata = {
  title: "E-DÉFENCE — Analyse Financière IA",
  description: "Plateforme SaaS d'audit et d'analyse des états financiers par IA — Zone UEMOA",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-base min-h-screen">
        <I18nProvider>
          {children}
        </I18nProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: { background: "#1e293b", color: "#fff", borderRadius: "8px" },
          }}
        />
      </body>
    </html>
  );
}

