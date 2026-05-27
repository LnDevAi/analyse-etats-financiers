"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ChevronLeft, Building2, Phone, Mail, Globe, MapPin,
  Plus, Pencil, CheckCircle2, Clock, CalendarDays, Star,
} from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";

const ACTIVITY_ICONS: Record<string, string> = {
  CALL: "📞", EMAIL: "✉️", MEETING: "🤝", DEMO: "💻", NOTE: "📝", RELANCE: "🔔",
};

const LIFECYCLE_OPTIONS = ["PROSPECT", "TRIAL", "ACTIF", "SUSPENDU", "CHURNED"];
const STAGE_OPTIONS = ["PROSPECT", "QUALIFIÉ", "DÉMO", "NÉGOCIATION", "GAGNÉ", "PERDU"];
const ACTIVITY_TYPES = ["CALL", "EMAIL", "MEETING", "DEMO", "NOTE", "RELANCE"];

interface Contact { id: string; full_name: string; role: string; email: string; phone: string; is_primary: boolean }
interface Activity { id: string; activity_type: string; subject: string; body: string; outcome: string; next_action: string; next_action_date: string; created_at: string; duration_minutes: number }
interface Client {
  id: string; company_name: string; rccm: string; nif: string; sector: string;
  country: string; city: string; address: string; website: string;
  lifecycle_status: string; pipeline_stage: string; deal_value: number | null;
  source: string; health_score: number | null; tags: string[]; notes: string;
  last_contact_at: string | null; created_at: string; contacts: Contact[];
}

export default function CRMClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [client, setClient] = useState<Client | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [tab, setTab] = useState<"info" | "contacts" | "activites">("info");
  const [showActivity, setShowActivity] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [editing, setEditing] = useState(false);
  const [actForm, setActForm] = useState({ activity_type: "CALL", subject: "", body: "", outcome: "", next_action: "", next_action_date: "" });
  const [contactForm, setContactForm] = useState({ full_name: "", role: "", email: "", phone: "", is_primary: false });
  const [editForm, setEditForm] = useState<Partial<Client>>({});

  const load = async () => {
    try {
      const [cRes, aRes] = await Promise.all([
        api.get(`/crm/clients/${id}`),
        api.get(`/crm/clients/${id}/activities`),
      ]);
      setClient(cRes.data);
      setActivities(aRes.data);
      setEditForm(cRes.data);
    } catch { toast.error("Client introuvable"); }
  };

  useEffect(() => { load(); }, [id]);

  const handleSave = async () => {
    try {
      await api.patch(`/crm/clients/${id}`, editForm);
      toast.success("Mis à jour");
      setEditing(false);
      load();
    } catch { toast.error("Erreur"); }
  };

  const handleAddActivity = async () => {
    try {
      await api.post(`/crm/clients/${id}/activities`, actForm);
      toast.success("Activité enregistrée");
      setShowActivity(false);
      setActForm({ activity_type: "CALL", subject: "", body: "", outcome: "", next_action: "", next_action_date: "" });
      load();
    } catch { toast.error("Erreur"); }
  };

  const handleAddContact = async () => {
    try {
      await api.post(`/crm/clients/${id}/contacts`, contactForm);
      toast.success("Contact ajouté");
      setShowContact(false);
      setContactForm({ full_name: "", role: "", email: "", phone: "", is_primary: false });
      load();
    } catch { toast.error("Erreur"); }
  };

  if (!client) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.push("/crm")} className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">{client.company_name}</h1>
          <p className="text-white/40 text-xs mt-0.5">{[client.sector, client.city, client.country].filter(Boolean).join(" · ")}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
            {client.lifecycle_status}
          </span>
          <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/60">
            {client.pipeline_stage}
          </span>
          <button onClick={() => setEditing(!editing)} className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
            <Pencil className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
          <p className="text-white text-lg font-bold">
            {client.deal_value ? `${(client.deal_value / 1000).toFixed(0)}k` : "—"}
          </p>
          <p className="text-white/40 text-xs">Valeur estimée (FCFA)</p>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
          <p className="text-white text-lg font-bold">{client.health_score ?? "—"}<span className="text-xs text-white/40">/100</span></p>
          <p className="text-white/40 text-xs">Score santé</p>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center">
          <p className="text-white text-lg font-bold">{activities.length}</p>
          <p className="text-white/40 text-xs">Interactions</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 rounded-lg p-1 w-fit">
        {(["info", "contacts", "activites"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === t ? "bg-white/15 text-white" : "text-white/50 hover:text-white"}`}>
            {t === "info" ? "Informations" : t === "contacts" ? `Contacts (${client.contacts.length})` : `Activités (${activities.length})`}
          </button>
        ))}
      </div>

      {/* Info tab */}
      {tab === "info" && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3">
            <h3 className="text-white font-semibold text-sm">Identité</h3>
            {editing ? (
              <div className="space-y-2">
                {[
                  { key: "company_name", label: "Raison sociale" },
                  { key: "rccm", label: "RCCM" },
                  { key: "nif", label: "NIF/IFU" },
                  { key: "sector", label: "Secteur" },
                  { key: "city", label: "Ville" },
                  { key: "website", label: "Site web" },
                ].map(({ key, label }) => (
                  <div key={key}>
                    <label className="text-white/40 text-xs">{label}</label>
                    <input value={(editForm as any)[key] ?? ""} onChange={(e) => setEditForm({ ...editForm, [key]: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500" />
                  </div>
                ))}
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: "lifecycle_status", label: "Statut cycle de vie", opts: LIFECYCLE_OPTIONS },
                    { key: "pipeline_stage", label: "Stade pipeline", opts: STAGE_OPTIONS },
                  ].map(({ key, label, opts }) => (
                    <div key={key}>
                      <label className="text-white/40 text-xs">{label}</label>
                      <select value={(editForm as any)[key] ?? ""} onChange={(e) => setEditForm({ ...editForm, [key]: e.target.value })}
                        className="w-full bg-white/5 border border-white/10 rounded px-2 py-1 text-white text-sm focus:outline-none">
                        {opts.map((o) => <option key={o} value={o}>{o}</option>)}
                      </select>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 pt-1">
                  <button onClick={() => setEditing(false)} className="flex-1 bg-white/5 text-white/60 rounded py-1.5 text-sm">Annuler</button>
                  <button onClick={handleSave} className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded py-1.5 text-sm font-medium">Enregistrer</button>
                </div>
              </div>
            ) : (
              <dl className="space-y-2">
                {[
                  { label: "RCCM", value: client.rccm },
                  { label: "NIF/IFU", value: client.nif },
                  { label: "Secteur", value: client.sector },
                  { label: "Ville", value: client.city },
                  { label: "Source", value: client.source },
                  { label: "Site web", value: client.website },
                ].map(({ label, value }) => value ? (
                  <div key={label} className="flex justify-between text-sm">
                    <dt className="text-white/40">{label}</dt>
                    <dd className="text-white font-medium">{value}</dd>
                  </div>
                ) : null)}
              </dl>
            )}
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3">
            <h3 className="text-white font-semibold text-sm">Notes internes</h3>
            {editing ? (
              <textarea value={editForm.notes ?? ""} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                rows={6} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none resize-none" />
            ) : (
              <p className="text-white/60 text-sm leading-relaxed">{client.notes || "Aucune note."}</p>
            )}
          </div>
        </div>
      )}

      {/* Contacts tab */}
      {tab === "contacts" && (
        <div className="space-y-3">
          <button onClick={() => setShowContact(true)}
            className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors">
            <Plus className="w-4 h-4" /> Ajouter un contact
          </button>
          {client.contacts.map((c) => (
            <div key={c.id} className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-4">
              <div className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {c.full_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1">
                <p className="text-white text-sm font-medium flex items-center gap-2">
                  {c.full_name}
                  {c.is_primary && <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />}
                </p>
                <p className="text-white/40 text-xs">{c.role}</p>
              </div>
              <div className="text-right space-y-0.5">
                {c.email && <p className="text-white/60 text-xs">{c.email}</p>}
                {c.phone && <p className="text-white/60 text-xs">{c.phone}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Activities tab */}
      {tab === "activites" && (
        <div className="space-y-3">
          <button onClick={() => setShowActivity(true)}
            className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors">
            <Plus className="w-4 h-4" /> Enregistrer une interaction
          </button>
          {activities.map((a) => (
            <div key={a.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-lg">{ACTIVITY_ICONS[a.activity_type] ?? "📋"}</span>
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">{a.subject || a.activity_type}</p>
                  <p className="text-white/40 text-xs">{new Date(a.created_at).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" })}</p>
                </div>
                {a.outcome && <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">{a.outcome}</span>}
              </div>
              {a.body && <p className="text-white/60 text-sm pl-9">{a.body}</p>}
              {a.next_action && (
                <div className="flex items-center gap-2 mt-2 pl-9 text-xs text-orange-400">
                  <CalendarDays className="w-3 h-3" />
                  <span>Prochaine action : {a.next_action} {a.next_action_date ? `(${a.next_action_date})` : ""}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Activity modal */}
      {showActivity && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-white font-bold">Enregistrer une interaction</h2>
            <div>
              <label className="text-white/60 text-xs mb-1 block">Type</label>
              <select value={actForm.activity_type} onChange={(e) => setActForm({ ...actForm, activity_type: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none">
                {ACTIVITY_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            {[
              { key: "subject", label: "Sujet", placeholder: "Ex: Appel de découverte" },
              { key: "body", label: "Notes", placeholder: "Résumé de l'interaction…" },
              { key: "outcome", label: "Résultat", placeholder: "Ex: Intéressé, Rappel prévu…" },
              { key: "next_action", label: "Prochaine action", placeholder: "Ex: Envoyer une offre" },
              { key: "next_action_date", label: "Date prochaine action", placeholder: "YYYY-MM-DD" },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="text-white/60 text-xs mb-1 block">{label}</label>
                {key === "body" ? (
                  <textarea value={(actForm as any)[key]} onChange={(e) => setActForm({ ...actForm, [key]: e.target.value })}
                    placeholder={placeholder} rows={3}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none resize-none placeholder-white/20" />
                ) : (
                  <input value={(actForm as any)[key]} onChange={(e) => setActForm({ ...actForm, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none placeholder-white/20" />
                )}
              </div>
            ))}
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowActivity(false)} className="flex-1 bg-white/5 text-white/60 rounded-lg py-2 text-sm">Annuler</button>
              <button onClick={handleAddActivity} className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 text-sm font-medium">Enregistrer</button>
            </div>
          </div>
        </div>
      )}

      {/* Contact modal */}
      {showContact && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-white font-bold">Ajouter un contact</h2>
            {[
              { key: "full_name", label: "Nom complet *", placeholder: "Ex: Moussa Kaboré" },
              { key: "role", label: "Fonction", placeholder: "Ex: Directeur Financier" },
              { key: "email", label: "Email", placeholder: "contact@exemple.bf" },
              { key: "phone", label: "Téléphone", placeholder: "+226 70 00 00 00" },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="text-white/60 text-xs mb-1 block">{label}</label>
                <input value={(contactForm as any)[key]} onChange={(e) => setContactForm({ ...contactForm, [key]: e.target.value })}
                  placeholder={placeholder}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none placeholder-white/20" />
              </div>
            ))}
            <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer">
              <input type="checkbox" checked={contactForm.is_primary} onChange={(e) => setContactForm({ ...contactForm, is_primary: e.target.checked })} />
              Contact principal
            </label>
            <div className="flex gap-3 pt-2">
              <button onClick={() => setShowContact(false)} className="flex-1 bg-white/5 text-white/60 rounded-lg py-2 text-sm">Annuler</button>
              <button onClick={handleAddContact} className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 text-sm font-medium">Ajouter</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
