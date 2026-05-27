import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/auth/login";
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password });

export const verifyMfa = (email: string, totp_code: string, temp_token: string) =>
  api.post("/auth/mfa/verify", { email, totp_code, temp_token });

export const logout = () => api.post("/auth/logout");

export const getMfaSetup = () => api.get("/auth/mfa/setup");

export const enableMfa = (totp_code: string) =>
  api.post("/auth/mfa/enable", { totp_code });

export const forgotPassword = (email: string) =>
  api.post("/auth/forgot-password", { email });

export const resetPassword = (token: string, new_password: string) =>
  api.post("/auth/reset-password", { token, new_password });

// Users
export const getMe = () => api.get("/users/me");
export const listUsers = () => api.get("/users/");
export const createUser = (data: any) => api.post("/users/", data);

// Documents
export const uploadDocument = (formData: FormData) =>
  api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const listDocuments = () => api.get("/documents/");
export const deleteDocument = (id: string) => api.delete(`/documents/${id}`);

// Analysis
export const createAnalysis = (
  document_id: string,
  previous_document_id?: string,
  balance_document_id?: string,
) =>
  api.post("/analyses/", {
    document_id,
    previous_document_id: previous_document_id || undefined,
    balance_document_id: balance_document_id || undefined,
  });

export const listAnalyses = () => api.get("/analyses/");

export const getAnalysis = (id: string) => api.get(`/analyses/${id}`);

export const getDashboard = () => api.get("/analyses/dashboard");

export const downloadDocx = (id: string) =>
  api.get(`/analyses/${id}/report/docx`, { responseType: "blob" });

export const downloadXlsx = (id: string) =>
  api.get(`/analyses/${id}/report/xlsx`, { responseType: "blob" });

// Tenant registration
export const registerTenant = (data: any) =>
  api.post("/tenants/register", data);

// AG Analysis
export const createAGAnalysis = (data: {
  fec_document_id: string;
  budget_document_id?: string;
  social_document_id?: string;
  marches_document_id?: string;
  activites_document_id?: string;
}) => api.post("/ag-analyses/", data);

export const listAGAnalyses = () => api.get("/ag-analyses/");
export const getAGAnalysis = (id: string) => api.get(`/ag-analyses/${id}`);

// CRM
export const listCRMClients = (params?: { stage?: string; lifecycle?: string; search?: string }) =>
  api.get("/crm/clients", { params });
export const getCRMClient = (id: string) => api.get(`/crm/clients/${id}`);
export const createCRMClient = (data: any) => api.post("/crm/clients", data);
export const updateCRMClient = (id: string, data: any) => api.patch(`/crm/clients/${id}`, data);
export const deleteCRMClient = (id: string) => api.delete(`/crm/clients/${id}`);
export const getCRMPipelineStats = () => api.get("/crm/pipeline/stats");
export const addCRMContact = (clientId: string, data: any) => api.post(`/crm/clients/${clientId}/contacts`, data);
export const deleteCRMContact = (contactId: string) => api.delete(`/crm/contacts/${contactId}`);
export const listCRMActivities = (clientId: string) => api.get(`/crm/clients/${clientId}/activities`);
export const addCRMActivity = (clientId: string, data: any) => api.post(`/crm/clients/${clientId}/activities`, data);

// Billing
export const listPlans = () => api.get("/billing/plans");
export const getMySubscription = () => api.get("/billing/subscription");
export const createSubscription = (data: any) => api.post("/billing/subscription", data);
export const upgradeSubscription = (data: any) => api.patch("/billing/subscription/upgrade", data);
export const listInvoices = () => api.get("/billing/invoices");
export const initiatePayment = (data: any) => api.post("/billing/payments/initiate", data);
export const listPayments = () => api.get("/billing/payments");
export const getBillingDashboard = () => api.get("/billing/dashboard");
