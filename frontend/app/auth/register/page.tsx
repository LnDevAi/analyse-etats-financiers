"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { Shield, Building2 } from "lucide-react";
import { registerTenant } from "@/lib/api";

interface RegisterForm {
  tenant_name: string;
  tenant_type: string;
  admin_full_name: string;
  admin_email: string;
  admin_password: string;
  confirm_password: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>();

  const onSubmit = async (data: RegisterForm) => {
    if (data.admin_password !== data.confirm_password) {
      toast.error("Les mots de passe ne correspondent pas");
      return;
    }
    setLoading(true);
    try {
      await registerTenant({
        tenant_name: data.tenant_name,
        tenant_type: data.tenant_type,
        admin_full_name: data.admin_full_name,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
      });
      toast.success("Inscription réussie ! Vous pouvez vous connecter.");
      router.push("/auth/login");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1e293b] rounded-2xl mb-4">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[#1e293b]">E-DÉFENCE — Inscription</h1>
          <p className="text-gray-500 text-sm mt-1">Créer votre espace cabinet / institution</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nom de l'organisation</label>
              <input
                {...register("tenant_name", { required: "Nom requis" })}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                placeholder="Cabinet XYZ & Associés"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type d'organisation</label>
              <select
                {...register("tenant_type")}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b] bg-white"
              >
                <option value="CABINET_EXPERTISE">Cabinet d'Expertise Comptable / Commissariat</option>
                <option value="ADMINISTRATION_FISCALE">Administration Fiscale</option>
                <option value="BANQUE">Banque / Établissement de Crédit</option>
              </select>
            </div>

            <hr className="border-gray-100" />
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Compte Administrateur</p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet</label>
                <input
                  {...register("admin_full_name", { required: true })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                  placeholder="Prénom Nom"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  {...register("admin_email", { required: true })}
                  type="email"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                  placeholder="admin@cabinet.com"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
                <input
                  {...register("admin_password", { required: true, minLength: 8 })}
                  type="password"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                  placeholder="Min. 8 caractères"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmer</label>
                <input
                  {...register("confirm_password", { required: true })}
                  type="password"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 mt-2"
            >
              {loading ? "Création en cours..." : "Créer mon espace"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            Déjà inscrit ?{" "}
            <a href="/auth/login" className="text-[#1e293b] font-medium hover:underline">
              Se connecter
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
