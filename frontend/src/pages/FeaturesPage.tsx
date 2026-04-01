import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  CloudSun, MapPin, TrendingUp, Landmark, Bug, BookOpen, FileText,
  UserPlus, Loader2, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

const COUNTRIES = [
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'KE', name: 'Kenya', flag: '🇰🇪' },
  { code: 'NG', name: 'Nigeria', flag: '🇳🇬' },
  { code: 'ET', name: 'Ethiopia', flag: '🇪🇹' },
];

function Section({ title, icon: Icon, color, children }: {
  title: string; icon: typeof CloudSun; color: string; children: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-5 hover:bg-gray-50">
        <div className="flex items-center gap-3">
          <div className={clsx('p-2 rounded-lg', color)}><Icon className="h-5 w-5" /></div>
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        </div>
        {open ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
      </button>
      {open && <div className="px-5 pb-5 border-t border-gray-100 pt-4">{children}</div>}
    </div>
  );
}

export default function FeaturesPage() {
  const [weatherCity, setWeatherCity] = useState('Sehore');
  const [yieldCrop, setYieldCrop] = useState('Wheat');
  const [yieldAcres, setYieldAcres] = useState('5');
  const [yieldCountry, setYieldCountry] = useState('IN');
  const [loanCountry, setLoanCountry] = useState('IN');
  const [kvkCountry, setKvkCountry] = useState('IN');
  const [kvkRegion, setKvkRegion] = useState('Madhya Pradesh');
  const [diaryFarmerId, setDiaryFarmerId] = useState('5');
  const [diaryCrop, setDiaryCrop] = useState('Wheat');
  const [diaryActivity, setDiaryActivity] = useState('planted');

  // Weather
  const weatherQuery = useQuery({
    queryKey: ['weather', weatherCity],
    queryFn: () => api.get(`/weather/${weatherCity}`).then(r => r.data),
    enabled: false,
  });

  // Yield
  const yieldMutation = useMutation({
    mutationFn: () => api.post('/yield/predict', {
      country: yieldCountry, crop: yieldCrop, land_acres: parseFloat(yieldAcres),
    }).then(r => r.data),
  });

  // Loans
  const loanQuery = useQuery({
    queryKey: ['loans', loanCountry],
    queryFn: () => api.get(`/loans/${loanCountry}?land_acres=5`).then(r => r.data),
    enabled: false,
  });

  // KVK
  const kvkQuery = useQuery({
    queryKey: ['kvk', kvkCountry, kvkRegion],
    queryFn: () => api.get(`/kvk/${kvkCountry}/${kvkRegion}`).then(r => r.data),
    enabled: false,
  });

  // Pests
  const pestsQuery = useQuery({
    queryKey: ['pests'],
    queryFn: () => api.get('/pests').then(r => r.data),
  });

  // Diary
  const diaryQuery = useQuery({
    queryKey: ['diary', diaryFarmerId],
    queryFn: () => api.get(`/diary/${diaryFarmerId}`).then(r => r.data),
    enabled: false,
  });

  const diaryMutation = useMutation({
    mutationFn: () => api.post('/diary', {
      farmer_id: parseInt(diaryFarmerId), crop: diaryCrop, activity: diaryActivity,
      details: `${diaryCrop} ${diaryActivity}`, date: new Date().toISOString().split('T')[0],
    }).then(r => r.data),
  });

  // Reminders
  const remindersQuery = useQuery({
    queryKey: ['reminders', diaryFarmerId],
    queryFn: () => api.get(`/reminders/${diaryFarmerId}`).then(r => r.data),
    enabled: false,
  });

  // Report
  const reportQuery = useQuery({
    queryKey: ['report', diaryFarmerId],
    queryFn: () => api.get(`/report/${diaryFarmerId}`).then(r => r.data),
    enabled: false,
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">All Features</h1>
      <p className="text-gray-500 mb-6">Test every KisanVaani feature with live data</p>

      {/* 1. WEATHER */}
      <Section title="Live Weather Forecast" icon={CloudSun} color="bg-blue-50 text-blue-600">
        <div className="flex gap-2 mb-3">
          <input value={weatherCity} onChange={e => setWeatherCity(e.target.value)}
            placeholder="City name (Sehore, Kakamega, Kano...)"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          <button onClick={() => weatherQuery.refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            {weatherQuery.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Get Weather'}
          </button>
        </div>
        {weatherQuery.data && (
          <div className="bg-blue-50 rounded-lg p-4 text-sm">
            <p className="font-medium">Now: {weatherQuery.data.current?.temperature}°C, {weatherQuery.data.current?.condition}</p>
            <div className="mt-2 space-y-1">
              {weatherQuery.data.forecast?.map((d: any) => (
                <p key={d.date}>{d.date}: {d.temp_min}-{d.temp_max}°C | Rain: {d.rain_chance}% | {d.condition}</p>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* 2. YIELD PREDICTOR */}
      <Section title="Crop Yield Predictor" icon={TrendingUp} color="bg-green-50 text-green-600">
        <div className="flex gap-2 mb-3 flex-wrap">
          <select value={yieldCountry} onChange={e => setYieldCountry(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.flag} {c.name}</option>)}
          </select>
          <input value={yieldCrop} onChange={e => setYieldCrop(e.target.value)} placeholder="Crop"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-32" />
          <input value={yieldAcres} onChange={e => setYieldAcres(e.target.value)} placeholder="Acres"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-20" />
          <button onClick={() => yieldMutation.mutate()}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">Predict</button>
        </div>
        {yieldMutation.data && (
          <div className="bg-green-50 rounded-lg p-4 text-sm">
            <p className="font-bold text-lg text-green-800">
              Expected: {yieldMutation.data.predicted_yield_per_acre} quintals/acre
              = {yieldMutation.data.total_yield} quintals total
            </p>
            <p className="mt-1">Range: {yieldMutation.data.range[0]} - {yieldMutation.data.range[1]} quintals</p>
            <p className="mt-1 text-gray-600">{yieldMutation.data.factors}</p>
            {yieldMutation.data.adjustments?.map((a: string, i: number) => (
              <p key={i} className="text-green-700">+ {a}</p>
            ))}
          </div>
        )}
      </Section>

      {/* 3. LOAN ELIGIBILITY */}
      <Section title="Loan & Scheme Eligibility" icon={Landmark} color="bg-purple-50 text-purple-600">
        <div className="flex gap-2 mb-3">
          <select value={loanCountry} onChange={e => setLoanCountry(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.flag} {c.name}</option>)}
          </select>
          <button onClick={() => loanQuery.refetch()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700">Check</button>
        </div>
        {loanQuery.data && (
          <div className="space-y-3">
            {loanQuery.data.map((loan: any, i: number) => (
              <div key={i} className={clsx('rounded-lg p-4 text-sm', loan.eligible ? 'bg-green-50' : 'bg-red-50')}>
                <p className="font-bold">{loan.name}</p>
                <p>Max Amount: {loan.max_amount.toLocaleString()} | Interest: {loan.interest_rate}%</p>
                <p className="text-gray-600">Apply at: {loan.where_to_apply}</p>
                <p className="text-gray-500 text-xs mt-1">Docs: {loan.documents.join(', ')}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* 4. KVK LOCATOR */}
      <Section title="Nearest Extension Service (KVK)" icon={MapPin} color="bg-red-50 text-red-600">
        <div className="flex gap-2 mb-3">
          <select value={kvkCountry} onChange={e => setKvkCountry(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.flag} {c.name}</option>)}
          </select>
          <input value={kvkRegion} onChange={e => setKvkRegion(e.target.value)} placeholder="State/Region"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          <button onClick={() => kvkQuery.refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700">Find</button>
        </div>
        {kvkQuery.data?.results && (
          <div className="space-y-2">
            {kvkQuery.data.results.map((k: any, i: number) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3 text-sm">
                <p className="font-bold">{k.name}</p>
                <p className="text-gray-600">{k.address}</p>
                <p className="text-primary-600 font-medium">{k.phone}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* 5. PEST GALLERY */}
      <Section title="Pest & Disease Gallery" icon={Bug} color="bg-amber-50 text-amber-600">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {pestsQuery.data?.map((pest: any) => (
            <div key={pest.id} className="bg-gray-50 rounded-lg p-3 text-sm">
              <p className="font-bold text-gray-900">{pest.name}</p>
              <p className="text-xs text-gray-500">Crops: {pest.crops.join(', ')}</p>
              <p className="mt-1 text-gray-700">{pest.symptoms}</p>
              <p className="mt-1 text-green-700 text-xs">{pest.treatment}</p>
              {pest.image_url && (
                <a href={pest.image_url} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-1 text-xs text-primary-600 hover:underline">
                  <ExternalLink className="h-3 w-3" /> View Reference Image
                </a>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* 6. CROP DIARY */}
      <Section title="Crop Diary & Reminders" icon={BookOpen} color="bg-teal-50 text-teal-600">
        <div className="flex gap-2 mb-3 flex-wrap">
          <input value={diaryFarmerId} onChange={e => setDiaryFarmerId(e.target.value)} placeholder="Farmer ID"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-24" />
          <input value={diaryCrop} onChange={e => setDiaryCrop(e.target.value)} placeholder="Crop"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-28" />
          <select value={diaryActivity} onChange={e => setDiaryActivity(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            <option value="planted">Planted</option>
            <option value="irrigated">Irrigated</option>
            <option value="fertilized">Fertilized</option>
            <option value="sprayed">Sprayed</option>
            <option value="harvested">Harvested</option>
            <option value="sold">Sold</option>
          </select>
          <button onClick={() => diaryMutation.mutate()}
            className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700">Log Entry</button>
          <button onClick={() => { diaryQuery.refetch(); remindersQuery.refetch(); }}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300">View Diary</button>
        </div>
        {diaryMutation.data && (
          <p className="text-green-600 text-sm mb-2">Logged: {diaryMutation.data.crop} - {diaryMutation.data.activity} on {diaryMutation.data.date}</p>
        )}
        {remindersQuery.data?.length > 0 && (
          <div className="mb-3">
            <p className="font-medium text-sm text-amber-700 mb-1">Upcoming Reminders:</p>
            {remindersQuery.data.map((r: any) => (
              <div key={r.id} className={clsx('text-sm p-2 rounded mb-1', r.overdue ? 'bg-red-50 text-red-800' : 'bg-amber-50 text-amber-800')}>
                {r.overdue ? '⚠ OVERDUE' : r.due_date} | {r.crop} | {r.message}
              </div>
            ))}
          </div>
        )}
        {diaryQuery.data?.length > 0 && (
          <div className="space-y-1">
            <p className="font-medium text-sm text-gray-700">Diary Entries:</p>
            {diaryQuery.data.map((e: any) => (
              <p key={e.id} className="text-sm text-gray-600">{e.date} | {e.crop} | {e.activity} | {e.details}</p>
            ))}
          </div>
        )}
      </Section>

      {/* 7. FARMER REPORT */}
      <Section title="Farmer PDF Report" icon={FileText} color="bg-indigo-50 text-indigo-600">
        <div className="flex gap-2 mb-3">
          <input value={diaryFarmerId} onChange={e => setDiaryFarmerId(e.target.value)} placeholder="Farmer ID"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-24" />
          <button onClick={() => reportQuery.refetch()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">Generate Report</button>
        </div>
        {reportQuery.data?.report && (
          <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-xs overflow-x-auto whitespace-pre-wrap font-mono">
            {reportQuery.data.report}
          </pre>
        )}
      </Section>

      {/* 8. ONBOARDING */}
      <Section title="Farmer Onboarding" icon={UserPlus} color="bg-pink-50 text-pink-600">
        <p className="text-sm text-gray-500 mb-3">Quick registration flow for new farmers — creates profile with tips</p>
        <button onClick={async () => {
          const r = await api.post('/onboard', {
            name: 'Demo Farmer', preferred_language: 'hi', country: 'IN',
            region: 'Maharashtra', crops: ['Cotton', 'Soybean'], land_size_acres: 3,
            soil_type: 'black', irrigation_type: 'rainfed',
          });
          alert(`${r.data.welcome_message}\n\nTips:\n${r.data.tips.join('\n')}`);
        }} className="px-4 py-2 bg-pink-600 text-white rounded-lg text-sm font-medium hover:bg-pink-700">
          Try Demo Onboarding
        </button>
      </Section>
    </div>
  );
}
