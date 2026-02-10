import React, { useState, useMemo } from 'react'

const formatPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)} млн` : `${Math.round(p/1e3)} тыс`
const shortPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)}` : `${Math.round(p/1e3)}т`
const statusColor = (s) => s === 'available' ? 'bg-rz-success' : s === 'booked' ? 'bg-rz-gold' : 'bg-rz-cream-muted'

export default function Catalog({ lots, stats, loading, onSelectLot }) {
  const [building, setBuilding] = useState(1)
  const [floor, setFloor] = useState(null)
  const [filter, setFilter] = useState('all')
  const [showFilters, setShowFilters] = useState(false)
  const [areaMin, setAreaMin] = useState('')
  const [areaMax, setAreaMax] = useState('')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')

  const hasAdvancedFilters = areaMin || areaMax || priceMin || priceMax

  const resetFilters = () => {
    setAreaMin('')
    setAreaMax('')
    setPriceMin('')
    setPriceMax('')
    setFilter('all')
  }

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

  const applyFilters = (list) => {
    let result = list
    if (filter !== 'all') result = result.filter(l => l.status === filter)
    if (areaMin) result = result.filter(l => l.area >= parseFloat(areaMin))
    if (areaMax) result = result.filter(l => l.area <= parseFloat(areaMax))
    if (priceMin) result = result.filter(l => l.price >= parseFloat(priceMin) * 1e6)
    if (priceMax) result = result.filter(l => l.price <= parseFloat(priceMax) * 1e6)
    return result
  }

  const filteredTotal = applyFilters(bLots).length

  const getFloorLots = (f) => {
    const fl = bLots.filter(l => l.floor === f).sort((a, b) => a.area - b.area)
    return applyFilters(fl)
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

      {/* Status filters + filter toggle */}
      <div className="flex gap-2 p-2 overflow-x-auto sticky top-28 z-20 bg-rz-green items-center">
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
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ml-auto ${
            hasAdvancedFilters ? 'bg-rz-gold text-rz-green-dark font-medium' : 'bg-rz-green-mid text-rz-cream-dark'
          }`}
        >
          ⚙ Фильтры
        </button>
      </div>

      {/* Advanced filters panel */}
      {showFilters && (
        <div className="px-2 pb-2 space-y-2 bg-rz-green sticky top-40 z-10">
          <div className="bg-rz-green-light rounded-xl p-3 space-y-3">
            <div className="flex gap-2 items-center">
              <span className="text-xs text-rz-cream-dark w-16">Площадь:</span>
              <input type="number" placeholder="от м²" value={areaMin} onChange={e => setAreaMin(e.target.value)}
                className="flex-1 bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold"/>
              <input type="number" placeholder="до м²" value={areaMax} onChange={e => setAreaMax(e.target.value)}
                className="flex-1 bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold"/>
            </div>
            <div className="flex gap-2 items-center">
              <span className="text-xs text-rz-cream-dark w-16">Цена:</span>
              <input type="number" placeholder="от млн" value={priceMin} onChange={e => setPriceMin(e.target.value)}
                className="flex-1 bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold"/>
              <input type="number" placeholder="до млн" value={priceMax} onChange={e => setPriceMax(e.target.value)}
                className="flex-1 bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold"/>
            </div>
            <div className="flex justify-between items-center">
              <p className="text-xs text-rz-cream-dark">Найдено: <span className="text-rz-gold font-medium">{filteredTotal}</span> из {bLots.length}</p>
              {hasAdvancedFilters && (
                <button onClick={resetFilters} className="text-xs text-rz-cream-muted hover:text-rz-cream">✕ Сброс</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Found counter (when filters active but panel closed) */}
      {!showFilters && hasAdvancedFilters && (
        <div className="px-4 py-1">
          <p className="text-xs text-rz-cream-dark">Найдено: <span className="text-rz-gold font-medium">{filteredTotal}</span> из {bLots.length}</p>
        </div>
      )}

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

          if (!floorLots.length && (filter !== 'all' || hasAdvancedFilters)) return null

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
