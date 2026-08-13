import axios from 'axios';
import { relativeApiBaseUrl, resolvedWsBaseUrl } from '@/services/runtimeConfig';

const apiBaseUrl = relativeApiBaseUrl;

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

function resolveAuthToken() {
  if (typeof window === 'undefined') return '';
  return (
    window.localStorage.getItem('liceu_access_token') ||
    window.localStorage.getItem('access_token') ||
    ''
  );
}

apiClient.interceptors.request.use((config) => {
  const token = resolveAuthToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const johnCRMChat = (payload) => apiClient.post('/john/crm/chat', payload);
export const johnLeads = () => apiClient.get('/john/leads');
export const johnLeadsMetrics = (days = 30) => apiClient.get('/john/leads/metrics', { params: { days } });
export const johnUpdateLeadStatus = (leadId, status, note = '') =>
  apiClient.patch(`/john/leads/${leadId}/status`, { status, note });
export const johnRetrainScoring = (lookbackDays = 180, minExamples = 8) =>
  apiClient.post('/john/crm/scoring/retrain', { lookback_days: lookbackDays, min_examples: minExamples });
export const johnWhatsAppSend = (message, to = '') =>
  apiClient.post('/john/crm/whatsapp/send', { message, to: to || null });
export const johnWelcome = (payload) => apiClient.post('/john/welcome', payload);
export const johnDispatch = (intent) => apiClient.post('/john/dispatch', null, { params: { intent } });
export const johnDiscussPillar = (pilar) => apiClient.get(`/john/discuss/${pilar}`);
export const createJourneyQr = (payload) => apiClient.post('/auth/qr/create', payload);
export const loginWithQr = (token) => apiClient.post('/auth/qr/login', { token });
export const getKanbanBoard = (params = {}) => apiClient.get('/kanban/board', { params });
export const getKanbanCard = (cardId) => apiClient.get(`/kanban/cards/${cardId}`);
export const ingestKanbanEvent = (payload) => apiClient.post('/kanban/events/ingest', payload);
export const syncKanbanRuntime = (limit = 100) => apiClient.post('/kanban/runtime/sync', null, { params: { limit } });
export const assignKanbanCard = (cardId, assignedTo) => apiClient.patch(`/kanban/cards/${cardId}/assign`, { assigned_to: assignedTo });
export const addKanbanComment = (cardId, content) => apiClient.post(`/kanban/cards/${cardId}/comments`, { content });
export const addKanbanAttachment = (cardId, payload) => apiClient.post(`/kanban/cards/${cardId}/attachments`, payload);
export const runKanbanAutomation = (cardId, automation) => apiClient.post(`/kanban/cards/${cardId}/automations`, { automation });
export const getStrategicKanbanBoard = (params = {}) => apiClient.get('/strategic-kanban/board', { params });
export const moveStrategicKanbanCardStage = (cardId, stage) => apiClient.patch(`/strategic-kanban/cards/${cardId}/stage`, { stage });
export const getStrategicSuggestion = (entityType, entityId, params = {}) => apiClient.get(`/strategic-suggestions/${entityType}/${entityId}`, { params });
export const getStrategies = (params = {}) => apiClient.get('/strategies', { params });
export const createStrategy = (payload) => apiClient.post('/strategies', payload);
export const getObjectives = (params = {}) => apiClient.get('/objectives', { params });
export const getInitiatives = (params = {}) => apiClient.get('/initiatives', { params });
export const getPlans = (params = {}) => apiClient.get('/plans', { params });
export const getTasks = (params = {}) => apiClient.get('/tasks', { params });
export const getIRDashboard = (investorId = '') =>
  apiClient.get('/gateway/investor-relations/dashboard', {
    params: investorId ? { investor_id: investorId } : {}
  });
export const getIREventsPublished = () => apiClient.get('/gateway/investor-relations/events/published');
export const createIROpportunity = (payload) => apiClient.post('/gateway/investor-relations/opportunities', payload);
export const createIRAllocation = (payload) => apiClient.post('/gateway/investor-relations/allocations', payload);
export const getQuantDashboard = () => apiClient.get('/gateway/quant-engine/dashboard');
export const getQuantEventsPublished = () => apiClient.get('/gateway/quant-engine/events/published');
export const runQuantRebalance = (portfolio = []) =>
  apiClient.post('/gateway/quant-engine/rebalance', { portfolio });
export const getLexDashboard = () => apiClient.get('/gateway/lex/dashboard');
export const getLexEventsPublished = () => apiClient.get('/gateway/lex/events/published');
export const getLexFairPrice = (roi, risk, progress) =>
  apiClient.get('/gateway/lex/pricing/fair', { params: { roi, risk, progress } });
export const getLexMarketMakerQuote = (assetId, confidence = 0.6) =>
  apiClient.get(`/gateway/lex/market-maker/${assetId}`, { params: { confidence } });
export const recalculateLexIndices = () => apiClient.post('/gateway/lex/indices/recalculate');
export const getLexFunds = () => apiClient.get('/gateway/lex/funds');
export const subscribeLexFund = (payload) => apiClient.post('/gateway/lex/funds/subscribe', payload);
export const getLexJohnMarketBrief = (indexCode = 'LEX-INFRA') =>
  apiClient.get('/gateway/lex/john/market-brief', { params: { index_code: indexCode } });
export const approveLexKyc = (investorId) => apiClient.post(`/gateway/lex/kyc/${investorId}`);
export const depositLexCash = (payload) => apiClient.post('/gateway/lex/clearing/cash/deposit', payload);
export const grantLexInventory = (payload) => apiClient.post('/gateway/lex/clearing/inventory/grant', payload);
export const createLexOrder = (payload) => apiClient.post('/gateway/lex/orders', payload);
export const runLexMatching = (assetId) => apiClient.post(`/gateway/lex/matching/${assetId}`);
export const createJohnEventsSocket = () => {
  return new WebSocket(`${resolvedWsBaseUrl}/ws/john/events`);
};
export const createKanbanEventsSocket = () => {
  return new WebSocket(`${resolvedWsBaseUrl}/ws/kanban/events`);
};
export const createEventsSocket = () => {
  return new WebSocket(`${resolvedWsBaseUrl}/events/ws`);
};

export default apiClient;
