import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Users, ThumbsUp, TrendingUp, MessageCircle, Search, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

export default function FarmerNetworkPage() {
  const [tab, setTab] = useState<'questions' | 'trending' | 'share'>('questions');
  const [filterRegion, setFilterRegion] = useState('');
  const [filterCrop, setFilterCrop] = useState('');
  const [filterCountry, setFilterCountry] = useState('IN');

  const [shareForm, setShareForm] = useState({
    region: 'Maharashtra', country: 'IN', crop: '', question_summary: '', ai_answer: '', category: 'pest',
  });

  const questionsQuery = useQuery({
    queryKey: ['community-questions', filterRegion, filterCrop, filterCountry],
    queryFn: () => {
      const params = new URLSearchParams({ country: filterCountry });
      if (filterRegion) params.set('region', filterRegion);
      if (filterCrop) params.set('crop', filterCrop);
      return api.get(`/community/questions?${params}`).then(r => r.data);
    },
  });

  const trendingQuery = useQuery({
    queryKey: ['trending', filterCountry],
    queryFn: () => api.get(`/community/trending?country=${filterCountry}`).then(r => r.data),
    enabled: tab === 'trending',
  });

  const helpfulMutation = useMutation({
    mutationFn: (id: number) => api.post(`/community/questions/${id}/helpful`).then(r => r.data),
    onSuccess: () => questionsQuery.refetch(),
  });

  const shareMutation = useMutation({
    mutationFn: () => api.post('/community/share', shareForm).then(r => r.data),
    onSuccess: () => {
      questionsQuery.refetch();
      setTab('questions');
      setShareForm({ ...shareForm, question_summary: '', ai_answer: '', crop: '' });
    },
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-cyan-100 rounded-lg"><Users className="h-6 w-6 text-cyan-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Farmer Network</h1>
          <p className="text-gray-500 text-sm">Learn from nearby farmers — see what problems they face and what works</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'questions' as const, label: 'Community Q&A', icon: MessageCircle },
          { id: 'trending' as const, label: 'Trending', icon: TrendingUp },
          { id: 'share' as const, label: 'Share Knowledge', icon: Users },
        ].map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); if (t.id === 'trending') trendingQuery.refetch(); }}
            className={clsx('px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2',
              tab === t.id ? 'bg-cyan-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}>
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'questions' && (
        <>
          {/* Filters */}
          <div className="flex gap-3 mb-4 flex-wrap">
            <select value={filterCountry} onChange={e => setFilterCountry(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              <option value="IN">India</option><option value="KE">Kenya</option>
              <option value="NG">Nigeria</option><option value="ET">Ethiopia</option>
            </select>
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input value={filterRegion} onChange={e => setFilterRegion(e.target.value)} placeholder="Filter by region..."
                className="w-full pl-9 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <input value={filterCrop} onChange={e => setFilterCrop(e.target.value)} placeholder="Filter by crop..."
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-40" />
          </div>

          {/* Questions */}
          <div className="space-y-3">
            {questionsQuery.data?.length === 0 && (
              <p className="text-center py-12 text-gray-400">No community questions yet. Be the first to share!</p>
            )}
            {questionsQuery.data?.map((q: any) => (
              <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow">
                <div className="flex items-start gap-4">
                  <button onClick={() => helpfulMutation.mutate(q.id)}
                    className="flex flex-col items-center gap-1 mt-1 group shrink-0">
                    <ThumbsUp className={clsx('h-5 w-5 transition-colors',
                      q.helpful_count > 0 ? 'text-cyan-500' : 'text-gray-300 group-hover:text-cyan-400')} />
                    <span className="text-xs font-medium text-gray-500">{q.helpful_count}</span>
                  </button>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {q.category && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{q.category}</span>
                      )}
                      {q.crop && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">{q.crop}</span>
                      )}
                      <span className="text-xs text-gray-400">{q.region}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-900 mb-2">{q.question}</p>
                    <div className="bg-green-50 rounded-lg p-3 text-sm text-green-800">
                      <p className="text-xs text-green-600 font-medium mb-1">AI Answer:</p>
                      {q.answer}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'trending' && (
        <div className="space-y-3">
          {trendingQuery.data?.length === 0 && (
            <p className="text-center py-12 text-gray-400">No trending topics yet</p>
          )}
          {trendingQuery.data?.map((t: any, i: number) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
              <div className="text-2xl font-bold text-gray-300 w-8">#{i + 1}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {t.category && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{t.category}</span>}
                  {t.crop && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">{t.crop}</span>}
                </div>
                <p className="text-sm text-gray-600">{t.region}</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-gray-900">{t.report_count}</p>
                <p className="text-xs text-gray-500">reports</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'share' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Share Your Farming Knowledge</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Region</label>
                <input value={shareForm.region} onChange={e => setShareForm({...shareForm, region: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Crop</label>
                <input value={shareForm.crop} onChange={e => setShareForm({...shareForm, crop: e.target.value})} placeholder="Tomato"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Category</label>
                <select value={shareForm.category} onChange={e => setShareForm({...shareForm, category: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option value="pest">Pest</option><option value="disease">Disease</option>
                  <option value="fertilizer">Fertilizer</option><option value="weather">Weather</option>
                  <option value="market">Market</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Question</label>
              <textarea value={shareForm.question_summary} onChange={e => setShareForm({...shareForm, question_summary: e.target.value})}
                rows={2} placeholder="What problem did you face?" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Solution / Answer</label>
              <textarea value={shareForm.ai_answer} onChange={e => setShareForm({...shareForm, ai_answer: e.target.value})}
                rows={3} placeholder="What worked for you?" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <button onClick={() => shareMutation.mutate()} disabled={!shareForm.question_summary || !shareForm.ai_answer}
              className="px-6 py-2 bg-cyan-600 text-white rounded-lg text-sm font-medium hover:bg-cyan-700 disabled:opacity-50 flex items-center gap-2">
              {shareMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
              Share with Community
            </button>
            {shareMutation.data && <p className="text-sm text-green-600">Shared successfully!</p>}
          </div>
        </div>
      )}
    </div>
  );
}
