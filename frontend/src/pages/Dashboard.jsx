import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getDashboard } from '../services/api'
import WorkflowGuide from '../components/WorkflowGuide'
import {
  TrendingUp, TrendingDown, Wallet,
  RefreshCw, ArrowRight, AlertTriangle, MessageSquare,
} from 'lucide-react'

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────
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

const fmt = (n) =>
  n != null
    ? `₺${Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}`
    : '—'

// ──────────────────────────────────────────────
// Stat Card
// ──────────────────────────────────────────────
function StatCard({ title, value, icon: Icon, iconBg, textColor, subtitle }) {
  return (
    <div className="glass-panel rounded-2xl p-6 hover-glow transition-all duration-300 relative overflow-hidden group">
      {/* Decorative gradient orb */}
      <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full opacity-20 blur-2xl transition-transform duration-500 group-hover:scale-150 ${iconBg.split(' ')[0].replace('/20', '')}`} />
      
      <div className="flex items-start justify-between mb-4 relative z-10">
        <div>
          <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">{title}</p>
          <p className={`text-3xl font-bold tracking-tight ${textColor || 'text-white'}`}>{fmt(value)}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-2 font-medium">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-2xl backdrop-blur-md border border-white/5 shadow-inner ${iconBg}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Category Bar Chart (pure CSS)
// ──────────────────────────────────────────────
const CATEGORY_COLORS = [
  'bg-violet-500', 'bg-blue-500', 'bg-emerald-500', 'bg-amber-500',
  'bg-rose-500', 'bg-cyan-500', 'bg-orange-500', 'bg-pink-500',
]

function CategoryChart({ categories }) {
  if (!categories || categories.length === 0) return null
  const getValue = (cat) => Number(cat.amount ?? cat.total ?? 0)
  const max = Math.max(...categories.map(getValue))

  return (
    <div className="space-y-3">
      {categories.slice(0, 7).map((cat, i) => {
        const val = getValue(cat)
        const pct = max > 0 ? (val / max) * 100 : 0
        return (
          <div key={i} className="flex items-center gap-3">
            <div className="w-24 text-xs text-gray-400 truncate text-right shrink-0">
              {cat.category || 'Diğer'}
            </div>
            <div className="flex-1 bg-gray-800 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${CATEGORY_COLORS[i % CATEGORY_COLORS.length]} transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="w-24 text-xs text-gray-300 text-right shrink-0">
              {fmt(val)}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ──────────────────────────────────────────────
// Income vs Expense ratio bar
// ──────────────────────────────────────────────
function IncomeExpenseBar({ income, expense }) {
  const total = Number(income || 0) + Number(expense || 0)
  if (total === 0) return null
  const incomePct = Math.round((Number(income || 0) / total) * 100)
  const expensePct = 100 - incomePct

  return (
    <div className="mt-4">
      <div className="flex justify-between text-xs text-gray-500 mb-1.5">
        <span>Gelir {incomePct}%</span>
        <span>Gider {expensePct}%</span>
      </div>
      <div className="flex h-2 rounded-full overflow-hidden">
        <div
          className="bg-emerald-500 transition-all duration-500"
          style={{ width: `${incomePct}%` }}
        />
        <div
          className="bg-red-500 transition-all duration-500"
          style={{ width: `${expensePct}%` }}
        />
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────
export default function Dashboard() {
  const { user } = useAuth()
  const [month, setMonth] = useState(MONTHS[0])
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(false)
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

  const netBalance = dashboard ? Number(dashboard.net_balance ?? 0) : 0
  const isNegative = netBalance < 0
  const incomeSourceLabel = dashboard?.income_basis === 'manual'
    ? 'manuel gelir'
    : dashboard?.income_basis === 'mixed'
      ? 'manuel + işlem girişi'
      : 'işlem girişi'

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-8 lg:px-8">
      {/* Header */}
      <div className="glass-panel rounded-3xl px-6 py-5 mb-6 relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-400/60 to-transparent" />
        <div className="flex items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                Doğrulanmış kullanıcı verisi
              </span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Finansal Kontrol Merkezi</h1>
            <p className="text-gray-400 text-sm mt-2">
              {user?.email && <span className="text-gray-500">{user.email} · </span>}
              Gelir, gider ve chatbot yorumları yalnızca onaylanan işlemlerden hesaplanır.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="text-gray-500 text-xs">Analiz ayı</span>
            <select
              value={month}
              onChange={e => setMonth(e.target.value)}
              className="bg-gray-800/80 border border-gray-700 text-white text-sm rounded-xl px-4 py-2 focus:outline-none focus:border-violet-500 shadow-lg"
            >
              {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
      </div>

      <WorkflowGuide active="/" />

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <RefreshCw size={14} className="animate-spin" />
          Yükleniyor...
        </div>
      )}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm">
          ⚠ {error}
        </div>
      )}

      {!loading && !dashboard && !error && (
        <div className="glass-panel border border-dashed border-gray-700 rounded-2xl p-12 text-center">
          <Wallet size={36} className="text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">Bu ay için henüz veri yok.</p>
          <p className="text-gray-500 text-sm mt-1">Önce PDF yükleyin veya manuel işlem ekleyin; PDF işlemleri doğrulamadan dashboard’a yansımaz.</p>
          <div className="flex gap-3 justify-center mt-4">
            <Link to="/upload" className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              PDF Yükle <ArrowRight size={14} />
            </Link>
            <Link to="/transactions" className="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
              İşlem Ekle <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      )}

      {dashboard && (
        <>
          {/* Negative balance warning */}
          {isNegative && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 flex items-center gap-2 text-sm text-red-400">
              <AlertTriangle size={16} />
              Bu ay giderleriniz gelirinizi aşıyor. Net bakiye negatif.
            </div>
          )}

          {/* Stat Cards */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <StatCard
              title="Toplam Gelir"
              value={dashboard.total_income}
              icon={TrendingUp}
              iconBg="bg-emerald-500/20 text-emerald-400"
              textColor="text-emerald-400"
              subtitle={`${incomeSourceLabel} · ${dashboard.income_count ?? '—'} giriş`}
            />
            <StatCard
              title="Toplam Gider"
              value={dashboard.total_expense}
              icon={TrendingDown}
              iconBg="bg-red-500/20 text-red-400"
              textColor="text-red-400"
              subtitle={`${dashboard.expense_count ?? '—'} çıkış`}
            />
            <StatCard
              title="Net Bakiye"
              value={dashboard.net_balance}
              icon={Wallet}
              iconBg="bg-violet-500/20 text-violet-400"
              textColor={isNegative ? 'text-red-400' : 'text-violet-400'}
              subtitle="Gelir - gider"
            />
          </div>

          <div className="mb-6 rounded-2xl border border-violet-500/20 bg-violet-500/10 px-5 py-4 flex items-center justify-between gap-4">
            <div>
              <p className="text-white text-sm font-semibold">Detaylı yorum istiyorsan chatbot’a sor.</p>
              <p className="text-gray-400 text-xs mt-1">
                “Faturaları tek tek göster”, “nereden tasarruf edebilirim” veya “en büyük harcamalarım neler” gibi sorular sorabilirsin.
              </p>
            </div>
            <Link
              to="/chat"
              className="shrink-0 inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <MessageSquare size={15} />
              Chatbot’a Sor
            </Link>
          </div>

          {/* Income vs Expense bar */}
          <div className="glass-panel rounded-2xl p-6 mb-6">
            <h2 className="text-white text-sm font-semibold mb-3 tracking-wide uppercase">Gelir / Gider Oranı</h2>
            <IncomeExpenseBar income={dashboard.total_income} expense={dashboard.total_expense} />
          </div>

          {/* Categories + Largest */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            {/* Category chart */}
            <div className="glass-panel rounded-2xl p-6">
              <h2 className="text-white text-sm font-semibold mb-5 tracking-wide uppercase">Harcama Kategorileri</h2>
              {dashboard.top_categories && dashboard.top_categories.length > 0 ? (
                <CategoryChart categories={dashboard.top_categories} />
              ) : (
                <p className="text-gray-500 text-sm">Kategori verisi yok.</p>
              )}
            </div>

            {/* Largest transactions */}
            <div className="glass-panel rounded-2xl p-6">
              <h2 className="text-white text-sm font-semibold mb-5 tracking-wide uppercase">En Büyük İşlemler</h2>
              {dashboard.largest_transactions && dashboard.largest_transactions.length > 0 ? (
                <div className="space-y-4">
                  {dashboard.largest_transactions.slice(0, 5).map((tx, i) => (
                    <div key={i} className="flex items-center justify-between group">
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-200 text-sm font-medium truncate group-hover:text-white transition-colors">{tx.description}</p>
                        <p className="text-gray-500 text-xs mt-0.5">{tx.category || 'Diğer'} · {tx.transaction_date}</p>
                      </div>
                      <span className={`text-sm font-bold ml-4 shrink-0 px-2 py-1 rounded-md bg-black/20 ${
                        tx.direction === 'income' ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {tx.direction === 'income' ? '+' : '-'}{fmt(tx.amount)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">Veri yok.</p>
              )}
            </div>
          </div>

        </>
      )}
    </div>
  )
}
