import { useState, useEffect } from 'react'
import { getAccounts, createAccount, archiveAccount } from '../services/api'
import { Plus, CreditCard, Landmark, Wallet, Banknote, Archive, RefreshCcw } from 'lucide-react'

const ACCOUNT_TYPES = [
  { value: 'bank',        label: 'Banka Hesabı',          icon: Landmark },
  { value: 'credit_card', label: 'Kredi Kartı',            icon: CreditCard },
  { value: 'cash',        label: 'Nakit',                   icon: Banknote },
  { value: 'wallet',      label: 'Dijital Cüzdan',          icon: Wallet },
  { value: 'manual',      label: 'Manuel Giriş Hesabı',    icon: RefreshCcw },
  { value: 'other',       label: 'Diğer',                   icon: Wallet },
]

const TYPE_COLORS = {
  bank:        'bg-blue-500/20 text-blue-400 border-blue-500/30',
  credit_card: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  cash:        'bg-green-500/20 text-green-400 border-green-500/30',
  wallet:      'bg-orange-500/20 text-orange-400 border-orange-500/30',
  manual:      'bg-gray-500/20 text-gray-400 border-gray-500/30',
  other:       'bg-gray-500/20 text-gray-400 border-gray-500/30',
}

const typeLabel = (type) => ACCOUNT_TYPES.find(t => t.value === type)?.label || type
const TypeIcon = ({ type, size = 20 }) => {
  const Icon = ACCOUNT_TYPES.find(t => t.value === type)?.icon || Wallet
  return <Icon size={size} />
}

const INITIAL_FORM = { name: '', account_type: 'bank', institution_name: '', currency: 'TRY' }

export default function Accounts() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(INITIAL_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const load = () => {
    setLoading(true)
    getAccounts()
      .then(res => setAccounts(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await createAccount({
        name: form.name.trim(),
        account_type: form.account_type,
        institution_name: form.institution_name.trim() || null,
        currency: form.currency,
      })
      setSuccessMsg(`"${form.name}" hesabı oluşturuldu.`)
      setForm(INITIAL_FORM)
      setShowForm(false)
      load()
      setTimeout(() => setSuccessMsg(''), 3000)
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Hesap oluşturulamadı.'
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleArchive = async (id, name) => {
    if (!confirm(`"${name}" hesabını devre dışı bırakmak istediğinize emin misiniz?`)) return
    try {
      await archiveAccount(id)
      load()
    } catch {
      alert('İşlem sırasında hata oluştu.')
    }
  }

  return (
    <div className="p-8 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Banka Hesaplarım</h1>
          <p className="text-gray-400 text-sm mt-1">
            PDF yüklerken ve manuel işlem girerken bu hesapları kullanırsınız.
          </p>
        </div>
        <button
          onClick={() => { setShowForm(v => !v); setError('') }}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Hesap Ekle
        </button>
      </div>

      {/* Success message */}
      {successMsg && (
        <div className="mb-4 bg-green-500/20 border border-green-500/30 text-green-400 px-4 py-3 rounded-lg text-sm">
          ✅ {successMsg}
        </div>
      )}

      {/* Add Account Form */}
      {showForm && (
        <div className="bg-gray-900 border border-violet-500/30 rounded-xl p-6 mb-6">
          <h2 className="text-white font-semibold mb-4">Yeni Hesap</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Hesap Adı <span className="text-red-400">*</span></label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  required
                  placeholder="Ziraat Maaş, Enpara Kredi Kartı..."
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Hesap Türü <span className="text-red-400">*</span></label>
                <select
                  value={form.account_type}
                  onChange={e => setForm(f => ({ ...f, account_type: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
                >
                  {ACCOUNT_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Banka / Kurum Adı <span className="text-gray-500">(opsiyonel)</span></label>
                <input
                  type="text"
                  value={form.institution_name}
                  onChange={e => setForm(f => ({ ...f, institution_name: e.target.value }))}
                  placeholder="Ziraat Bankası, Garanti..."
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-violet-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Para Birimi</label>
                <select
                  value={form.currency}
                  onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
                >
                  <option value="TRY">₺ TRY — Türk Lirası</option>
                  <option value="USD">$ USD — Amerikan Doları</option>
                  <option value="EUR">€ EUR — Euro</option>
                  <option value="GBP">£ GBP — İngiliz Sterlini</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/30 text-red-400 px-3 py-2 rounded-lg text-sm">
                ❌ {error}
              </div>
            )}

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={() => { setShowForm(false); setError('') }}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
              >
                İptal
              </button>
              <button
                type="submit"
                disabled={saving || !form.name.trim()}
                className="px-5 py-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
              >
                {saving ? 'Oluşturuluyor...' : 'Hesabı Oluştur'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Account List */}
      {loading ? (
        <p className="text-gray-400 text-sm">Yükleniyor...</p>
      ) : accounts.length === 0 ? (
        <div className="bg-gray-900 border border-dashed border-gray-700 rounded-xl p-12 text-center">
          <Landmark size={36} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">Henüz hesap eklemediniz.</p>
          <p className="text-gray-500 text-sm mt-1">
            Yukarıdaki "Hesap Ekle" butonuna tıklayarak başlayabilirsiniz.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {accounts.map(account => (
            <div
              key={account.id}
              className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 flex items-center justify-between hover:border-gray-700 transition-colors"
            >
              {/* Left: Icon + Info */}
              <div className="flex items-center gap-4">
                <div className={`p-2.5 rounded-lg border ${TYPE_COLORS[account.account_type] || TYPE_COLORS.other}`}>
                  <TypeIcon type={account.account_type} size={18} />
                </div>
                <div>
                  <div className="text-white font-medium">{account.name}</div>
                  <div className="text-gray-500 text-xs mt-0.5">
                    {account.institution_name && `${account.institution_name} · `}
                    {typeLabel(account.account_type)} · {account.currency}
                  </div>
                </div>
              </div>

              {/* Right: Badge + Archive button */}
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2.5 py-1 rounded-full border ${TYPE_COLORS[account.account_type] || TYPE_COLORS.other}`}>
                  {typeLabel(account.account_type)}
                </span>
                <button
                  onClick={() => handleArchive(account.id, account.name)}
                  title="Hesabı devre dışı bırak"
                  className="text-gray-600 hover:text-red-400 transition-colors p-1"
                >
                  <Archive size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info note */}
      {accounts.length > 0 && (
        <p className="text-gray-600 text-xs mt-6">
          * Devre dışı bırakılan hesaplar listelenmez ancak geçmiş işlemler korunur.
        </p>
      )}
    </div>
  )
}
