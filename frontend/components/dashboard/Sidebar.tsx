"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Shield, LayoutDashboard, FileText, BarChart3,
  Users, LogOut, GitCompare, ChevronRight,
  FolderOpen, Building2, CreditCard, Languages,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuthStore } from "@/lib/store";
import { logout } from "@/lib/api";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { toggleLang, currentLang } from "@/lib/i18n";
import { useState } from "react";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const { t, i18n } = useTranslation();
  const [lang, setLang] = useState<"fr" | "en">(currentLang());

  const navItems = [
    { href: "/dashboard", labelKey: "sidebar.nav.dashboard", icon: LayoutDashboard },
    { href: "/documents", labelKey: "sidebar.nav.documents", icon: FileText },
    { href: "/analysis", labelKey: "sidebar.nav.analysis", icon: BarChart3 },
    { href: "/ag-analysis", labelKey: "sidebar.nav.ag_analysis", icon: FolderOpen },
    { href: "/cross-check", labelKey: "sidebar.nav.cross_check", icon: GitCompare },
    { href: "/crm", labelKey: "sidebar.nav.crm", icon: Building2 },
    { href: "/billing", labelKey: "sidebar.nav.billing", icon: CreditCard },
    { href: "/users", labelKey: "sidebar.nav.users", icon: Users },
  ];

  const handleLogout = async () => {
    try {
      await logout();
    } catch {}
    clearAuth();
    toast.success(t("sidebar.logout_success"));
    router.replace("/auth/login");
  };

  const handleToggleLang = () => {
    toggleLang();
    setLang(currentLang());
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
            <p className="text-white/50 text-xs">{t("sidebar.subtitle")}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, labelKey, icon: Icon }) => {
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
              <span>{t(labelKey)}</span>
              {active && <ChevronRight className="w-3 h-3 ml-auto" />}
            </Link>
          );
        })}

        {/* Subscription link */}
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
            <span>{t("sidebar.nav.subscription")}</span>
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
          <button
            onClick={handleToggleLang}
            title="Toggle language"
            className="flex items-center gap-1 px-2 py-1 rounded text-white/50 hover:text-white hover:bg-white/10 text-xs transition-all"
          >
            <Languages className="w-3 h-3" />
            <span className="font-semibold">{lang === "fr" ? "EN" : "FR"}</span>
          </button>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-white/60 hover:bg-white/10 hover:text-white text-sm transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>{t("sidebar.logout")}</span>
        </button>
      </div>
    </aside>
  );
}
