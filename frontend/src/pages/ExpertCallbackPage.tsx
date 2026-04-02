import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { HeadphonesIcon, Clock, CheckCircle, AlertCircle, Loader2, Send } from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

export default function ExpertCallbackPage() {
  const [tab, setTab] = useState<'request' | 'queue'>('request');
  const [form, setForm] = useState({
    farmer_id: '', question: '', category: 'pest', language: 'hi', country: 'IN', region: '',
  });
  const [resolveForm, setResolveForm] = useState({ expert_name: '', response: '' });
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const statsQuery = useQuery({
    queryKey: ['expert-stats'],
    queryFn: () => api.get('/expert/stats').then(r => r.data),
  });

  const queueQuery = useQuery({
    queryKey: ['expert-queue'],
    queryFn: () => api.get('/expert/queue?status=pending&limit=20').then(r => r.data),
    enabled: tab === 'queue',
  });

  const requestMutation = useMutation({
    mutationFn: () => api.post('/expert/request', {
      ...form, farmer_id: parseInt(form.farmer_id) || 1,
    }).then(r => r.data),
    onSuccess: () => {
      statsQuery.refetch();
      setForm({ ...form, question: '' });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (ticketId: number) => api.post(`/expert/${ticketId}/resolve`, resolveForm).then(r => r.data),
    onSuccess: () => {
      queueQuery.refetch();
      statsQuery.refetch();
      setResolvingId(null);
      setResolveForm({ expert_name: '', response: '' });
    },
  });

  const s = statsQuery.data;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-violet-100 rounded-lg"><HeadphonesIcon className="h-6 w-6 text-violet-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Expert Callback</h1>
          <p className="text-gray-500 text-sm">When AI needs help, real agronomists step in within 48 hours</p>
        </div>
      </div>

      {/* Stats */}
      {s && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold">{s.total}</p>
            <p className="text-xs text-gray-500">Total Tickets</p>
          </div>
          <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 text-center">
            <p className="text-2xl font-bold text-amber-700">{s.pending}</p>
            <p className="text-xs text-amber-600">Pending</p>
          </div>
          <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
            <p className="text-2xl font-bold text-green-700">{s.resolved}</p>
            <p className="text-xs text-green-600">Resolved</p>
          </div>
          <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">{s.avg_resolution_hours}h</p>
            <p className="text-xs text-blue-600">Avg Response</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button onClick={() => setTab('request')}
          className={clsx('px-4 py-2 rounded-lg text-sm font-medium',
            tab === 'request' ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}>
          Request Callback
        </button>
        <button onClick={() => { setTab('queue'); queueQuery.refetch(); }}
          className={clsx('px-4 py-2 rounded-lg text-sm font-medium',
            tab === 'queue' ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}>
          Expert Queue {s?.pending ? `(${s.pending})` : ''}
        </button>
      </div>

      {tab === 'request' ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Request Expert Help</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Farmer ID</label>
                <input value={form.farmer_id} onChange={e => setForm({...form, farmer_id: e.target.value})} placeholder="1"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Category</label>
                <select value={form.category} onChange={e => setForm({...form, category: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option value="pest">Pest</option>
                  <option value="disease">Disease</option>
                  <option value="soil">Soil</option>
                  <option value="livestock">Livestock</option>
                  <option value="legal">Legal / Schemes</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Farmer's Question</label>
              <textarea value={form.question} onChange={e => setForm({...form, question: e.target.value})} rows={3}
                placeholder="Describe the problem in detail..."
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Language</label>
                <select value={form.language} onChange={e => setForm({...form, language: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option value="hi">Hindi</option><option value="en">English</option>
                  <option value="te">Telugu</option><option value="ta">Tamil</option><option value="sw">Swahili</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Country</label>
                <select value={form.country} onChange={e => setForm({...form, country: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option value="IN">India</option><option value="KE">Kenya</option>
                  <option value="NG">Nigeria</option><option value="ET">Ethiopia</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Region</label>
                <input value={form.region} onChange={e => setForm({...form, region: e.target.value})} placeholder="Maharashtra"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
            </div>
            <button onClick={() => requestMutation.mutate()} disabled={!form.question}
              className="px-6 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-50 flex items-center gap-2">
              {requestMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Submit Request
            </button>
            {requestMutation.data && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm">
                <p className="font-medium text-green-800">Ticket #{requestMutation.data.ticket_id} created!</p>
                <p className="text-green-700">{requestMutation.data.message}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Expert Queue */
        <div className="space-y-3">
          {queueQuery.data?.length === 0 && (
            <p className="text-center py-12 text-gray-400">No pending tickets</p>
          )}
          {queueQuery.data?.map((t: any) => (
            <div key={t.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full',
                    t.priority === 1 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600')}>
                    P{t.priority}
                  </span>
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{t.category}</span>
                  <span className="text-sm font-medium text-gray-900">#{t.id} — {t.farmer_name || `Farmer ${t.farmer_id}`}</span>
                </div>
                <span className="text-xs text-gray-400 flex items-center gap-1"><Clock className="h-3 w-3" />{t.created_at?.split('T')[0]}</span>
              </div>
              <p className="text-sm text-gray-800 mb-2">{t.question}</p>
              {t.ai_response && <p className="text-xs text-gray-500 italic mb-2">AI attempted: {t.ai_response}</p>}
              <div className="text-xs text-gray-400 mb-3">{t.region}, {t.country} | {t.language}</div>

              {resolvingId === t.id ? (
                <div className="border-t pt-3 space-y-2">
                  <input value={resolveForm.expert_name} onChange={e => setResolveForm({...resolveForm, expert_name: e.target.value})}
                    placeholder="Expert name (Dr. Sharma)" className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
                  <textarea value={resolveForm.response} onChange={e => setResolveForm({...resolveForm, response: e.target.value})}
                    placeholder="Expert response and advice..." rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
                  <div className="flex gap-2">
                    <button onClick={() => resolveMutation.mutate(t.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" /> Resolve
                    </button>
                    <button onClick={() => setResolvingId(null)}
                      className="px-4 py-2 bg-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-300">Cancel</button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setResolvingId(t.id)}
                  className="text-sm text-violet-600 hover:text-violet-800 font-medium">Respond to this ticket</button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
