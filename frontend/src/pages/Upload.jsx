import { useState, useEffect } from 'react'
import { getStatements, uploadStatement, getDrafts, approveDraft, rejectDraft, getAccounts, createAccount, finalizeStatement } from '../services/api'
import { Upload, CheckCircle, XCircle, Clock, Plus, X, AlertTriangle, ArrowRight } from 'lucide-react'

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

const ACCOUNT_TYPES = [
  { value: 'bank', label: 'Banka Hesabı' },
  { value: 'credit_card', label: 'Kredi Kartı' },
  { value: 'cash', label: 'Nakit' },
  { value: 'wallet', label: 'Dijital Cüzdan (Papara vb.)' },
  { value: 'manual', label: 'Manuel Giriş Hesabı' },
  { value: 'other', label: 'Diğer' },
]

const STATUS_COLORS = {
  pending_review: 'text-yellow-400',
  approved: 'text-green-400',
  failed: 'text-red-400',
  extracting: 'text-blue-400',
  uploaded: 'text-gray-400',
}

function CreateAccountModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ name: '', account_type: 'bank', institution_name: '', currency: 'TRY' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await createAccount({
        name: form.name,
        account_type: form.account_type,
        institution_name: form.institution_name || null,
        currency: form.currency,
      })
      if (res.success) {
        onCreated(res.data)
        onClose()
      } else {
        setError(res.error?.message || 'Bir hata oluştu.')
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Hesap oluşturulamadı.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-lg">Yeni Hesap Ekle</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Hesap Adı *</label>
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
            <label className="block text-sm text-gray-400 mb-1">Hesap Türü *</label>
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
          <div>
            <label className="block text-sm text-gray-400 mb-1">Banka / Kurum Adı (opsiyonel)</label>
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
              <option value="TRY">₺ TRY</option>
              <option value="USD">$ USD</option>
              <option value="EUR">€ EUR</option>
            </select>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 bg-gray-800 text-gray-300 py-2 rounded-lg text-sm hover:bg-gray-700">
              İptal
            </button>
            <button
              type="submit"
              disabled={loading || !form.name}
              className="flex-1 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? 'Oluşturuluyor...' : 'Hesap Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function UploadPage() {
  const [month, setMonth] = useState('2026-05')
  const [accounts, setAccounts] = useState([])
  const [accountId, setAccountId] = useState('')
  const [file, setFile] = useState(null)
  const [statements, setStatements] = useState([])
  const [drafts, setDrafts] = useState([])
  const [selectedStatement, setSelectedStatement] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [showCreateAccount, setShowCreateAccount] = useState(false)
  const [finalizing, setFinalizing] = useState(false)
  const [incomeWarning, setIncomeWarning] = useState(false)

  const loadAccounts = () => {
    getAccounts().then(res => {
      const list = res.data || []
      setAccounts(list)
      if (list.length > 0 && !accountId) setAccountId(list[0].id)
    }).catch(() => {})
  }

  const loadStatements = () => {
    getStatements(month).then(res => setStatements(res.data || [])).catch(() => {})
  }

  useEffect(() => {
    loadAccounts()
    loadStatements()
  }, [month])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file || !accountId) return
    setUploading(true)
    setMessage('')
    setIncomeWarning(false)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('month', month)
    formData.append('account_id', accountId)
    try {
      const res = await uploadStatement(formData)
      const pendingCount = res.data?.draft_count || 0
      const failedCount = res.data?.failed_draft_count || 0
      const suffix = failedCount > 0 ? ` (${failedCount} işlem taslağı kaydedilemedi.)` : ''
      setMessage(`✅ PDF işlendi. ${pendingCount} işlem onay bekliyor.${suffix}`)
      if (res.data?.income_detected === false) {
        setIncomeWarning(true)
      }
      setFile(null)
      loadStatements()
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Yükleme başarısız.'
      setMessage(`❌ ${msg}`)
    } finally {
      setUploading(false)
    }
  }

  const loadDrafts = async (stmt) => {
    setSelectedStatement(stmt)
    try {
      const res = await getDrafts(stmt.id)
      const list = res.data || []
      setDrafts(list)
      if (stmt.status === 'pending_review' && list.length === 0 && (stmt.total_draft_count || 0) === 0) {
        setMessage('⚠ Bu PDF için işlem taslağı oluşmamış; backend loglarını ve Supabase RPC hatalarını kontrol edin.')
      }
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Taslaklar getirilemedi.'
      setMessage(`❌ ${msg}`)
      setDrafts([])
    }
  }

  const handleApprove = async (draftId) => {
    await approveDraft(draftId)
    setDrafts(prev => prev.filter(d => d.id !== draftId))
  }

  const handleReject = async (draftId) => {
    await rejectDraft(draftId, 'Kullanıcı tarafından reddedildi.')
    setDrafts(prev => prev.filter(d => d.id !== draftId))
  }

  const handleFinalize = async () => {
    const pendingStatements = statements.filter(s => s.status === 'pending_review')
    if (pendingStatements.length === 0) return
    setFinalizing(true)
    setMessage('')
    try {
      for (const stmt of pendingStatements) {
        await finalizeStatement(stmt.id)
      }
      setMessage('✅ Ay başarıyla tamamlandı. Dashboard güncellenmiştir.')
      loadStatements()
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Tamamlama başarısız.'
      setMessage(`❌ ${msg}`)
    } finally {
      setFinalizing(false)
    }
  }

  return (
    <div className="p-8">
      {showCreateAccount && (
        <CreateAccountModal
          onClose={() => setShowCreateAccount(false)}
          onCreated={(account) => {
            loadAccounts()
            setAccountId(account.id)
          }}
        />
      )}

      <h1 className="text-2xl font-bold text-white mb-6">PDF Yükle</h1>

      {/* Upload Form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Ay</label>
              <select
                value={month}
                onChange={e => setMonth(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              >
                {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Hesap</label>
              <div className="flex gap-2">
                <select
                  value={accountId}
                  onChange={e => setAccountId(e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
                >
                  {accounts.length === 0
                    ? <option value="">— Hesap yok —</option>
                    : accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)
                  }
                </select>
                <button
                  type="button"
                  onClick={() => setShowCreateAccount(true)}
                  className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                  title="Yeni hesap ekle"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">PDF Dosyası</label>
            <input
              type="file"
              accept=".pdf"
              onChange={e => setFile(e.target.files[0])}
              className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-lg px-3 py-2 text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:bg-violet-600 file:text-white"
            />
          </div>

          {message && <p className="text-sm text-gray-300">{message}</p>}

          {incomeWarning && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex flex-col gap-2 mt-2">
              <div className="flex items-center gap-2 text-amber-400 font-medium text-sm">
                <AlertTriangle size={18} />
                <span>Gelir Tespit Edilemedi</span>
              </div>
              <p className="text-gray-400 text-xs leading-relaxed">
                Yüklediğiniz PDF ekstresinde aylık gelirinizi temsil eden bir işlem bulunamadı. 
                Finansal analizlerinizin ve bütçe planlamanızın doğru çalışması için lütfen 
                <strong> Aylık Hedefler</strong> sayfasından bu ayki gelirinizi manuel bildirin.
              </p>
              <a 
                href="/goals"
                className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center gap-1 mt-1 transition-colors self-start"
              >
                Aylık Hedeflere Git <ArrowRight size={14} />
              </a>
            </div>
          )}

          <button
            type="submit"
            disabled={uploading || !file || !accountId}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Upload size={16} />
            {uploading ? 'Yükleniyor ve işleniyor...' : 'Yükle ve İşle'}
          </button>

          {accounts.length === 0 && (
            <p className="text-yellow-500 text-xs">
              ⚠ PDF yüklemek için önce "+" butonuna tıklayarak bir hesap oluşturun.
            </p>
          )}
        </form>
      </div>

      {/* Statement List */}
      {statements.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-semibold">Bu Aydaki PDF'ler</h2>
            {statements.some(s => s.status === 'pending_review') && (
              <button
                onClick={handleFinalize}
                disabled={finalizing}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-xs font-medium transition-colors"
              >
                {finalizing ? 'Tamamlanıyor...' : '✅ Ayı Tamamla'}
              </button>
            )}
          </div>
          <div className="space-y-2">
            {statements.map(stmt => (
              <div key={stmt.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <Clock size={14} className={STATUS_COLORS[stmt.status] || 'text-gray-400'} />
                  <span className="text-gray-300">{stmt.file_name || 'PDF'}</span>
                  <span className={`text-xs ${STATUS_COLORS[stmt.status] || 'text-gray-500'}`}>
                    {stmt.status}
                  </span>
                  {stmt.status === 'failed' && stmt.error_message && (
                    <span className="text-xs text-red-400 max-w-lg truncate">
                      {stmt.error_message}
                    </span>
                  )}
                </div>
                {stmt.status === 'pending_review' && (
                  <button
                    onClick={() => loadDrafts(stmt)}
                    className="text-xs text-violet-400 hover:text-violet-300"
                  >
                    İşlemleri Onayla →
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Draft Review */}
      {selectedStatement && (
        <div className="bg-gray-900 border border-yellow-500/30 rounded-xl p-5">
          <h2 className="text-white font-semibold mb-1">İşlem Onayı</h2>
          <p className="text-gray-500 text-xs mb-4">{drafts.length} işlem onay bekliyor. Onayladıklarınız dashboard'a yansır.</p>
          {drafts.length === 0 ? (
            <p className="text-amber-400 text-sm">
              {selectedStatement.status === 'pending_review' && (selectedStatement.total_draft_count || 0) === 0
                ? 'İşlem taslağı oluşmamış; backend loglarını kontrol edin.'
                : '✅ Tüm işlemler tamamlandı.'}
            </p>
          ) : (
            <div className="space-y-2">
              {drafts.map(draft => (
                <div key={draft.id} className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-3 text-sm">
                  <div className="flex-1 min-w-0">
                    <div className="text-white truncate">{draft.description}</div>
                    <div className="text-gray-400 text-xs mt-1">
                      {draft.transaction_date} · {draft.category || 'Kategori yok'}
                      {draft.confidence_score && (
                        <span className="ml-2 text-gray-500">
                          %{Math.round(draft.confidence_score * 100)} güven
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-4 shrink-0">
                    <span className={`font-semibold ${draft.direction === 'income' ? 'text-green-400' : 'text-red-400'}`}>
                      {draft.direction === 'income' ? '+' : '-'}₺{Number(draft.amount).toLocaleString('tr-TR')}
                    </span>
                    <button onClick={() => handleApprove(draft.id)} title="Onayla" className="text-green-400 hover:text-green-300 transition-colors">
                      <CheckCircle size={22} />
                    </button>
                    <button onClick={() => handleReject(draft.id)} title="Reddet" className="text-red-400 hover:text-red-300 transition-colors">
                      <XCircle size={22} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
