import api from './client';
import type {
  AnalyticsOverview, Alert, CallLog, CommunityInsight, CountryInfo,
  DailyCallStat, FarmerCreate, FarmerProfile, LanguageInfo, LanguageStat,
  ExpenseRecord, ExpenseSummary,
} from '../types';

export async function getOverview(): Promise<AnalyticsOverview> {
  return (await api.get('/analytics/overview')).data;
}

export async function getLanguageStats(): Promise<LanguageStat[]> {
  return (await api.get('/analytics/languages')).data;
}

export async function getTimeline(days?: number): Promise<DailyCallStat[]> {
  return (await api.get('/analytics/timeline', { params: { days } })).data;
}

export async function getCalls(skip?: number, limit?: number, language?: string): Promise<CallLog[]> {
  return (await api.get('/calls', { params: { skip, limit, language } })).data;
}

export async function getLanguages(): Promise<Record<string, LanguageInfo>> {
  return (await api.get('/languages')).data;
}

export async function getCountries(): Promise<Record<string, CountryInfo>> {
  return (await api.get('/countries')).data;
}

// Farmers
export async function createFarmer(data: FarmerCreate): Promise<FarmerProfile> {
  return (await api.post('/farmers', data)).data;
}

export async function listFarmers(country?: string): Promise<FarmerProfile[]> {
  return (await api.get('/farmers', { params: { country } })).data;
}

export async function getFarmer(id: number): Promise<FarmerProfile> {
  return (await api.get(`/farmers/${id}`)).data;
}

// Alerts
export async function getAlerts(country?: string): Promise<Alert[]> {
  return (await api.get('/alerts', { params: { country } })).data;
}

// Community
export async function getCommunityInsights(country?: string): Promise<CommunityInsight[]> {
  return (await api.get('/community', { params: { country } })).data;
}

// Expenses
export async function getExpenses(farmerId: number): Promise<ExpenseRecord[]> {
  return (await api.get(`/expenses/${farmerId}`)).data;
}

export async function getExpenseSummary(farmerId: number): Promise<ExpenseSummary> {
  return (await api.get(`/expenses/${farmerId}/summary`)).data;
}
