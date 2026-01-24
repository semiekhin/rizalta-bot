import React, { useState, useEffect } from 'react'
import Home from './pages/Home'
import Catalog from './pages/Catalog'
import Chat from './pages/Chat'
import LotDetail from './pages/LotDetail'

const NAV_ITEMS = [
  { id: 'home', icon: '🏠', label: 'Главная' },
  { id: 'catalog', icon: '🏢', label: 'Каталог' },
  { id: 'chat', icon: '💬', label: 'Чат' },
  { id: 'menu', icon: '☰', label: 'Меню' },
]

export default function App() {
  const [screen, setScreen] = useState('home')
  const [lots, setLots] = useState([])
  const [stats, setStats] = useState({ available: 0, booked: 0, sold: 0, total: 0 })
  const [loading, setLoading] = useState(true)
  const [selectedLot, setSelectedLot] = useState(null)

  useEffect(() => {
    fetch('https://api.rizaltaservice.ru/api/lots')
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
    <div className="min-h-screen bg-slate-900 text-white">
      {renderScreen()}
      
      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-800 border-t border-slate-700 flex justify-around py-2 px-1 z-50">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => navigate(item.id)}
            className={`flex flex-col items-center px-3 py-1 rounded-lg transition-colors ${
              screen === item.id ? 'text-amber-400' : 'text-slate-400'
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
