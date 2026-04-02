import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Minus, Loader2, BarChart3, ArrowRight } from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

const CROPS = ['Wheat', 'Rice', 'Tomato', 'Onion', 'Cotton', 'Soybean', 'Maize', 'Potato', 'Groundnut', 'Sugarcane'];

export default function PricePredictionPage() {
  const [crop, setCrop] = useState('Tomato');
  const [days, setDays] = useState(14);

  const predictionQuery = useQuery({
    queryKey: ['price-predict', crop, days],
    queryFn: () => api.get(`/prices/predict/${crop}?days=${days}`).then(r => r.data),
    enabled: false,
  });

  const trendsQuery = useQuery({
    queryKey: ['price-trends', crop],
    queryFn: () => api.get(`/prices/trends/${crop}?days=30`).then(r => r.data),
    enabled: false,
  });

  const handlePredict = () => {
    predictionQuery.refetch();
    trendsQuery.refetch();
  };

  const d = predictionQuery.data;
  const isUp = d && d.change_percent > 0;
  const isDown = d && d.change_percent < 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-emerald-100 rounded-lg"><TrendingUp className="h-6 w-6 text-emerald-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Price Predictor</h1>
          <p className="text-gray-500 text-sm">Predict mandi prices and get sell/hold recommendations</p>
        </div>
      </div>

      {/* Input Controls */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <div className="flex gap-3 flex-wrap items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Crop</label>
            <select value={crop} onChange={e => setCrop(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Predict for</label>
            <select value={days} onChange={e => setDays(Number(e.target.value))}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={21}>21 days</option>
              <option value={28}>28 days</option>
            </select>
          </div>
          <button onClick={handlePredict}
            className="px-6 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 flex items-center gap-2">
            {predictionQuery.isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
            Predict Price
          </button>
        </div>
      </div>

      {/* Prediction Result */}
      {d && (
        <div className="space-y-4">
          {/* Main Price Card */}
          <div className={clsx('rounded-xl border-2 p-6',
            isUp ? 'border-green-200 bg-green-50' : isDown ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50')}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm text-gray-500 font-medium">{d.crop} — Current Price</p>
                <p className="text-3xl font-bold text-gray-900">Rs {d.current_price?.toLocaleString()}<span className="text-lg text-gray-500">/quintal</span></p>
              </div>
              <div className="flex items-center gap-3">
                <ArrowRight className="h-5 w-5 text-gray-400" />
                <div className="text-right">
                  <p className="text-sm text-gray-500 font-medium">Predicted ({d.days_ahead} days)</p>
                  <p className="text-3xl font-bold">{d.predicted_price?.toLocaleString()}</p>
                  <p className={clsx('text-sm font-medium', isUp ? 'text-green-600' : isDown ? 'text-red-600' : 'text-gray-600')}>
                    {isUp ? <TrendingUp className="h-3 w-3 inline" /> : isDown ? <TrendingDown className="h-3 w-3 inline" /> : <Minus className="h-3 w-3 inline" />}
                    {' '}{d.change_percent > 0 ? '+' : ''}{d.change_percent}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendation */}
          <div className={clsx('rounded-xl p-5 border',
            d.recommendation?.includes('HOLD') ? 'bg-amber-50 border-amber-200' :
            d.recommendation?.includes('SELL NOW') ? 'bg-red-50 border-red-200' :
            d.recommendation?.includes('SELL') ? 'bg-orange-50 border-orange-200' :
            'bg-blue-50 border-blue-200')}>
            <p className="text-lg font-bold mb-1">{d.recommendation}</p>
            <p className="text-sm text-gray-700">{d.reason}</p>
            <div className="flex gap-4 mt-3 text-xs text-gray-500">
              <span>Confidence: <strong>{d.confidence}</strong></span>
              <span>Method: {d.method}</span>
              <span>Range: Rs {d.predicted_range?.low?.toLocaleString()} - {d.predicted_range?.high?.toLocaleString()}</span>
            </div>
          </div>

          {/* Weekly Forecast */}
          {d.weekly_forecast?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Weekly Forecast</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {d.weekly_forecast.map((w: any) => (
                  <div key={w.week} className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500">Week {w.week}</p>
                    <p className="text-lg font-bold">Rs {w.predicted_price?.toLocaleString()}</p>
                    <p className="text-xs text-gray-400">{w.date}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price History */}
          {trendsQuery.data?.prices?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">30-Day Price History</h3>
              <div className="overflow-x-auto">
                <div className="flex items-end gap-1 h-32 min-w-[600px]">
                  {trendsQuery.data.prices.map((p: any, i: number) => {
                    const prices = trendsQuery.data.prices.map((x: any) => x.price);
                    const max = Math.max(...prices);
                    const min = Math.min(...prices);
                    const range = max - min || 1;
                    const height = ((p.price - min) / range) * 100 + 10;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center justify-end group relative">
                        <div className="absolute -top-6 hidden group-hover:block bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap z-10">
                          {p.date}: Rs {p.price}
                        </div>
                        <div className="w-full bg-emerald-400 hover:bg-emerald-500 rounded-t transition-colors" style={{ height: `${height}%` }} />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
