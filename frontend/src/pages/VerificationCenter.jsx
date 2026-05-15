import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'
import { TransactionCard } from '../components/TransactionCard'

export default function VerificationCenter() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState('all')

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiClient.get('/transactions/categories').then(r => r.data)
  })

  const { data, isLoading } = useQuery({
    queryKey: ['pending'],
    queryFn: () => apiClient.get('/analytics/pending-review').then(r => r.data)
  })

  const verifyMutation = useMutation({
    mutationFn: ({ id, body }) => apiClient.patch(`/transactions/${id}/verify`, body),
    onSuccess: () => qc.invalidateQueries(['pending'])
  })

  const bulkMutation = useMutation({
    mutationFn: (ids) => apiClient.patch('/transactions/bulk-verify', { transaction_ids: ids }),
    onSuccess: () => qc.invalidateQueries(['pending'])
  })

  if (isLoading) return <div className="p-8 text-center text-gray-400">Yukleniyor...</div>

  const pending  = data?.pending || []
  const highConf = pending.filter(t => t.confidence >= 0.80)
  const lowConf  = pending.filter(t => t.confidence < 0.80)
  const shown    = filter === 'low' ? lowConf : pending

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dogrulama Merkezi</h1>
          <p className="text-sm text-gray-500 mt-1">AI'in cikardigi islemleri kontrol et ve onayla</p>
        </div>
        <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm font-medium">
          {pending.length} islem bekliyor
        </span>
      </div>

      <div className="flex gap-3 mb-6">
        {highConf.length > 0 && (
          <button
            onClick={() => bulkMutation.mutate(highConf.map(t => t.id))}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
          >
            Yuksek guvenilirlikli {highConf.length} islemi onayla
          </button>
        )}
        <button
          onClick={() => setFilter(filter === 'low' ? 'all' : 'low')}
          className="border px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          {filter === 'low' ? 'Tumunu goster' : `Sadece belirsizleri goster (${lowConf.length})`}
        </button>
      </div>

      <div className="space-y-3">
        {shown.map(tx => (
          <TransactionCard
            key={tx.id}
            transaction={tx}
            categories={categories}
            onVerify={(body) => verifyMutation.mutate({ id: tx.id, body })}
          />
        ))}
        {shown.length === 0 && (
          <div className="text-center py-12 text-gray-400">Tum islemler onaylandi!</div>
        )}
      </div>
    </div>
  )
}
