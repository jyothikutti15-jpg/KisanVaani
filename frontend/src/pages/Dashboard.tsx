import { useQuery } from '@tanstack/react-query';
import { Phone, Users, Globe, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getOverview, getLanguageStats, getTimeline } from '../api/analytics';

const COLORS = ['#16a34a', '#eab308', '#3b82f6', '#ef4444', '#8b5cf6'];

export default function Dashboard() {
  const { data: overview } = useQuery({ queryKey: ['overview'], queryFn: getOverview });
  const { data: languages } = useQuery({ queryKey: ['languages'], queryFn: getLanguageStats });
  const { data: timeline } = useQuery({ queryKey: ['timeline'], queryFn: () => getTimeline(30) });

  const stats = [
    { label: 'Total Calls', value: overview?.total_calls ?? 0, icon: Phone, color: 'bg-primary-50 text-primary-600' },
    { label: 'Unique Sessions', value: overview?.unique_sessions ?? 0, icon: Users, color: 'bg-blue-50 text-blue-600' },
    { label: 'Languages Served', value: overview?.languages_served ?? 0, icon: Globe, color: 'bg-purple-50 text-purple-600' },
    { label: 'Calls Today', value: overview?.calls_today ?? 0, icon: TrendingUp, color: 'bg-earth-50 text-earth-600' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-2xl font-bold text-gray-900">{value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Call timeline */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Calls Over Time (30 days)</h2>
          {timeline && timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={timeline}>
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#16a34a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-400">
              No call data yet. Try the demo to generate some calls!
            </div>
          )}
        </div>

        {/* Language breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Language Breakdown</h2>
          {languages && languages.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={languages}
                    dataKey="count"
                    nameKey="language_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ language_name, percentage }) => `${language_name} ${percentage}%`}
                  >
                    {languages.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {languages.map((lang, i) => (
                  <div key={lang.language} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-sm text-gray-700">{lang.language_name}</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{lang.count} ({lang.percentage}%)</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-gray-400 text-sm">
              No language data yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
