"use client";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Users, Plus, Shield, User } from "lucide-react";
import toast from "react-hot-toast";
import { listUsers, createUser } from "@/lib/api";
import Sidebar from "@/components/dashboard/Sidebar";
import { useAuthStore } from "@/lib/store";

const ROLE_LABELS: Record<string, string> = {
  ASSOCIE: "Associé",
  CHEF_MISSION: "Chef de mission",
  AUDITEUR_JUNIOR: "Auditeur junior",
};

const ROLE_COLORS: Record<string, string> = {
  ASSOCIE: "bg-purple-100 text-purple-800",
  CHEF_MISSION: "bg-blue-100 text-blue-800",
  AUDITEUR_JUNIOR: "bg-gray-100 text-gray-700",
};

export default function UsersPage() {
  const { user: me } = useAuthStore();
  const [users, setUsers] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const { register, handleSubmit, reset } = useForm();

  const load = async () => {
    try {
      const res = await listUsers();
      setUsers(res.data);
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onCreate = async (data: any) => {
    try {
      await createUser(data);
      toast.success("Utilisateur créé");
      reset();
      setShowCreate(false);
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erreur création");
    }
  };

  const canCreate = me?.role === "ASSOCIE" || me?.role === "CHEF_MISSION";

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <main className="flex-1 ml-64 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b]">Équipe</h1>
            <p className="text-gray-500 text-sm mt-0.5">Gestion des utilisateurs de votre cabinet</p>
          </div>
          {canCreate && (
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" /> Ajouter un membre
            </button>
          )}
        </div>

        {showCreate && (
          <div className="card mb-6">
            <h3 className="text-sm font-semibold text-[#1e293b] mb-4">Nouvel utilisateur</h3>
            <form onSubmit={handleSubmit(onCreate)} className="grid grid-cols-4 gap-4">
              <input
                {...register("full_name", { required: true })}
                placeholder="Nom complet"
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
              />
              <input
                {...register("email", { required: true })}
                type="email"
                placeholder="Email"
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
              />
              <select
                {...register("role")}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
              >
                <option value="AUDITEUR_JUNIOR">Auditeur junior</option>
                <option value="CHEF_MISSION">Chef de mission</option>
                {me?.role === "ASSOCIE" && <option value="ASSOCIE">Associé</option>}
              </select>
              <div className="flex gap-2">
                <input
                  {...register("password", { required: true, minLength: 8 })}
                  type="password"
                  placeholder="Mot de passe"
                  className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e293b]"
                />
                <button type="submit" className="btn-primary px-4 text-sm">Créer</button>
              </div>
            </form>
          </div>
        )}

        <div className="card">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1e293b]" />
            </div>
          ) : (
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#1e293b]/10 rounded-full flex items-center justify-center">
                      <span className="text-[#1e293b] font-bold text-sm">
                        {u.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-[#1e293b] text-sm">{u.full_name}</p>
                        {u.id === me?.id && (
                          <span className="text-xs bg-[#1e293b] text-white px-1.5 py-0.5 rounded">Vous</span>
                        )}
                        {!u.is_active && (
                          <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">Inactif</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400">{u.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {u.mfa_enabled && (
                      <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-1 rounded-full">
                        <Shield className="w-3 h-3" /> MFA actif
                      </span>
                    )}
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${ROLE_COLORS[u.role] || "bg-gray-100"}`}>
                      {ROLE_LABELS[u.role] || u.role}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
