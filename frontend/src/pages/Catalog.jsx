import React, { useState } from 'react'

const formatPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)} млн` : `${Math.round(p/1e3)} тыс`
const shortPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)}` : `${Math.round(p/1e3)}т`
const statusColor = (s) => s === 'available' ? 'bg-emerald-500' : s === 'booked' ? 'bg-amber-500' : 'bg-gray-500'

export default function Catalog({ lots, stats, loading, onSelectLot }) {
  const [building, setBuilding] = useState(1)
  const [floor, setFloor] = useState(null)
  const [filter, setFilter] = useState('all')

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white pb-20">
        <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mb-4"/>
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
    <div className="min-h-screen bg-slate-900 text-white pb-20">
      {/* Header */}
      <div className="bg-amber-500 px-4 py-3 flex justify-between items-center sticky top-0 z-40">
        <div>
          <h1 className="font-bold text-lg">RIZALTA</h1>
          <p className="text-xs text-amber-100">Каталог апартаментов</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold">{stats.available}</p>
          <p className="text-xs text-amber-100">свободно</p>
        </div>
      </div>

      {/* Building tabs */}
      <div className="flex border-b border-slate-700 sticky top-14 z-30 bg-slate-900">
        {[1, 2].map(b => (
          <button
            key={b}
            onClick={() => { setBuilding(b); setFloor(null) }}
            className={`flex-1 py-3 transition-colors ${
              building === b 
                ? 'text-amber-400 border-b-2 border-amber-400 bg-slate-800' 
                : 'text-slate-400'
            }`}
          >
            Корпус {b}
            <span className="block text-xs opacity-70">{b === 1 ? 'Family' : 'Business'}</span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 p-2 overflow-x-auto sticky top-28 z-20 bg-slate-900">
        {filters.map(f => (
          <button
            key={f.k}
            onClick={() => setFilter(f.k)}
            className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ${
              filter === f.k 
                ? 'bg-amber-500 text-black font-medium' 
                : 'bg-slate-700 text-slate-300'
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
            <div key={f} className="bg-slate-800 rounded-xl overflow-hidden">
              <button 
                onClick={() => setFloor(isOpen ? null : f)} 
                className="w-full flex items-center justify-between p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center font-bold text-amber-400">
                    {f}
                  </span>
                  <div className="text-left">
                    <p className="font-medium">{f} этаж</p>
                    <p className="text-xs text-slate-400">
                      <span className="text-emerald-400">{availLots.length}</span> / {allFloorLots.length}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <p className="text-amber-400 font-medium">от {formatPrice(minPrice)}</p>
                  <span className={`text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
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
