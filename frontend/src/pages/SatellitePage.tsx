import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Satellite, Leaf, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

const LOCATIONS = ['Pune', 'Nagpur', 'Vidarbha', 'Hyderabad', 'Bangalore', 'Chennai', 'Kakamega', 'Kano', 'Nairobi', 'Indore'];
const CROPS = ['Tomato', 'Wheat', 'Rice', 'Cotton', 'Soybean', 'Maize', 'Onion', 'Sugarcane'];

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: typeof CheckCircle }> = {
  healthy:  { color: 'text-green-700', bg: 'bg-green-50 border-green-200', icon: CheckCircle },
  moderate: { color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200', icon: AlertTriangle },
  stressed: { color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200', icon: AlertTriangle },
  critical: { color: 'text-red-700', bg: 'bg-red-50 border-red-200', icon: XCircle },
};

export default function SatellitePage() {
  const [location, setLocation] = useState('Pune');
  const [crop, setCrop] = useState('Tomato');
  const [farmerId, setFarmerId] = useState('');

  const analyzeMutation = useMutation({
    mutationFn: () => api.post('/satellite/analyze', {
      location,
      crop,
      farmer_id: farmerId ? parseInt(farmerId) : null,
      country: 'IN',
    }).then(r => r.data),
  });

  const historyQuery = useQuery({
    queryKey: ['satellite-history', farmerId],
    queryFn: () => api.get(`/satellite/history/${farmerId}`).then(r => r.data),
    enabled: false,
  });

  const d = analyzeMutation.data;
  const sc = d ? STATUS_CONFIG[d.health_status] || STATUS_CONFIG.moderate : null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-indigo-100 rounded-lg"><Satellite className="h-6 w-6 text-indigo-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Satellite Crop Health</h1>
          <p className="text-gray-500 text-sm">NDVI-based vegetation analysis — detect stress before you see it</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <div className="flex gap-3 flex-wrap items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Location</label>
            <select value={location} onChange={e => setLocation(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              {LOCATIONS.map(l => <option key={l}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Crop</label>
            <select value={crop} onChange={e => setCrop(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              {CROPS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Farmer ID (optional)</label>
            <input value={farmerId} onChange={e => setFarmerId(e.target.value)} placeholder="e.g. 1"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-24" />
          </div>
          <button onClick={() => analyzeMutation.mutate()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 flex items-center gap-2">
            {analyzeMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Satellite className="h-4 w-4" />}
            Analyze Field
          </button>
          {farmerId && (
            <button onClick={() => historyQuery.refetch()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300">History</button>
          )}
        </div>
      </div>

      {d && sc && (
        <div className="space-y-4">
          {/* NDVI Score Card */}
          <div className={clsx('rounded-xl border-2 p-6', sc.bg)}>
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <sc.icon className={clsx('h-6 w-6', sc.color)} />
                  <span className={clsx('text-lg font-bold uppercase', sc.color)}>{d.health_status}</span>
                  {d.alert_level !== 'none' && (
                    <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium',
                      d.alert_level === 'critical' ? 'bg-red-200 text-red-800' :
                      d.alert_level === 'warning' ? 'bg-orange-200 text-orange-800' :
                      'bg-yellow-200 text-yellow-800')}>
                      {d.alert_level} alert
                    </span>
                  )}
                </div>
                <p className="text-gray-700 text-sm">{d.analysis}</p>
              </div>
              <div className="text-center">
                <div className="relative w-24 h-24">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke={d.ndvi_score >= 0.6 ? '#16a34a' : d.ndvi_score >= 0.4 ? '#f59e0b' : d.ndvi_score >= 0.2 ? '#ea580c' : '#dc2626'}
                      strokeWidth="8" strokeDasharray={`${d.ndvi_score * 251} 251`} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xl font-bold">{d.ndvi_score}</span>
                    <span className="text-[10px] text-gray-500">NDVI</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Regional Comparison */}
          {d.regional_comparison && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Regional Comparison</h3>
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{d.regional_comparison.your_ndvi}</p>
                  <p className="text-xs text-gray-500">Your Field</p>
                </div>
                <div className="text-sm text-gray-500">vs</div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-400">{d.regional_comparison.region_average}</p>
                  <p className="text-xs text-gray-500">Region Avg</p>
                </div>
                <div className="flex-1 text-sm text-gray-600">{d.regional_comparison.comparison}</div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {d.recommendations?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {d.recommendations.map((r: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Leaf className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                    <span className="text-gray-700">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* History */}
      {historyQuery.data?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mt-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Monitoring History</h3>
          <div className="space-y-2">
            {historyQuery.data.map((r: any) => (
              <div key={r.id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg text-sm">
                <span className="text-gray-400 w-24">{r.satellite_date}</span>
                <span className={clsx('font-medium w-20',
                  r.health_status === 'healthy' ? 'text-green-600' :
                  r.health_status === 'moderate' ? 'text-amber-600' :
                  r.health_status === 'stressed' ? 'text-orange-600' : 'text-red-600')}>
                  {r.ndvi_score} ({r.health_status})
                </span>
                <span className="text-gray-500 flex-1 truncate">{r.crop}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
