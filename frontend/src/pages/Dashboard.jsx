import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { getDashboard, generateInsight } from '../services/api'
import { TrendingUp, TrendingDown, Wallet, Sparkles } from 'lucide-react'

const MONTHS = [
  '2026-05', '2026-04', '2026-03', '2026-02', '2026-01',
  '2025-12', '2025-11', '2025-10',
]

function StatCard({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-400 text-sm">{title}</span>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={16} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">
        {value != null
          ? `₺${Number(value).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`
          : '—'}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [month, setMonth] = useState('2026-05')
  const [dashboard, setDashboard] = useState(null)
  const [insight, setInsight] = useState(null)
  const [loading, setLoading] = useState(false)
  const [insightLoading, setInsightLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    setDashboard(null)
    getDashboard(month)
      .then(res => setDashboard(res.data))
      .catch(() => setError('Dashboard yüklenemedi.'))
      .finally(() => setLoading(false))
  }, [month])

  const handleGenerateInsight = async () => {
    setInsightLoading(true)
    try {
      const res = await generateInsight(month)
      setInsight(res.data)
    } catch {
      setInsight(null)
    } finally {
      setInsightLoading(false)
    }
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Doğrulanmış verilerinizin özeti</p>
        </div>
        <select
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2"
        >
          {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {loading && <p className="text-gray-400">Yükleniyor...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {!loading && !dashboard && !error && (
        <div className="bg-gray-900 border border-dashed border-gray-700 rounded-xl p-10 text-center">
          <p className="text-gray-400">Bu ay için henüz veri yok.</p>
          <p className="text-gray-500 text-sm mt-1">Manuel işlem ekleyin veya PDF yükleyin.</p>
        </div>
      )}

      {dashboard && (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <StatCard title="Toplam Gelir" value={dashboard.total_income} icon={TrendingUp} color="bg-green-500/20 text-green-400" />
            <StatCard title="Toplam Gider" value={dashboard.total_expense} icon={TrendingDown} color="bg-red-500/20 text-red-400" />
            <StatCard title="Net Bakiye" value={dashboard.net_balance} icon={Wallet} color="bg-violet-500/20 text-violet-400" />
          </div>

          {/* Top Categories */}
          {dashboard.top_categories && dashboard.top_categories.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-5">
              <h2 className="text-white font-semibold mb-4">En Yüksek Kategoriler</h2>
              <div className="space-y-2">
                {dashboard.top_categories.slice(0, 5).map((cat, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="text-gray-300">{cat.category || 'Diğer'}</span>
                    <span className="text-gray-400">₺{Number(cat.total).toLocaleString('tr-TR')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Insight */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-white font-semibold flex items-center gap-2">
                <Sparkles size={16} className="text-violet-400" />
                AI Yorumu
              </h2>
              <button
                onClick={handleGenerateInsight}
                disabled={insightLoading}
                className="text-xs text-violet-400 hover:text-violet-300 disabled:opacity-50"
              >
                {insightLoading ? 'Üretiliyor...' : 'Yorum üret'}
              </button>
            </div>
            {insight ? (
              <p className="text-gray-300 text-sm leading-relaxed">{insight.insight_text}</p>
            ) : (
              <p className="text-gray-500 text-sm">"Yorum üret" butonuna tıklayarak AI yorumu alabilirsiniz.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
