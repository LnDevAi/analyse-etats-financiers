"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield, LayoutDashboard, FileText, BarChart3,
  Users, LogOut, GitCompare, ChevronRight,
  FolderOpen, Building2, CreditCard,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuthStore } from "@/lib/store";
import { logout } from "@/lib/api";
import toast from "react-hot-toast";

const navItems = [
  { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/analysis", label: "Analyses IA", icon: BarChart3 },
  { href: "/ag-analysis", label: "Analyse AG", icon: FolderOpen },
  { href: "/cross-check", label: "Cross-Checking", icon: GitCompare },
  { href: "/crm", label: "CRM Clients", icon: Building2 },
  { href: "/billing", label: "Facturation", icon: CreditCard },
  { href: "/users", label: "Équipe", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    try {
      await logout();
    } catch {}
    clearAuth();
    toast.success("Déconnexion réussie");
    router.replace("/auth/login");
  };

  return (
    <aside className="hidden md:flex w-64 bg-[#1e293b] min-h-screen flex-col fixed left-0 top-0 z-30">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/10 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-tight">E-DÉFENCE</p>
            <p className="text-white/50 text-xs">Analyse Financière IA</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                active
                  ? "bg-white/15 text-white"
                  : "text-white/60 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
              {active && <ChevronRight className="w-3 h-3 ml-auto" />}
            </Link>
          );
        })}

        {/* Portail client (séparateur) */}
        <div className="pt-3 mt-3 border-t border-white/5">
          <Link
            href="/account/billing"
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
              pathname.startsWith("/account/billing")
                ? "bg-white/15 text-white"
                : "text-white/40 hover:bg-white/10 hover:text-white/70"
            )}
          >
            <CreditCard className="w-4 h-4 flex-shrink-0" />
            <span>Mon abonnement</span>
          </Link>
        </div>
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <span className="text-white text-xs font-bold">
              {user?.full_name?.charAt(0).toUpperCase() || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-medium truncate">{user?.full_name}</p>
            <p className="text-white/50 text-xs truncate">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-white/60 hover:bg-white/10 hover:text-white text-sm transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Déconnexion</span>
        </button>
      </div>
    </aside>
  );
}
