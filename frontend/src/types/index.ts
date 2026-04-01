export interface VoiceResponse {
  transcript: string;
  response_text: string;
  audio_url: string;
  language: string;
  session_id: string;
  expense_detected?: ExpenseData;
}

export interface ExpenseData {
  category: string;
  amount: number;
  description: string;
  crop?: string;
}

export interface CallLog {
  id: number;
  session_id: string;
  source: string;
  phone_number?: string;
  language: string;
  farmer_question: string;
  ai_response: string;
  category?: string;
  created_at: string;
}

export interface AnalyticsOverview {
  total_calls: number;
  unique_sessions: number;
  languages_served: number;
  calls_today: number;
}

export interface LanguageStat {
  language: string;
  language_name: string;
  count: number;
  percentage: number;
}

export interface DailyCallStat {
  date: string;
  count: number;
}

export interface LanguageInfo {
  name: string;
  native_name: string;
}

export interface ConversationTurn {
  role: 'farmer' | 'advisor';
  text: string;
  language: string;
  audio_url?: string;
}

export interface FarmerProfile {
  id: number;
  name?: string;
  preferred_language: string;
  country: string;
  region?: string;
  district?: string;
  village?: string;
  land_size_acres?: number;
  crops: string[];
  soil_type?: string;
  irrigation_type?: string;
  past_problems: string[];
  active_issues: string[];
  total_calls: number;
}

export interface FarmerCreate {
  name?: string;
  preferred_language: string;
  country: string;
  region?: string;
  district?: string;
  village?: string;
  land_size_acres?: number;
  crops: string[];
  soil_type?: string;
  irrigation_type?: string;
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  country: string;
  region?: string;
  affected_crops: string[];
  source?: string;
  created_at: string;
}

export interface CommunityInsight {
  id: number;
  region: string;
  country: string;
  topic: string;
  affected_crop?: string;
  farmer_count: number;
  trending: boolean;
  ai_summary?: string;
  last_reported: string;
}

export interface ExpenseRecord {
  id: number;
  farmer_id: number;
  category: string;
  description: string;
  amount: number;
  date?: string;
  crop?: string;
  created_at: string;
}

export interface ExpenseSummary {
  total_spent: number;
  by_category: Record<string, number>;
  by_crop: Record<string, number>;
  expense_count: number;
}

export interface CountryInfo {
  name: string;
  languages: string[];
  currency: string;
}
