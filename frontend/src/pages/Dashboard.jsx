import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'
import { HealthScoreGauge } from '../components/HealthScoreGauge'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
         LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Link } from 'react-router-dom'

const COLORS = ['#1A56A0','#16a34a','#d97706','#dc2626','#7c3aed','#0891b2']
const fmt = (n) => `${n?.toLocaleString('tr-TR') ?? '-'} TL`

function SummaryCard({ title, value, sub, colorClass = 'text-gray-800' }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border">
      <p className="text-sm text-gray-500 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { data: summary } = useQuery({ queryKey: ['summary'], queryFn: () => apiClient.get('/analytics/summary').then(r => r.data) })
  const { data: trend }   = useQuery({ queryKey: ['trend'],   queryFn: () => apiClient.get('/analytics/monthly-trend').then(r => r.data) })
  const { data: pending } = useQuery({ queryKey: ['pending'], queryFn: () => apiClient.get('/analytics/pending-review').then(r => r.data) })
  const { data: insight } = useQuery({ 
    queryKey: ['insight'], 
    queryFn: () => apiClient.get('/analytics/insight').then(r => r.data),
    staleTime: 1000 * 60 * 60, // 1 saat boyunca tekrar istek atmaz
    refetchOnWindowFocus: false, // Sekme değiştirince tekrar istek atmaz
    retry: false
  })

  if (!summary) return <div className="p-8 text-center text-gray-400">Yukleniyor...</div>

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">

      {pending?.count > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex justify-between items-center">
          <span className="text-amber-800">{pending.count} islem onayini bekliyor.</span>
          <Link to="/verify" className="text-amber-700 font-medium hover:underline">Incele</Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard title="Aylık Toplam Gelir"   value={fmt(summary.total_income)}   colorClass="text-green-600"/>
        <SummaryCard title="Aylık Toplam Gider"   value={fmt(summary.total_expense)}  colorClass="text-red-600"/>
        <SummaryCard title="Aylık Net Durum"      value={fmt(summary.net_balance)}    colorClass={summary.net_balance >= 0 ? "text-green-600" : "text-red-600"} sub="(Gelir - Gider)"/>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <HealthScoreGauge score={summary.health_score}/>
        <div className="md:col-span-2 bg-white rounded-2xl p-5 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Harcama Dagilimi</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={summary.categories} dataKey="amount" nameKey="name" cx="50%" cy="50%" outerRadius={70}>
                {summary.categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]}/>)}
              </Pie>
              <Tooltip formatter={(v) => fmt(v)}/>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {insight?.insight && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-xl p-5">
          <p className="text-xs font-medium text-blue-500 mb-2">Aliyda'nin Analizi</p>
          <p className="text-gray-700 leading-relaxed">{insight.insight}</p>
        </div>
      )}

      {trend && trend.length > 0 && (
        <div className="bg-white rounded-2xl p-5 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 mb-3">Aylik Gelir / Gider Trendi</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9"/>
              <XAxis dataKey="month" tick={{ fontSize: 12 }}/>
              <YAxis tick={{ fontSize: 12 }}/>
              <Tooltip formatter={(v) => fmt(v)}/>
              <Line type="monotone" dataKey="income"  stroke="#16a34a" strokeWidth={2} dot={false}/>
              <Line type="monotone" dataKey="expense" stroke="#dc2626" strokeWidth={2} dot={false}/>
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
