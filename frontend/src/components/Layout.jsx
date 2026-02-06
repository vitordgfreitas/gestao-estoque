import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  PlusCircle, 
  CalendarCheck, 
  Search, 
  Calendar, 
  Table,
  Menu,
  X,
  LogOut,
  ExternalLink,
  DollarSign,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { infoAPI } from '../services/api'

const menuGroups = [
  {
    label: 'Principal',
    items: [
      { path: '/', icon: LayoutDashboard, label: 'Dashboard' }
    ]
  },
  {
    label: 'Estoque',
    items: [
      { path: '/itens', icon: PlusCircle, label: 'Registrar Item' },
      { path: '/compromissos', icon: CalendarCheck, label: 'Registrar Compromisso' },
      { path: '/disponibilidade', icon: Search, label: 'Verificar Disponibilidade' },
      { path: '/visualizar', icon: Table, label: 'Visualizar Dados' }
    ]
  },
  {
    label: 'Agenda',
    items: [
      { path: '/calendario', icon: Calendar, label: 'Calendário' }
    ]
  },
  {
    label: 'Financeiro',
    items: [
      { path: '/financeiro', icon: DollarSign, label: 'Dashboard Financeiro' },
      { path: '/contas-receber', icon: TrendingUp, label: 'Contas a Receber' },
      { path: '/contas-pagar', icon: TrendingDown, label: 'Contas a Pagar' },
      { path: '/financiamentos', icon: DollarSign, label: 'Financiamentos' }
    ]
  }
]

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [sheetsUrl, setSheetsUrl] = useState(null)
  const location = useLocation()

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setSidebarOpen(true)
      } else {
        setSidebarOpen(false)
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    // Carrega informações do Google Sheets
    infoAPI.obter()
      .then(res => {
        if (res.data?.spreadsheet_url) {
          setSheetsUrl(res.data.spreadsheet_url)
        }
      })
      .catch(() => {
        // Ignora erro silenciosamente
      })
  }, [])

  return (
    <div className="min-h-screen bg-dark-900 flex">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            {/* Overlay para mobile */}
            {isMobile && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 z-40"
                onClick={() => setSidebarOpen(false)}
              />
            )}
            
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed md:static h-screen w-[280px] bg-dark-800 border-r border-dark-700 flex flex-col z-50"
            >
              {/* Logo */}
              <div className="p-6 border-b border-dark-700">
                <div className="flex items-center gap-3">
                  <img 
                    src="/star_logo.jpeg" 
                    alt="STAR Locação" 
                    className="w-full h-auto"
                  />
                </div>
              </div>

              {/* Navigation */}
              <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {menuGroups.map((group) => (
                  <div key={group.label} className="mb-6">
                    <h3 className="text-xs font-semibold text-dark-500 uppercase tracking-wider px-4 py-2 mb-1">
                      {group.label}
                    </h3>
                    <div className="space-y-1">
                      {group.items.map((item) => {
                        const Icon = item.icon
                        const isActive = location.pathname === item.path
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => isMobile && setSidebarOpen(false)}
                            className={`
                              flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                              ${isActive 
                                ? 'bg-primary-600/20 text-primary-400 border-l-2 border-primary-500' 
                                : 'text-dark-400 hover:bg-dark-700/50 hover:text-dark-200'
                              }
                            `}
                          >
                            <Icon size={20} />
                            <span className="font-medium">{item.label}</span>
                          </Link>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </nav>

              {/* Footer */}
              <div className="p-4 border-t border-dark-700 space-y-2">
                {sheetsUrl && (
                  <a
                    href={sheetsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-green-400 hover:text-green-300 hover:bg-green-600/10 rounded-lg transition-colors border border-green-600/20"
                  >
                    <ExternalLink size={16} />
                    <span>Google Sheets</span>
                  </a>
                )}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold">
                      {localStorage.getItem('usuario')?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <span className="text-sm text-dark-300">{localStorage.getItem('usuario') || 'Usuário'}</span>
                  </div>
                </div>
                <button 
                  onClick={() => {
                    localStorage.removeItem('token')
                    localStorage.removeItem('usuario')
                    window.location.href = '/login'
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-dark-400 hover:text-dark-200 hover:bg-dark-700/50 rounded-lg transition-colors"
                >
                  <LogOut size={16} />
                  Sair
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-30 bg-dark-800/80 backdrop-blur-lg border-b border-dark-700 px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
              type="button"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <h2 className="text-xl font-semibold text-dark-50">
              {menuGroups.flatMap(g => g.items).find(item => item.path === location.pathname)?.label || 'Dashboard'}
            </h2>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  )
}
