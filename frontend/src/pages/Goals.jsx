import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'

function GoalCard({ goal }) {
  const { data: a } = useQuery({
    queryKey: ['goal', goal.id],
    queryFn: () => apiClient.get(`/goals/${goal.id}/analysis`).then(r => r.data)
  })
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold">{goal.name}</h3>
        {a && (
          <span className={`text-xs px-2 py-1 rounded-full ${a.achievable ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {a.achievable ? 'Ulasılabilir' : 'Eksik var'}
          </span>
        )}
      </div>
      {a && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><p className="text-gray-400 text-xs">Hedef</p><p className="font-medium">{goal.target_amount.toLocaleString()} TL</p></div>
          <div><p className="text-gray-400 text-xs">Kalan sure</p><p className="font-medium">{a.months_left} ay</p></div>
          <div><p className="text-gray-400 text-xs">Aylik birikim</p><p className="font-medium text-blue-600">{a.required_monthly.toLocaleString()} TL</p></div>
          <div><p className="text-gray-400 text-xs">Mevcut arti</p><p className={`font-medium ${a.achievable ? 'text-green-600' : 'text-red-600'}`}>{a.current_surplus.toLocaleString()} TL</p></div>
          {!a.achievable && (
            <p className="col-span-2 text-xs text-red-600 bg-red-50 rounded-lg p-2 mt-1">
              Aylik {a.shortfall_monthly.toLocaleString()} TL eksik.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Goals() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ name: '', target_amount: '', target_date: '' })
  const { data: goals } = useQuery({ queryKey: ['goals'], queryFn: () => apiClient.get('/goals').then(r => r.data) })
  const createMutation = useMutation({
    mutationFn: (d) => apiClient.post('/goals', d),
    onSuccess: () => { qc.invalidateQueries(['goals']); setForm({ name:'', target_amount:'', target_date:'' }) }
  })

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Birikim Hedefleri</h1>
      <div className="bg-white rounded-2xl p-6 shadow-sm border mb-6">
        <h2 className="font-semibold mb-4">Yeni Hedef</h2>
        <input className="w-full border rounded-lg p-2 mb-3" placeholder="Hedef adi"
          value={form.name} onChange={e => setForm({...form, name: e.target.value})}/>
        <input className="w-full border rounded-lg p-2 mb-3" placeholder="Hedef tutar (TL)" type="number"
          value={form.target_amount} onChange={e => setForm({...form, target_amount: e.target.value})}/>
        <input className="w-full border rounded-lg p-2 mb-4" type="date"
          value={form.target_date} onChange={e => setForm({...form, target_date: e.target.value})}/>
        <button onClick={() => createMutation.mutate(form)}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700">
          Hedef Olustur
        </button>
      </div>
      <div className="space-y-4">
        {goals?.map(g => <GoalCard key={g.id} goal={g}/>)}
      </div>
    </div>
  )
}
