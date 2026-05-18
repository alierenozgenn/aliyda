import axios from 'axios'
import { supabase } from '../lib/supabase'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({ baseURL: API_BASE })

/**
 * Inject the Supabase JWT on every request.
 * We always call getSession() to get the freshest token —
 * Supabase caches this internally so it's fast after the first call.
 */
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// --- Accounts ---
export const getAccounts = () => api.get('/accounts').then(r => r.data)
export const createAccount = (data) => api.post('/accounts', data).then(r => r.data)
export const updateAccount = (id, data) => api.patch(`/accounts/${id}`, data).then(r => r.data)
export const archiveAccount = (id) => api.delete(`/accounts/${id}`).then(r => r.data)

// --- Transactions ---
export const getTransactions = (month) => api.get('/transactions', { params: { month } }).then(r => r.data)
export const createManualTransaction = (month, data) =>
  api.post('/transactions/manual', data, { params: { month } }).then(r => r.data)
export const updateTransaction = (id, data) => api.patch(`/transactions/${id}`, data).then(r => r.data)
export const deleteTransaction = (id) => api.delete(`/transactions/${id}`).then(r => r.data)
export const restoreTransaction = (id) => api.post(`/transactions/${id}/restore`).then(r => r.data)

// --- Statements (PDF) ---
export const uploadStatement = (formData) =>
  api.post('/statements/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
export const getStatements = (month) => api.get('/statements', { params: { month } }).then(r => r.data)
export const getDrafts = (statementId) => api.get(`/statements/${statementId}/drafts`).then(r => r.data)
export const finalizeStatement = (statementId) => api.post(`/statements/${statementId}/finalize`).then(r => r.data)

// --- Drafts ---
export const approveDraft = (draftId, data) =>
  api.post(`/drafts/${draftId}/approve`, data || {}).then(r => r.data)
export const rejectDraft = (draftId, reason) =>
  api.post(`/drafts/${draftId}/reject`, { reason }).then(r => r.data)

// --- Dashboard ---
export const getDashboard = (month) => api.get('/dashboard', { params: { month } }).then(r => r.data)
export const upsertMonthlyProfile = (month, data) =>
  api.put(`/dashboard/profile/${month}`, data).then(r => r.data)

// --- Insights ---
export const generateInsight = (month, forceRefresh = false) =>
  api.post('/insights/monthly', null, {
    params: { month, force_refresh: forceRefresh },
  }).then(r => r.data)

// --- Chat ---
export const createChatSession = (month) =>
  api.post('/chat/sessions', null, { params: { month } }).then(r => r.data)
export const getChatSessions = () => api.get('/chat/sessions').then(r => r.data)
export const getSessionMessages = (sessionId) =>
  api.get(`/chat/sessions/${sessionId}/messages`).then(r => r.data)
export const sendChatMessage = (data) => api.post('/chat', data).then(r => r.data)

export default api
