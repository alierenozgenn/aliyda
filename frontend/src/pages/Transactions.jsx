import { useState, useEffect } from 'react'
import {
  getTransactions,
  createManualTransaction,
  updateTransaction,
  deleteTransaction,
  restoreTransaction,
  getAccounts,
} from '../services/api'
import {
  Plus, Trash2, RotateCcw, Pencil, X, Check,
  TrendingUp, TrendingDown, ArrowLeftRight,
  ChevronLeft, ChevronRight,
} from 'lucide-react'

// ──────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────
const CATEGORIES = [
  'Market', 'Restoran/Kafe', 'Ulaşım', 'Faturalar', 'Eğlence',
  'Sağlık', 'Giyim', 'Eğitim', 'Kira', 'Maaş', 'Diğer Gelir',
  'Transfer', 'Alışveriş', 'Teknoloji', 'Spor', 'Diğer',
]

const DIRECTION_LABELS = {
  income: { label: 'Gelir', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: TrendingUp },
  expense: { label: 'Gider', color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: TrendingDown },
  transfer: { label: 'Transfer', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: ArrowLeftRight },
}

function buildMonths() {
  const months = []
  const now = new Date()
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    months.push(val)
  }
  return months
}
const MONTHS = buildMonths()

const EMPTY_FORM = {
  transaction_date: new Date().toISOString().slice(0, 10),
  transaction_time: '',
  description: '',
  amount: '',
  direction: 'expense',
  category: 'Diğer',
  counterparty: '',
  account_id: '',
}

// ──────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────

function DirectionBadge({ direction }) {
  const d = DIRECTION_LABELS[direction] || DIRECTION_LABELS.expense
  const Icon = d.icon
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${d.color}`}>
      <Icon size={11} />
      {d.label}
    </span>
  )
}

function TransactionFormModal({ title, initial, accounts, onSave, onClose, saving }) {
  const [form, setForm] = useState(initial || EMPTY_FORM)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(form)
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-lg">{title}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Date + Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tarih *</label>
              <input
                type="date"
                value={form.transaction_date}
                onChange={e => set('transaction_date', e.target.value)}
                required
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Saat (opsiyonel)</label>
              <input
                type="time"
                value={form.transaction_time}
                onChange={e => set('transaction_time', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Açıklama *</label>
            <input
              type="text"
              value={form.description}
              onChange={e => set('description', e.target.value)}
              required
              placeholder="Migros market alışverişi"
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
            />
          </div>

          {/* Amount + Direction */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Tutar (₺) *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={form.amount}
                onChange={e => set('amount', e.target.value)}
                required
                placeholder="0.00"
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Yön *</label>
              <select
                value={form.direction}
                onChange={e => set('direction', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              >
                <option value="expense">Gider</option>
                <option value="income">Gelir</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
          </div>

          {/* Category + Counterparty */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Kategori</label>
              <select
                value={form.category}
                onChange={e => set('category', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Karşı Taraf</label>
              <input
                type="text"
                value={form.counterparty}
                onChange={e => set('counterparty', e.target.value)}
                placeholder="Migros, Netflix..."
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>

          {/* Account */}
          {accounts.length > 0 && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">Hesap</label>
              <select
                value={form.account_id}
                onChange={e => set('account_id', e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              >
                <option value="">— Hesap seçin —</option>
                {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm transition-colors"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────
// Main Page
// ──────────────────────────────────────────────
export default function Transactions() {
  const [month, setMonth] = useState(MONTHS[0])
  const [transactions, setTransactions] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editTx, setEditTx] = useState(null)   // tx object being edited
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')   // all | income | expense | transfer | deleted

  const load = () => {
    setLoading(true)
    // İki ayrı istek: aktif işlemler + silinmişler
    Promise.all([
      getTransactions(month, false),
      getTransactions(month, true),
    ])
      .then(([activeRes, allRes]) => {
        const active = activeRes.data || []
        const all = allRes.data || []
        // Silinmişler = all'da olup active'de olmayanlar
        const activeIds = new Set(active.map(t => t.id))
        const deleted = all.filter(t => !activeIds.has(t.id))
        setTransactions([...active.map(t => ({ ...t, is_deleted: false })), ...deleted.map(t => ({ ...t, is_deleted: true }))])
      })
      .catch(() => setTransactions([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    getAccounts()
      .then(res => setAccounts(res.data || []))
      .catch(() => {})
  }, [])

  useEffect(() => { load() }, [month])

  // ── Stats ──────────────────────────────────
  const active = transactions.filter(t => !t.is_deleted)
  const totalIncome = active.filter(t => t.direction === 'income').reduce((s, t) => s + Number(t.amount), 0)
  const totalExpense = active.filter(t => t.direction === 'expense').reduce((s, t) => s + Number(t.amount), 0)
  const netBalance = totalIncome - totalExpense

  // ── Filter ─────────────────────────────────
  const filtered = transactions.filter(t => {
    if (filter === 'deleted') return t.is_deleted
    if (filter === 'all') return !t.is_deleted
    return !t.is_deleted && t.direction === filter
  })

  // ── Actions ────────────────────────────────
  const handleAdd = async (form) => {
    setSaving(true)
    setError('')
    try {
      await createManualTransaction({
        transaction_date: form.transaction_date,
        transaction_time: form.transaction_time || null,
        description: form.description,
        amount: parseFloat(form.amount),
        direction: form.direction,
        category: form.category,
        counterparty: form.counterparty || null,
        account_id: form.account_id || null,
      })
      setShowAddModal(false)
      load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'İşlem eklenemedi.')
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = async (form) => {
    setSaving(true)
    setError('')
    try {
      await updateTransaction(editTx.id, {
        transaction_date: form.transaction_date,
        transaction_time: form.transaction_time || null,
        description: form.description,
        amount: parseFloat(form.amount),
        direction: form.direction,
        category: form.category,
        counterparty: form.counterparty || null,
      })
      setEditTx(null)
      load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'İşlem güncellenemedi.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Bu işlemi silmek istediğinize emin misiniz? Geri alabilirsiniz.')) return
    try {
      await deleteTransaction(id)
      load()
    } catch {
      alert('Silme sırasında hata oluştu.')
    }
  }

  const handleRestore = async (id) => {
    try {
      await restoreTransaction(id)
      load()
    } catch {
      alert('Geri alma sırasında hata oluştu.')
    }
  }

  const fmt = (n) => Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2 })

  return (
    <div className="p-8 max-w-5xl">
      {/* Modals */}
      {showAddModal && (
        <TransactionFormModal
          title="Manuel İşlem Ekle"
          initial={{ ...EMPTY_FORM, account_id: accounts[0]?.id || '' }}
          accounts={accounts}
          saving={saving}
          onSave={handleAdd}
          onClose={() => { setShowAddModal(false); setError('') }}
        />
      )}
      {editTx && (
        <TransactionFormModal
          title="İşlemi Düzenle"
          initial={{
            transaction_date: editTx.transaction_date,
            transaction_time: editTx.transaction_time || '',
            description: editTx.description,
            amount: String(editTx.amount),
            direction: editTx.direction,
            category: editTx.category || 'Diğer',
            counterparty: editTx.counterparty || '',
            account_id: editTx.account_id || '',
          }}
          accounts={accounts}
          saving={saving}
          onSave={handleEdit}
          onClose={() => { setEditTx(null); setError('') }}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">İşlemlerim</h1>
          <p className="text-gray-400 text-sm mt-1">Doğrulanmış gelir ve giderleriniz</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={month}
            onChange={e => setMonth(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2"
          >
            {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            İşlem Ekle
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-500/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
          ❌ {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Toplam Gelir</p>
          <p className="text-xl font-bold text-emerald-400">₺{fmt(totalIncome)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Toplam Gider</p>
          <p className="text-xl font-bold text-red-400">₺{fmt(totalExpense)}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Net Bakiye</p>
          <p className={`text-xl font-bold ${netBalance >= 0 ? 'text-violet-400' : 'text-red-400'}`}>
            {netBalance >= 0 ? '+' : ''}₺{fmt(Math.abs(netBalance))}
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {[
          { key: 'all', label: 'Tümü' },
          { key: 'income', label: 'Gelirler' },
          { key: 'expense', label: 'Giderler' },
          { key: 'transfer', label: 'Transferler' },
          { key: 'deleted', label: 'Silinenler' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === key
                ? 'bg-violet-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <p className="text-gray-400 text-sm">Yükleniyor...</p>}

      {/* Empty */}
      {!loading && filtered.length === 0 && (
        <div className="bg-gray-900 border border-dashed border-gray-700 rounded-xl p-12 text-center">
          <p className="text-gray-400">Bu ay için {filter === 'deleted' ? 'silinmiş' : 'onaylanmış'} işlem yok.</p>
          {filter === 'all' && (
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-3 text-sm text-violet-400 hover:text-violet-300 underline"
            >
              Manuel işlem ekle →
            </button>
          )}
        </div>
      )}

      {/* Table */}
      {!loading && filtered.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-800">
              <tr className="text-gray-500 text-left text-xs">
                <th className="px-5 py-3 font-medium">Tarih</th>
                <th className="px-5 py-3 font-medium">Açıklama</th>
                <th className="px-5 py-3 font-medium">Kategori</th>
                <th className="px-5 py-3 font-medium">Yön</th>
                <th className="px-5 py-3 font-medium text-right">Tutar</th>
                <th className="px-5 py-3 font-medium text-right">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filtered.map(tx => (
                <tr
                  key={tx.id}
                  className={`hover:bg-gray-800/40 transition-colors ${tx.is_deleted ? 'opacity-50' : ''}`}
                >
                  <td className="px-5 py-3 text-gray-400 text-xs whitespace-nowrap">
                    {tx.transaction_date}
                    {tx.transaction_time && (
                      <span className="text-gray-600 ml-1">{tx.transaction_time.slice(0, 5)}</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-white max-w-xs">
                    <div className="truncate">{tx.description}</div>
                    {tx.counterparty && (
                      <div className="text-gray-600 text-xs truncate">{tx.counterparty}</div>
                    )}
                  </td>
                  <td className="px-5 py-3 text-gray-400 text-xs">{tx.category || '—'}</td>
                  <td className="px-5 py-3">
                    <DirectionBadge direction={tx.direction} />
                  </td>
                  <td className={`px-5 py-3 text-right font-semibold ${
                    tx.direction === 'income' ? 'text-emerald-400' :
                    tx.direction === 'transfer' ? 'text-blue-400' : 'text-red-400'
                  }`}>
                    {tx.direction === 'income' ? '+' : tx.direction === 'expense' ? '-' : ''}₺{fmt(tx.amount)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {tx.is_deleted ? (
                      <button
                        onClick={() => handleRestore(tx.id)}
                        title="Geri al"
                        className="text-gray-500 hover:text-emerald-400 transition-colors p-1"
                      >
                        <RotateCcw size={15} />
                      </button>
                    ) : (
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditTx(tx)}
                          title="Düzenle"
                          className="text-gray-500 hover:text-violet-400 transition-colors p-1"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(tx.id)}
                          title="Sil"
                          className="text-gray-500 hover:text-red-400 transition-colors p-1"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Footer summary */}
          <div className="border-t border-gray-800 px-5 py-3 flex items-center justify-between text-xs text-gray-500">
            <span>{filtered.length} işlem</span>
            {filter !== 'deleted' && (
              <span>
                {filtered.filter(t => t.direction === 'income').length} gelir ·{' '}
                {filtered.filter(t => t.direction === 'expense').length} gider
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
