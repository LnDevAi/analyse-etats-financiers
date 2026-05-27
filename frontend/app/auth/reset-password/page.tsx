"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { resetPassword } from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError("Lien de réinitialisation invalide ou manquant.");
    }
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      setSuccess(true);
      setTimeout(() => router.push("/auth/login"), 3000);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Lien invalide ou expiré. Veuillez recommencer.";
      setError(message);
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
          {success ? (
            <div className="text-center py-6">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-navy-950 mb-2">Mot de passe réinitialisé</h2>
              <p className="text-slate-600 text-sm">
                Votre mot de passe a été mis à jour avec succès.
                Vous allez être redirigé vers la page de connexion…
              </p>
              <Link
                href="/auth/login"
                className="mt-6 inline-block btn-primary text-sm px-6 py-2"
              >
                Se connecter
              </Link>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-semibold text-navy-950 mb-1">Nouveau mot de passe</h2>
              <p className="text-slate-500 text-sm mb-6">
                Choisissez un nouveau mot de passe sécurisé (8 caractères minimum).
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Nouveau mot de passe
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    placeholder="••••••••"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-950"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Confirmer le mot de passe
                  </label>
                  <input
                    type="password"
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-950"
                  />
                  {confirm && password !== confirm && (
                    <p className="text-red-500 text-xs mt-1">Les mots de passe ne correspondent pas.</p>
                  )}
                </div>

                {/* Indicateur de force */}
                {password && (
                  <div className="space-y-1">
                    <div className="flex gap-1">
                      {[8, 10, 12].map((len, i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full transition-colors ${
                            password.length >= len
                              ? i === 0 ? "bg-red-400" : i === 1 ? "bg-yellow-400" : "bg-green-500"
                              : "bg-slate-200"
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-slate-400">
                      {password.length < 8 ? "Trop court" : password.length < 10 ? "Faible" : password.length < 12 ? "Moyen" : "Fort"}
                    </p>
                  </div>
                )}

                {error && (
                  <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading || !token || password !== confirm}
                  className="btn-primary w-full"
                >
                  {loading ? "Enregistrement…" : "Enregistrer le nouveau mot de passe"}
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

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50 flex items-center justify-center"><p className="text-slate-500">Chargement…</p></div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
