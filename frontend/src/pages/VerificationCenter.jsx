import { useState, useEffect } from 'react'
import { getTransactions, deleteTransaction, restoreTransaction } from '../services/api'
import { Trash2, RotateCcw } from 'lucide-react'

const MONTHS = ['2026-05', '2026-04', '2026-03', '2026-02']

export default function VerificationCenter() {
  const [month, setMonth] = useState('2026-05')
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    getTransactions(month)
      .then(res => setTransactions(res.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [month])

  const handleDelete = async (id) => {
    await deleteTransaction(id)
    load()
  }

  const handleRestore = async (id) => {
    await restoreTransaction(id)
    load()
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">İşlemlerim</h1>
        <select
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg px-4 py-2"
        >
          {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {loading && <p className="text-gray-400">Yükleniyor...</p>}

      {!loading && transactions.length === 0 && (
        <div className="bg-gray-900 border border-dashed border-gray-700 rounded-xl p-10 text-center">
          <p className="text-gray-400">Bu ay için onaylanmış işlem yok.</p>
        </div>
      )}

      {transactions.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-800">
              <tr className="text-gray-400 text-left">
                <th className="px-5 py-3">Tarih</th>
                <th className="px-5 py-3">Açıklama</th>
                <th className="px-5 py-3">Kategori</th>
                <th className="px-5 py-3">Yön</th>
                <th className="px-5 py-3 text-right">Tutar</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {transactions.map(tx => (
                <tr key={tx.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="px-5 py-3 text-gray-400">{tx.transaction_date}</td>
                  <td className="px-5 py-3 text-white">{tx.description}</td>
                  <td className="px-5 py-3 text-gray-400">{tx.category || '—'}</td>
                  <td className="px-5 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      tx.direction === 'income' ? 'bg-green-500/20 text-green-400'
                      : tx.direction === 'transfer' ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-red-500/20 text-red-400'
                    }`}>
                      {tx.direction === 'income' ? 'Gelir' : tx.direction === 'transfer' ? 'Transfer' : 'Gider'}
                    </span>
                  </td>
                  <td className={`px-5 py-3 text-right font-semibold ${tx.direction === 'income' ? 'text-green-400' : 'text-red-400'}`}>
                    ₺{Number(tx.amount).toLocaleString('tr-TR')}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button onClick={() => handleDelete(tx.id)} className="text-gray-500 hover:text-red-400 ml-2">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
