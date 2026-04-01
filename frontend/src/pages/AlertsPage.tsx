import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Bell, TrendingUp, Users, ShieldAlert, Info } from 'lucide-react';
import clsx from 'clsx';
import { getAlerts, getCommunityInsights } from '../api/analytics';

const SEVERITY_CONFIG: Record<string, { bg: string; icon: typeof AlertTriangle }> = {
  critical: { bg: 'bg-red-50 border-red-200 text-red-800', icon: ShieldAlert },
  warning: { bg: 'bg-amber-50 border-amber-200 text-amber-800', icon: AlertTriangle },
  info: { bg: 'bg-blue-50 border-blue-200 text-blue-800', icon: Info },
};

const COUNTRIES = [
  { code: undefined as string | undefined, label: 'All' },
  { code: 'IN', label: '🇮🇳 India' },
  { code: 'KE', label: '🇰🇪 Kenya' },
  { code: 'NG', label: '🇳🇬 Nigeria' },
  { code: 'ET', label: '🇪🇹 Ethiopia' },
];

export default function AlertsPage() {
  const [country, setCountry] = useState<string | undefined>();
  const { data: alerts } = useQuery({ queryKey: ['alerts', country], queryFn: () => getAlerts(country) });
  const { data: insights } = useQuery({ queryKey: ['community', country], queryFn: () => getCommunityInsights(country) });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts & Community Intelligence</h1>
          <p className="text-sm text-gray-500 mt-1">Proactive warnings and crowdsourced insights from farmers</p>
        </div>
        <div className="flex gap-2">
          {COUNTRIES.map((c) => (
            <button
              key={c.label}
              onClick={() => setCountry(c.code)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium',
                country === c.code ? 'bg-primary-100 text-primary-800' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Alerts */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Bell className="h-5 w-5 text-red-600" />
            <h2 className="text-lg font-semibold text-gray-900">Active Alerts</h2>
          </div>
          <div className="space-y-3">
            {alerts?.length === 0 && (
              <p className="text-gray-400 text-center py-8">No active alerts</p>
            )}
            {alerts?.map((alert) => {
              const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
              const Icon = config.icon;
              return (
                <div key={alert.id} className={clsx('rounded-xl border p-4', config.bg)}>
                  <div className="flex items-start gap-3">
                    <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-sm">{alert.title}</h3>
                        <span className="px-2 py-0.5 bg-white/50 rounded text-xs font-medium">{alert.alert_type}</span>
                      </div>
                      <p className="text-sm mt-1 opacity-90">{alert.message}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs opacity-70">
                        {alert.source && <span>Source: {alert.source}</span>}
                        {alert.affected_crops.length > 0 && (
                          <span>Crops: {alert.affected_crops.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Community Intelligence */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-5 w-5 text-purple-600" />
            <h2 className="text-lg font-semibold text-gray-900">Community Intelligence</h2>
          </div>
          <div className="space-y-3">
            {insights?.length === 0 && (
              <p className="text-gray-400 text-center py-8">No community insights yet</p>
            )}
            {insights?.map((insight) => (
              <div key={insight.id} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{insight.topic}</h3>
                      {insight.trending && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs font-medium">
                          <TrendingUp className="h-3 w-3" /> Trending
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {insight.region} {insight.affected_crop ? `• ${insight.affected_crop}` : ''}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-primary-700">{insight.farmer_count}</p>
                    <p className="text-xs text-gray-400">farmers</p>
                  </div>
                </div>
                {insight.ai_summary && (
                  <p className="mt-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">{insight.ai_summary}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
