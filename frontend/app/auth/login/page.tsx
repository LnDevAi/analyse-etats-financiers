"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { Shield, Eye, EyeOff, Lock } from "lucide-react";
import { login, verifyMfa, getMe } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

interface LoginForm {
  email: string;
  password: string;
}

interface MFAForm {
  totp_code: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [tempToken, setTempToken] = useState("");
  const [userEmail, setUserEmail] = useState("");

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();
  const mfaForm = useForm<MFAForm>();

  const onLogin = async (data: LoginForm) => {
    setLoading(true);
    try {
      const res = await login(data.email, data.password);
      const body = res.data;

      if (body.requires_mfa) {
        setMfaRequired(true);
        setTempToken(body.temp_token);
        setUserEmail(data.email);
        return;
      }

      localStorage.setItem("access_token", body.access_token);
      localStorage.setItem("refresh_token", body.refresh_token);
      const meRes = await getMe();
      setAuth(meRes.data, body.access_token);
      toast.success("Connexion réussie");
      router.replace("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Identifiants incorrects");
    } finally {
      setLoading(false);
    }
  };

  const onMfaVerify = async (data: MFAForm) => {
    setLoading(true);
    try {
      const res = await verifyMfa(userEmail, data.totp_code, tempToken);
      const body = res.data;
      localStorage.setItem("access_token", body.access_token);
      const meRes = await getMe();
      setAuth(meRes.data, body.access_token);
      toast.success("Authentification MFA réussie");
      router.replace("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Code MFA invalide");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1e293b] rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#1e293b]">E-DÉFENCE</h1>
          <p className="text-gray-500 text-sm mt-1">Analyse Financière & Audit IA — UEMOA</p>
        </div>

        <div className="card">
          {!mfaRequired ? (
            <>
              <h2 className="text-lg font-semibold text-[#1e293b] mb-6">Connexion sécurisée</h2>
              <form onSubmit={handleSubmit(onLogin)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    {...register("email", { required: "Email requis" })}
                    type="email"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b] focus:border-transparent"
                    placeholder="vous@cabinet.com"
                  />
                  {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
                  <div className="relative">
                    <input
                      {...register("password", { required: "Mot de passe requis" })}
                      type={showPassword ? "text" : "password"}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary py-2.5 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  ) : (
                    <><Lock className="w-4 h-4" /> Se connecter</>
                  )}
                </button>
              </form>

              <p className="text-center text-xs text-gray-400 mt-4">
                Pas encore inscrit ?{" "}
                <a href="/auth/register" className="text-[#1e293b] font-medium hover:underline">
                  Créer un compte cabinet
                </a>
              </p>
            </>
          ) : (
            <>
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-50 rounded-xl mb-3">
                  <Shield className="w-6 h-6 text-[#1e293b]" />
                </div>
                <h2 className="text-lg font-semibold text-[#1e293b]">Vérification MFA</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Entrez le code de votre application d'authentification
                </p>
              </div>
              <form onSubmit={mfaForm.handleSubmit(onMfaVerify)} className="space-y-4">
                <input
                  {...mfaForm.register("totp_code", { required: true, minLength: 6, maxLength: 6 })}
                  type="text"
                  inputMode="numeric"
                  className="w-full border border-gray-200 rounded-lg px-3 py-3 text-center text-2xl tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                  placeholder="000000"
                  maxLength={6}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary py-2.5"
                >
                  {loading ? "Vérification..." : "Vérifier"}
                </button>
                <button
                  type="button"
                  onClick={() => setMfaRequired(false)}
                  className="w-full text-sm text-gray-500 hover:text-gray-700"
                >
                  ← Retour
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          E-DÉFENCE SaaS V4 — Confidentiel | © 2026 Tous droits réservés
        </p>
      </div>
    </div>
  );
}
