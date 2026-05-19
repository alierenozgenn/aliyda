import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Upload, ListOrdered,
  MessageSquare, LogOut, Target, Landmark, Shield, Sparkles
} from 'lucide-react'

const navItems = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard',    end: true },
  { to: '/upload',       icon: Upload,          label: 'PDF Yükle' },
  { to: '/verify',       icon: Shield,          label: 'Doğrulama' },
  { to: '/transactions', icon: ListOrdered,     label: 'İşlemlerim' },
  { to: '/chat',         icon: MessageSquare,   label: 'Chatbot' },
  { to: '/goals',        icon: Target,          label: 'Hedefler' },
  { to: '/accounts',     icon: Landmark,        label: 'Hesaplarım' },
]

export default function Layout() {
  const { signOut } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-transparent text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 glass border-r border-gray-800/50 flex flex-col shrink-0">
        <div className="px-6 py-5 border-b border-gray-800/50">
          <span className="text-xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent drop-shadow-md">Aliyda</span>
          <p className="text-gray-500 text-xs mt-0.5 tracking-wider uppercase">Bütçe Asistanın</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25'
                    : 'text-gray-400 hover:bg-gray-800/50 hover:text-white hover:shadow-md'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mx-4 mb-4 rounded-2xl border border-violet-500/20 bg-violet-500/10 p-3">
          <p className="text-white text-xs font-semibold mb-1">Nasıl çalışır?</p>
          <p className="text-gray-400 text-[11px] leading-relaxed">
            PDF yükle, işlemleri doğrula, sonra dashboard ve chatbot yalnızca onaylı veriyi kullanır.
          </p>
        </div>

        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white w-full transition-colors"
          >
            <LogOut size={18} />
            Çıkış Yap
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0 flex flex-col">
        <header className="h-[72px] glass border-b border-gray-800/50 px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-violet-500/15 border border-violet-400/25 flex items-center justify-center shadow-[0_0_24px_rgba(139,92,246,0.18)]">
              <Sparkles size={18} className="text-violet-300" />
            </div>
            <div>
              <h1 className="text-white font-bold tracking-wide">Aliyda</h1>
              <p className="text-gray-400 text-xs tracking-[0.16em] uppercase">Kişisel Finansal Analiz</p>
            </div>
          </div>
          <div className="hidden lg:block text-right">
            <p className="text-gray-300 text-sm font-medium">PDF’den doğrulanmış veriye</p>
            <p className="text-gray-500 text-xs mt-0.5">Yükle, onayla, analiz et</p>
          </div>
        </header>
        <section className="flex-1 min-h-0 overflow-auto">
          <Outlet />
        </section>
      </main>
    </div>
  )
}
