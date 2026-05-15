export function HealthScoreGauge({ score }) {
  const color = score >= 70 ? '#16a34a' : score >= 40 ? '#d97706' : '#dc2626'
  const label = score >= 70 ? 'Iyi' : score >= 40 ? 'Orta' : 'Dusuk'
  const dash  = score * 2.51

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border">
      <h3 className="text-sm font-medium text-gray-500 mb-4">Finansal Saglik Skoru</h3>
      <div className="flex items-center gap-4">
        <div className="relative w-24 h-24">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f1f5f9" strokeWidth="12"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="12"
              strokeDasharray={`${dash} 251`} strokeLinecap="round"/>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center rotate-90">
            <span className="text-2xl font-bold" style={{ color }}>{score}</span>
          </div>
        </div>
        <div>
          <span className="text-lg font-semibold" style={{ color }}>{label}</span>
          <p className="text-xs text-gray-400 mt-1">100 uzerinden</p>
        </div>
      </div>
    </div>
  )
}
