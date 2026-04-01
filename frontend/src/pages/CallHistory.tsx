import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Phone, Globe, MessageSquare, Monitor } from 'lucide-react';
import clsx from 'clsx';
import { getCalls } from '../api/analytics';

const LANG_NAMES: Record<string, string> = {
  hi: 'Hindi', te: 'Telugu', ta: 'Tamil', sw: 'Swahili', en: 'English',
};

export default function CallHistory() {
  const [langFilter, setLangFilter] = useState<string | undefined>();
  const { data: calls, isLoading } = useQuery({
    queryKey: ['calls', langFilter],
    queryFn: () => getCalls(0, 100, langFilter),
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Filter:</span>
          <button
            onClick={() => setLangFilter(undefined)}
            className={clsx(
              'px-3 py-1 rounded-lg text-sm',
              !langFilter ? 'bg-primary-100 text-primary-800' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            All
          </button>
          {['hi', 'te', 'ta', 'sw', 'en'].map(l => (
            <button
              key={l}
              onClick={() => setLangFilter(langFilter === l ? undefined : l)}
              className={clsx(
                'px-3 py-1 rounded-lg text-sm',
                langFilter === l ? 'bg-primary-100 text-primary-800' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {LANG_NAMES[l]}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-gray-500 text-center py-8">Loading...</p>}

      {calls && calls.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No calls yet</h3>
          <p className="text-gray-500">Try the voice demo to generate call logs.</p>
        </div>
      )}

      <div className="space-y-3">
        {calls?.map((call) => (
          <div key={call.id} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={clsx(
                  'p-2 rounded-lg',
                  call.source === 'phone' ? 'bg-green-50' : 'bg-blue-50'
                )}>
                  {call.source === 'phone'
                    ? <Phone className="h-4 w-4 text-green-600" />
                    : <Monitor className="h-4 w-4 text-blue-600" />
                  }
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">{call.source === 'phone' ? 'Phone Call' : 'Web Demo'}</span>
                    <span className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded text-xs font-medium flex items-center gap-1">
                      <Globe className="h-3 w-3" />
                      {LANG_NAMES[call.language] || call.language}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">{call.created_at}</p>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Farmer's Question</p>
                <p className="text-sm text-gray-800 bg-gray-50 rounded-lg p-3">{call.farmer_question}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-green-600 mb-1">AI Response</p>
                <p className="text-sm text-gray-800 bg-green-50 rounded-lg p-3 leading-relaxed">
                  {call.ai_response.length > 300 ? call.ai_response.slice(0, 300) + '...' : call.ai_response}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
