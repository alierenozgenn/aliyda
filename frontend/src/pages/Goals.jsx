import { useState } from 'react'
import { upsertMonthlyProfile } from '../services/api'
import { Target, TrendingUp, PiggyBank, Wallet } from 'lucide-react'

function buildMonths() {
  const months = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}
const MONTHS = buildMonths()

export default function Goals() {
  const [month, setMonth] = useState(MONTHS[0])
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
      setTimeout(() => setMessage(''), 4000)
    } catch {
      setMessage('❌ Kayıt başarısız.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-6 py-8 lg:px-8">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-2">
        <Target size={22} className="text-violet-400" />
        Aylık Hedefler
      </h1>
      <p className="text-gray-400 text-sm mb-6">
        PDF'de gelir tespit edilemezse buradan aylık gelirinizi girin. Tasarruf ve bütçe hedeflerinizi belirleyin.
      </p>

      <div className="glass-panel rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5 font-medium">Ay</label>
            <select
              value={month}
              onChange={e => setMonth(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-violet-500 transition-colors"
            >
              {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-1.5 font-medium flex items-center gap-2">
              <TrendingUp size={14} className="text-emerald-400" />
              Aylık Gelir (₺) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              value={form.declared_income}
              onChange={e => setForm(f => ({ ...f, declared_income: e.target.value }))}
              required
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-violet-500 transition-colors"
              placeholder="Ör: 30000"
            />
            <p className="text-gray-600 text-xs mt-1">
              Banka ekstresinde gelir bulunamazsa bu değer kullanılır.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400 mb-1.5 font-medium flex items-center gap-2">
                <PiggyBank size={14} className="text-violet-400" />
                Tasarruf Hedefi (₺)
              </label>
              <input
                type="number"
                value={form.savings_goal}
                onChange={e => setForm(f => ({ ...f, savings_goal: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-violet-500 transition-colors"
                placeholder="Ör: 5000"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 mb-1.5 font-medium flex items-center gap-2">
                <Wallet size={14} className="text-amber-400" />
                Bütçe Hedefi (₺)
              </label>
              <input
                type="number"
                value={form.budget_goal}
                onChange={e => setForm(f => ({ ...f, budget_goal: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-violet-500 transition-colors"
                placeholder="Ör: 20000"
              />
            </div>
          </div>

          {message && (
            <div className={`px-4 py-3 rounded-lg text-sm ${
              message.startsWith('✅')
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/30 text-red-400'
            }`}>
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={saving || !form.declared_income}
            className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </form>
      </div>
    </div>
  )
}
