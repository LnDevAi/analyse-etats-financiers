"use client";

import { useState } from "react";
import Link from "next/link";
import { forgotPassword } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch {
      setError("Une erreur est survenue. Veuillez réessayer.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-navy-950">E-DÉFENCE</h1>
          <p className="text-slate-500 text-sm mt-1">Analyse Financière IA — SYSCOHADA</p>
        </div>

        <div className="card">
          {sent ? (
            <div className="text-center py-6">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-navy-950 mb-2">Email envoyé</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Si votre adresse email est connue, vous recevrez un lien de réinitialisation
                dans les prochaines minutes. Vérifiez également vos spams.
              </p>
              <p className="text-slate-500 text-xs mt-4">Le lien expire dans 30 minutes.</p>
              <Link
                href="/auth/login"
                className="mt-6 inline-block text-navy-950 text-sm font-medium underline underline-offset-2"
              >
                Retour à la connexion
              </Link>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-navy-950 mb-1">Mot de passe oublié</h2>
              <p className="text-slate-500 text-sm mb-6">
                Saisissez votre adresse email pour recevoir un lien de réinitialisation.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Adresse email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="vous@cabinet.com"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-950"
                  />
                </div>

                {error && (
                  <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading || !email}
                  className="btn-primary w-full"
                >
                  {loading ? "Envoi en cours…" : "Envoyer le lien de réinitialisation"}
                </button>
              </form>

              <div className="mt-4 text-center">
                <Link href="/auth/login" className="text-sm text-slate-500 hover:text-navy-950">
                  ← Retour à la connexion
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
