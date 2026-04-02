import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ShoppingCart, Plus, Search, Loader2, Phone, MapPin, Tag } from 'lucide-react';
import clsx from 'clsx';
import api from '../api/client';

export default function MarketplacePage() {
  const [tab, setTab] = useState<'browse' | 'create'>('browse');
  const [filterCrop, setFilterCrop] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterRegion, setFilterRegion] = useState('');

  // Form state
  const [form, setForm] = useState({
    farmer_id: '', listing_type: 'sell', crop: '', quantity: '',
    price_per_unit: '', region: '', description: '', phone_number: '',
  });

  const listingsQuery = useQuery({
    queryKey: ['marketplace', filterCrop, filterType, filterRegion],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filterCrop) params.set('crop', filterCrop);
      if (filterType) params.set('listing_type', filterType);
      if (filterRegion) params.set('region', filterRegion);
      return api.get(`/marketplace/listings?${params}`).then(r => r.data);
    },
  });

  const statsQuery = useQuery({
    queryKey: ['marketplace-stats'],
    queryFn: () => api.get('/marketplace/stats').then(r => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/marketplace/listings', {
      ...form,
      farmer_id: parseInt(form.farmer_id) || 1,
      price_per_unit: form.price_per_unit ? parseFloat(form.price_per_unit) : null,
    }).then(r => r.data),
    onSuccess: () => {
      listingsQuery.refetch();
      statsQuery.refetch();
      setTab('browse');
    },
  });

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg"><ShoppingCart className="h-6 w-6 text-orange-600" /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Farmer Marketplace</h1>
            <p className="text-gray-500 text-sm">Buy and sell crops directly — no middleman</p>
          </div>
        </div>
        <button onClick={() => setTab(tab === 'create' ? 'browse' : 'create')}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 flex items-center gap-2">
          <Plus className="h-4 w-4" /> {tab === 'create' ? 'Browse' : 'New Listing'}
        </button>
      </div>

      {/* Stats */}
      {statsQuery.data && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl border p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{statsQuery.data.total_listings}</p>
            <p className="text-xs text-gray-500">Total Listings</p>
          </div>
          <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
            <p className="text-2xl font-bold text-green-700">{statsQuery.data.sell_listings}</p>
            <p className="text-xs text-green-600">Selling</p>
          </div>
          <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">{statsQuery.data.buy_listings}</p>
            <p className="text-xs text-blue-600">Buying</p>
          </div>
        </div>
      )}

      {tab === 'create' ? (
        /* Create Listing Form */
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold mb-4">Create Listing</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
              <select value={form.listing_type} onChange={e => setForm({...form, listing_type: e.target.value})}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                <option value="sell">Sell</option>
                <option value="buy">Buy</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Crop</label>
              <input value={form.crop} onChange={e => setForm({...form, crop: e.target.value})} placeholder="e.g. Tomato"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Quantity</label>
              <input value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} placeholder="e.g. 10 quintals"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Price per quintal (Rs)</label>
              <input value={form.price_per_unit} onChange={e => setForm({...form, price_per_unit: e.target.value})} placeholder="e.g. 2500"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Region</label>
              <input value={form.region} onChange={e => setForm({...form, region: e.target.value})} placeholder="e.g. Maharashtra"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Phone Number</label>
              <input value={form.phone_number} onChange={e => setForm({...form, phone_number: e.target.value})} placeholder="+91..."
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
              <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})}
                placeholder="Quality, grade, harvest date..." rows={2}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Farmer ID</label>
              <input value={form.farmer_id} onChange={e => setForm({...form, farmer_id: e.target.value})} placeholder="1"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <button onClick={() => createMutation.mutate()} disabled={!form.crop || !form.quantity || !form.region}
            className="mt-4 px-6 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 disabled:opacity-50 flex items-center gap-2">
            {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Post Listing
          </button>
          {createMutation.data && (
            <p className="mt-2 text-sm text-green-600">{createMutation.data.message}</p>
          )}
        </div>
      ) : (
        /* Browse Listings */
        <>
          <div className="flex gap-3 mb-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input value={filterCrop} onChange={e => setFilterCrop(e.target.value)} placeholder="Search by crop..."
                className="w-full pl-9 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <select value={filterType} onChange={e => setFilterType(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
              <option value="">All Types</option>
              <option value="sell">Selling</option>
              <option value="buy">Buying</option>
            </select>
            <input value={filterRegion} onChange={e => setFilterRegion(e.target.value)} placeholder="Region..."
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-40" />
          </div>

          <div className="space-y-3">
            {listingsQuery.data?.length === 0 && (
              <p className="text-center py-12 text-gray-400">No listings found. Create the first one!</p>
            )}
            {listingsQuery.data?.map((l: any) => (
              <div key={l.id} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full',
                        l.type === 'sell' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700')}>
                        {l.type === 'sell' ? 'SELLING' : 'BUYING'}
                      </span>
                      <h3 className="font-semibold text-gray-900">{l.crop}</h3>
                    </div>
                    <p className="text-sm text-gray-600">{l.quantity}</p>
                    {l.description && <p className="text-sm text-gray-500 mt-1">{l.description}</p>}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      {l.farmer_name && <span>{l.farmer_name}</span>}
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{l.region}{l.district ? `, ${l.district}` : ''}</span>
                      {l.phone && <span className="flex items-center gap-1"><Phone className="h-3 w-3" />{l.phone}</span>}
                    </div>
                  </div>
                  {l.price_per_unit && (
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">Rs {l.price_per_unit?.toLocaleString()}</p>
                      <p className="text-xs text-gray-500">per {l.unit || 'quintal'}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
