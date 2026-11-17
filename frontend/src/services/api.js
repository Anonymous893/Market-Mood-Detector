import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE,
  timeout: 30_000,
  headers: { Accept: 'application/json' },
});

function normalizeTicker(ticker) {
  return String(ticker ?? '').trim().toUpperCase();
}

export function getApiErrorMessage(error, fallback = 'The analysis could not be completed.') {
  const payload = error?.response?.data;
  const apiMessage = payload?.error?.message;

  if (apiMessage) return apiMessage;
  if (typeof payload?.detail === 'string') return payload.detail;
  if (typeof error?.message === 'string' && error.message !== 'Network Error') {
    return error.message;
  }
  if (error?.code === 'ECONNABORTED') {
    return 'The request timed out. Please try again.';
  }
  if (!error?.response) {
    return `Unable to reach the backend at ${BASE}.`;
  }
  return fallback;
}

export async function analyseTicker(ticker) {
  const symbol = normalizeTicker(ticker);
  const { data } = await client.get(`/analyse/${encodeURIComponent(symbol)}`);
  return data;
}

export async function getHistory(ticker, limit = 8) {
  const symbol = normalizeTicker(ticker);
  const { data } = await client.get(`/history/${encodeURIComponent(symbol)}`, { params: { limit } });
  return data.history ?? [];
}

export async function getAnalytics(ticker) {
  const symbol = normalizeTicker(ticker);
  const { data } = await client.get(`/analytics/${encodeURIComponent(symbol)}`);
  return data;
}

export async function getHealth() {
  const { data } = await client.get('/');
  return data;
}

export default client;
