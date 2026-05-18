import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Upload, ListOrdered,
  MessageSquare, LogOut, Target, Landmark
} from 'lucide-react'

const navItems = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard',    end: true },
  { to: '/accounts',     icon: Landmark,        label: 'Hesaplarım' },
  { to: '/transactions', icon: ListOrdered,     label: 'İşlemlerim' },
  { to: '/upload',       icon: Upload,          label: 'PDF Yükle' },
  { to: '/chat',         icon: MessageSquare,   label: 'Chatbot' },
  { to: '/goals',        icon: Target,          label: 'Hedefler' },
]

export default function Layout() {
  const { signOut } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-transparent text-white">
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
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
