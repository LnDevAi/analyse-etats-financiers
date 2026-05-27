"use client";
import { useEffect, useState } from "react";
import {
  TrendingUp, CreditCard, AlertTriangle, Users,
  FileText, CheckCircle2, BarChart2,
} from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from "recharts";

interface DashboardData {
  mrr: number;
  arr: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  overdue_invoices: number;
  overdue_amount: number;
  revenue_by_month: { month: string; revenue: number; invoices_count: number }[];
  subscriptions_by_plan: Record<string, number>;
}

interface Invoice {
  id: string; invoice_number: string; status: string;
  total_amount: number; due_date: string; created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  PAID: "text-green-400",
  OVERDUE: "text-red-400",
  SENT: "text-blue-400",
  DRAFT: "text-gray-400",
  CANCELLED: "text-gray-400",
};

const PIE_COLORS = ["#3b82f6", "#22c55e", "#f97316", "#a855f7"];

export default function BillingDashboardPage() {
  const [dash, setDash] = useState<DashboardData | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  useEffect(() => {
    Promise.all([api.get("/billing/dashboard"), api.get("/billing/invoices")])
      .then(([dRes, iRes]) => { setDash(dRes.data); setInvoices(iRes.data); })
      .catch(() => toast.error("Erreur de chargement"));
  }, []);

  if (!dash) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" /></div>;

  const pieData = Object.entries(dash.subscriptions_by_plan).map(([name, count], i) => ({
    name, value: count, color: PIE_COLORS[i % PIE_COLORS.length],
  }));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard Facturation</h1>
        <p className="text-white/50 text-sm mt-1">Revenus, abonnements et paiements</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "MRR", value: `${dash.mrr.toLocaleString("fr-FR")} FCFA`, icon: TrendingUp, color: "text-blue-400" },
          { label: "ARR", value: `${dash.arr.toLocaleString("fr-FR")} FCFA`, icon: BarChart2, color: "text-purple-400" },
          { label: "Abonnements actifs", value: dash.active_subscriptions, icon: Users, color: "text-green-400" },
          { label: "Factures en retard", value: dash.overdue_invoices, icon: AlertTriangle, color: dash.overdue_invoices > 0 ? "text-red-400" : "text-green-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${color}`} />
              <p className="text-white/50 text-xs">{label}</p>
            </div>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <h2 className="text-white font-semibold text-sm mb-4">Revenus mensuels (FCFA)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={dash.revenue_by_month}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(v: number) => [`${v.toLocaleString("fr-FR")} FCFA`, "Revenus"]}
              />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <h2 className="text-white font-semibold text-sm mb-4">Répartition par plan</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3} dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                  formatter={(v: number) => [v, "abonnements"]} />
                <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-40">
              <p className="text-white/30 text-sm">Aucun abonnement actif</p>
            </div>
          )}
        </div>
      </div>

      {/* Invoices */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold text-sm">Dernières factures</h2>
        </div>
        <div className="space-y-2">
          {invoices.length === 0 && <p className="text-white/30 text-sm text-center py-6">Aucune facture</p>}
          {invoices.map((inv) => (
            <div key={inv.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-white/30" />
                <div>
                  <p className="text-white text-sm font-medium">{inv.invoice_number}</p>
                  <p className="text-white/40 text-xs">{new Date(inv.created_at).toLocaleDateString("fr-FR")}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <p className={`text-sm font-semibold ${STATUS_COLORS[inv.status] ?? "text-white"}`}>
                  {inv.status}
                </p>
                <p className="text-white font-mono text-sm">
                  {Number(inv.total_amount).toLocaleString("fr-FR")} FCFA
                </p>
                <a
                  href={`/api/v1/billing/invoices/${inv.id}/pdf`}
                  target="_blank"
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  PDF
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Overdue alert */}
      {dash.overdue_amount > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-red-300 font-semibold text-sm">
              {dash.overdue_invoices} facture(s) en retard — {dash.overdue_amount.toLocaleString("fr-FR")} FCFA
            </p>
            <p className="text-red-400/70 text-xs mt-0.5">Des relances automatiques ont été envoyées.</p>
          </div>
        </div>
      )}
    </div>
  );
}
