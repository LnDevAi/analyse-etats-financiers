"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, CreditCard, Download, Loader2, Zap, Star } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";

interface Plan {
  id: string; name: string; display_name: string;
  price_monthly: number; price_yearly: number;
  max_analyses: number | null; max_users: number | null; max_documents: number | null;
  trial_days: number; features: string[];
}

interface Subscription {
  id: string; status: string; billing_cycle: string;
  trial_ends_at: string | null; current_period_end: string | null;
  analyses_used: number; documents_used: number;
  plan: Plan | null;
}

interface Invoice {
  id: string; invoice_number: string; status: string;
  total_amount: number; created_at: string;
}

const PAYMENT_METHODS = [
  { key: "ORANGE_MONEY", label: "Orange Money", icon: "🟠" },
  { key: "WAVE", label: "Wave", icon: "🔵" },
  { key: "MOOV_MONEY", label: "Moov Money", icon: "🟣" },
  { key: "CARD", label: "Carte bancaire", icon: "💳" },
];

const STATUS_COLORS: Record<string, string> = {
  TRIAL: "bg-blue-500/20 text-blue-400",
  ACTIVE: "bg-green-500/20 text-green-400",
  PAST_DUE: "bg-orange-500/20 text-orange-400",
  SUSPENDED: "bg-red-500/20 text-red-400",
  CANCELLED: "bg-gray-500/20 text-gray-400",
};

export default function AccountBillingPage() {
  const [sub, setSub] = useState<Subscription | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payModal, setPayModal] = useState<Invoice | null>(null);
  const [payMethod, setPayMethod] = useState("ORANGE_MONEY");
  const [paying, setPaying] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get("/billing/subscription"),
      api.get("/billing/plans"),
      api.get("/billing/invoices"),
    ]).then(([sRes, pRes, iRes]) => {
      setSub(sRes.data);
      setPlans(pRes.data);
      setInvoices(iRes.data);
    }).catch((err) => {
      if (err.response?.status !== 404) toast.error("Erreur de chargement");
    });
  }, []);

  const handlePay = async () => {
    if (!payModal) return;
    setPaying(true);
    try {
      const res = await api.post("/billing/payments/initiate", {
        invoice_id: payModal.id,
        payment_method: payMethod,
      });
      window.open(res.data.payment_url, "_blank");
      setPayModal(null);
      toast.success("Redirection vers la page de paiement…");
    } catch {
      toast.error("Erreur lors de l'initiation du paiement");
    } finally {
      setPaying(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    try {
      await api.patch("/billing/subscription/upgrade", { plan_id: planId });
      const res = await api.get("/billing/subscription");
      setSub(res.data);
      toast.success("Plan mis à jour");
    } catch {
      toast.error("Erreur lors du changement de plan");
    }
  };

  const plan = sub?.plan;
  const usagePct = plan?.max_analyses
    ? Math.min(100, Math.round(((sub?.analyses_used ?? 0) / plan.max_analyses) * 100))
    : 0;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Mon abonnement</h1>
        <p className="text-white/50 text-sm mt-1">Gérez votre plan et vos paiements</p>
      </div>

      {/* Current subscription */}
      {sub ? (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-bold text-lg">{plan?.display_name ?? "—"}</p>
              <p className="text-white/40 text-sm">
                {sub.billing_cycle === "MONTHLY" ? "Facturation mensuelle" : "Facturation annuelle"}
              </p>
            </div>
            <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_COLORS[sub.status] ?? ""}`}>
              {sub.status}
            </span>
          </div>

          {sub.status === "TRIAL" && sub.trial_ends_at && (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-sm text-blue-300">
              Période d'essai jusqu'au {new Date(sub.trial_ends_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" })}
            </div>
          )}

          {sub.current_period_end && (
            <p className="text-white/40 text-xs">
              Prochain renouvellement : {new Date(sub.current_period_end).toLocaleDateString("fr-FR")}
            </p>
          )}

          {/* Usage */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-white/50">Analyses utilisées</span>
                <span className="text-white font-medium">
                  {sub.analyses_used} / {plan?.max_analyses ?? "∞"}
                </span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${usagePct}%` }} />
              </div>
            </div>
            <div className="flex gap-4 text-xs text-white/40">
              <span>Documents : {sub.documents_used} / {plan?.max_documents ?? "∞"}</span>
              <span>Utilisateurs : — / {plan?.max_users ?? "∞"}</span>
            </div>
          </div>

          <div className="text-right">
            <p className="text-white font-bold text-2xl">
              {plan ? `${Number(plan.price_monthly).toLocaleString("fr-FR")} FCFA` : "—"}
              <span className="text-sm font-normal text-white/40">/mois</span>
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
          <p className="text-white/40 text-sm">Aucun abonnement actif. Choisissez un plan ci-dessous.</p>
        </div>
      )}

      {/* Plans */}
      <div>
        <h2 className="text-white font-semibold mb-4">Plans disponibles</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map((p) => {
            const isCurrent = sub?.plan?.id === p.id;
            const isPro = p.name === "PRO";
            return (
              <div key={p.id} className={`relative bg-white/5 border rounded-2xl p-5 flex flex-col gap-4 ${isPro ? "border-blue-500/50 bg-blue-500/5" : "border-white/10"}`}>
                {isPro && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                    <Star className="w-3 h-3" /> Recommandé
                  </div>
                )}
                <div>
                  <p className="text-white font-bold text-base">{p.display_name}</p>
                  <p className="text-white/40 text-xs mt-0.5">{p.trial_days} jours d'essai offerts</p>
                </div>
                <div>
                  <p className="text-white text-2xl font-bold">
                    {Number(p.price_monthly).toLocaleString("fr-FR")} FCFA
                    <span className="text-sm font-normal text-white/40">/mois</span>
                  </p>
                  {p.price_yearly && (
                    <p className="text-green-400 text-xs mt-0.5">
                      {Number(p.price_yearly).toLocaleString("fr-FR")} FCFA/an (−15%)
                    </p>
                  )}
                </div>
                <ul className="space-y-1.5 text-xs text-white/60 flex-1">
                  <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> {p.max_analyses ? `${p.max_analyses} analyses/mois` : "Analyses illimitées"}</li>
                  <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> {p.max_users ? `${p.max_users} utilisateurs` : "Utilisateurs illimités"}</li>
                  <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> {p.max_documents ? `${p.max_documents} documents` : "Documents illimités"}</li>
                  {(p.features as string[] ?? []).map((f, i) => (
                    <li key={i} className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> {f}</li>
                  ))}
                </ul>
                <button
                  onClick={() => !isCurrent && handleUpgrade(p.id)}
                  disabled={isCurrent}
                  className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${isCurrent ? "bg-green-500/20 text-green-400 cursor-default" : "bg-blue-600 hover:bg-blue-500 text-white"}`}
                >
                  {isCurrent ? "Plan actuel" : p.name === "ENTERPRISE" ? "Nous contacter" : "Choisir ce plan"}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Invoices */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
        <h2 className="text-white font-semibold mb-4">Historique des factures</h2>
        {invoices.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-6">Aucune facture pour l'instant</p>
        ) : (
          <div className="space-y-2">
            {invoices.map((inv) => (
              <div key={inv.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div>
                  <p className="text-white text-sm font-medium">{inv.invoice_number}</p>
                  <p className="text-white/40 text-xs">{new Date(inv.created_at).toLocaleDateString("fr-FR")}</p>
                </div>
                <div className="flex items-center gap-4">
                  <p className="text-white font-mono text-sm">{Number(inv.total_amount).toLocaleString("fr-FR")} FCFA</p>
                  {inv.status !== "PAID" && (
                    <button
                      onClick={() => setPayModal(inv)}
                      className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg transition-colors flex items-center gap-1"
                    >
                      <CreditCard className="w-3 h-3" /> Payer
                    </button>
                  )}
                  {inv.status === "PAID" && <CheckCircle2 className="w-4 h-4 text-green-400" />}
                  <a href={`/api/v1/billing/invoices/${inv.id}/pdf`} target="_blank"
                    className="text-white/40 hover:text-white/70 transition-colors">
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payment modal */}
      {payModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-5">
            <h2 className="text-white font-bold">Paiement — {payModal.invoice_number}</h2>
            <p className="text-white/60 text-sm">
              Montant : <span className="text-white font-bold">
                {Number(payModal.total_amount).toLocaleString("fr-FR")} FCFA
              </span>
            </p>
            <div>
              <p className="text-white/60 text-xs mb-3">Choisissez votre mode de paiement</p>
              <div className="grid grid-cols-2 gap-2">
                {PAYMENT_METHODS.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setPayMethod(m.key)}
                    className={`flex items-center gap-2 p-3 rounded-xl border text-sm font-medium transition-all ${payMethod === m.key ? "border-blue-500 bg-blue-500/10 text-white" : "border-white/10 bg-white/5 text-white/60 hover:border-white/30"}`}
                  >
                    <span className="text-lg">{m.icon}</span>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setPayModal(null)} className="flex-1 bg-white/5 text-white/60 rounded-lg py-2.5 text-sm">Annuler</button>
              <button onClick={handlePay} disabled={paying}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-medium flex items-center justify-center gap-2">
                {paying && <Loader2 className="w-4 h-4 animate-spin" />}
                Payer maintenant
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
