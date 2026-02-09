import React, { useState } from 'react'

const formatPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)} млн` : `${Math.round(p/1e3)} тыс`
const shortPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)}` : `${Math.round(p/1e3)}т`
const statusColor = (s) => s === 'available' ? 'bg-rz-success' : s === 'booked' ? 'bg-rz-gold' : 'bg-rz-cream-muted'

export default function Catalog({ lots, stats, loading, onSelectLot }) {
  const [building, setBuilding] = useState(1)
  const [floor, setFloor] = useState(null)
  const [filter, setFilter] = useState('all')

  if (loading) {
    return (
      <div className="min-h-screen bg-rz-green flex flex-col items-center justify-center text-rz-cream pb-20">
        <div className="w-10 h-10 border-4 border-rz-gold border-t-transparent rounded-full animate-spin mb-4"/>
        <p>Загрузка лотов...</p>
      </div>
    )
  }

  const bLots = lots.filter(l => l.building === building)
  const floors = [...new Set(bLots.map(l => l.floor))].sort((a, b) => b - a)

  const bStats = {
    available: bLots.filter(l => l.status === 'available').length,
    booked: bLots.filter(l => l.status === 'booked').length,
    sold: bLots.filter(l => l.status === 'sold').length,
  }

  const getFloorLots = (f) => {
    let fl = bLots.filter(l => l.floor === f).sort((a, b) => a.area - b.area)
    return filter === 'all' ? fl : fl.filter(l => l.status === filter)
  }

  const filters = [
    { k: 'all', l: 'Все', c: bLots.length, i: '📋' },
    { k: 'available', l: 'Свободно', c: bStats.available, i: '🟢' },
    { k: 'booked', l: 'Бронь', c: bStats.booked, i: '🟡' },
    { k: 'sold', l: 'Продано', c: bStats.sold, i: '⚫' },
  ]

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      {/* Header */}
      <div className="bg-rz-gold px-4 py-3 flex justify-between items-center sticky top-0 z-40">
        <div>
          <h1 className="font-bold text-lg text-rz-green-dark">RIZALTA</h1>
          <p className="text-xs text-rz-green-dark/70">Каталог апартаментов</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-rz-green-dark">{stats.available}</p>
          <p className="text-xs text-rz-green-dark/70">свободно</p>
        </div>
      </div>

      {/* Building tabs */}
      <div className="flex border-b border-rz-green-mid sticky top-14 z-30 bg-rz-green">
        {[1, 2].map(b => (
          <button
            key={b}
            onClick={() => { setBuilding(b); setFloor(null) }}
            className={`flex-1 py-3 transition-colors ${
              building === b
                ? 'text-rz-gold border-b-2 border-rz-gold bg-rz-green-light'
                : 'text-rz-cream-dark'
            }`}
          >
            Корпус {b}
            <span className="block text-xs opacity-70">{b === 1 ? 'Family' : 'Business'}</span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 p-2 overflow-x-auto sticky top-28 z-20 bg-rz-green">
        {filters.map(f => (
          <button
            key={f.k}
            onClick={() => setFilter(f.k)}
            className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ${
              filter === f.k
                ? 'bg-rz-gold text-rz-green-dark font-medium'
                : 'bg-rz-green-mid text-rz-cream-dark'
            }`}
          >
            {f.i} {f.l} ({f.c})
          </button>
        ))}
      </div>

      {/* Floors */}
      <div className="p-2 space-y-2">
        {floors.map(f => {
          const floorLots = getFloorLots(f)
          const allFloorLots = bLots.filter(l => l.floor === f)
          const availLots = allFloorLots.filter(l => l.status === 'available')
          const minPrice = availLots.length
            ? Math.min(...availLots.map(l => l.price))
            : Math.min(...allFloorLots.map(l => l.price))
          const isOpen = floor === f

          if (!floorLots.length && filter !== 'all') return null

          return (
            <div key={f} className="bg-rz-green-light rounded-xl overflow-hidden">
              <button
                onClick={() => setFloor(isOpen ? null : f)}
                className="w-full flex items-center justify-between p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 bg-rz-green-mid rounded-lg flex items-center justify-center font-bold text-rz-gold">
                    {f}
                  </span>
                  <div className="text-left">
                    <p className="font-medium">{f} этаж</p>
                    <p className="text-xs text-rz-cream-dark">
                      <span className="text-rz-success">{availLots.length}</span> / {allFloorLots.length}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <p className="text-rz-gold font-medium">от {formatPrice(minPrice)}</p>
                  <span className={`text-rz-cream-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
                </div>
              </button>

              {isOpen && floorLots.length > 0 && (
                <div className="p-2 pt-0 grid grid-cols-4 gap-1.5">
                  {floorLots.map(l => (
                    <button
                      key={l.code}
                      onClick={() => l.status !== 'sold' && onSelectLot(l)}
                      disabled={l.status === 'sold'}
                      className={`rounded-lg p-2 flex flex-col items-center justify-center transition-transform
                        ${statusColor(l.status)} ${l.status === 'sold' ? 'opacity-40 cursor-not-allowed' : 'hover:scale-105'}`}
                    >
                      <span className="text-white font-bold text-sm">{l.area} м²</span>
                      <span className="text-white/80 text-xs font-medium">{shortPrice(l.price)} млн</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
