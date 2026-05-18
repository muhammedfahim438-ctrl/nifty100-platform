// B100 Intelligence — API Service
// All calls to Django REST API go through this file

import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Companies ──
export const getCompanies = (params = {}) =>
  api.get('/companies/', { params: { ...params, page_size: 100 } });

export const getCompany = (symbol) =>
  api.get(`/companies/${symbol}/`);

export const getCompanyFinancials = (symbol) =>
  api.get(`/companies/${symbol}/financials/`);

// ── Sectors ──
export const getSectors = () =>
  api.get('/sectors/');

// ── Health Scores ──
export const getHealthScores = (params = {}) =>
  api.get('/scores/', { params });

// ── Screener ──
export const screenCompanies = (params = {}) =>
  api.get('/screener/', { params });

export default api;