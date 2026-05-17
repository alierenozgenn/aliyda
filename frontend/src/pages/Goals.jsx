import { useState, useEffect } from 'react'
import { upsertMonthlyProfile } from '../services/api'
import { Target } from 'lucide-react'

const MONTHS = ['2026-05', '2026-04', '2026-03', '2026-02']

export default function Goals() {
  const [month, setMonth] = useState('2026-05')
  const [form, setForm] = useState({ declared_income: '', savings_goal: '', budget_goal: '' })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    try {
      await upsertMonthlyProfile(month, {
        month,
        declared_income: Number(form.declared_income),
        savings_goal: form.savings_goal ? Number(form.savings_goal) : null,
        budget_goal: form.budget_goal ? Number(form.budget_goal) : null,
      })
      setMessage('✅ Kaydedildi. Dashboard güncellendi.')
    } catch {
      setMessage('❌ Kayıt başarısız.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
        <Target size={22} className="text-violet-400" />
        Aylık Hedefler
      </h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Ay</label>
            <select
              value={month}
              onChange={e => setMonth(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
            >
              {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Aylık Gelir (₺)</label>
            <input
              type="number"
              value={form.declared_income}
              onChange={e => setForm(f => ({ ...f, declared_income: e.target.value }))}
              required
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              placeholder="30000"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Tasarruf Hedefi (₺, opsiyonel)</label>
            <input
              type="number"
              value={form.savings_goal}
              onChange={e => setForm(f => ({ ...f, savings_goal: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              placeholder="5000"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Bütçe Hedefi (₺, opsiyonel)</label>
            <input
              type="number"
              value={form.budget_goal}
              onChange={e => setForm(f => ({ ...f, budget_goal: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              placeholder="20000"
            />
          </div>

          {message && <p className="text-sm text-gray-300">{message}</p>}

          <button
            type="submit"
            disabled={saving || !form.declared_income}
            className="w-full bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </form>
      </div>
    </div>
  )
}
