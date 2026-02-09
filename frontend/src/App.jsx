import React, { useState, useEffect, Suspense, lazy } from 'react'

// Lazy load pages - каждая станет отдельным чанком
const Home = lazy(() => import('./pages/Home'))
const Catalog = lazy(() => import('./pages/Catalog'))
const Chat = lazy(() => import('./pages/Chat'))
const LotDetail = lazy(() => import('./pages/LotDetail'))

const NAV_ITEMS = [
  { id: 'home', icon: '🏠', label: 'Главная' },
  { id: 'catalog', icon: '🏢', label: 'Каталог' },
  { id: 'chat', icon: '💬', label: 'Чат' },
  { id: 'menu', icon: '☰', label: 'Меню' },
]

// Loading spinner
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-rz-gold"></div>
  </div>
)

export default function App() {
  const [screen, setScreen] = useState('home')
  const [lots, setLots] = useState([])
  const [stats, setStats] = useState({ available: 0, booked: 0, sold: 0, total: 0 })
  const [loading, setLoading] = useState(true)
  const [selectedLot, setSelectedLot] = useState(null)

  useEffect(() => {
    fetch('/api/lots')
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          setLots(d.lots || [])
          setStats(d.stats || {})
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const navigate = (to, lot = null) => {
    if (lot) setSelectedLot(lot)
    setScreen(to)
  }

  const renderScreen = () => {
    switch (screen) {
      case 'home':
        return <Home stats={stats} onNavigate={navigate} />
      case 'catalog':
        return <Catalog lots={lots} stats={stats} loading={loading} onSelectLot={(lot) => navigate('lot', lot)} />
      case 'lot':
        return <LotDetail lot={selectedLot} onBack={() => navigate('catalog')} onChat={() => navigate('chat')} />
      case 'chat':
        return <Chat lots={lots} onNavigate={navigate} />
      default:
        return <Home stats={stats} onNavigate={navigate} />
    }
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream">
      <Suspense fallback={<PageLoader />}>
        {renderScreen()}
      </Suspense>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-rz-green border-t border-rz-green-light flex justify-around py-2 px-1 z-50">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => navigate(item.id)}
            className={`flex flex-col items-center px-3 py-1 rounded-lg transition-colors ${
              screen === item.id ? 'text-rz-gold' : 'text-rz-cream-dark'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="text-xs">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
