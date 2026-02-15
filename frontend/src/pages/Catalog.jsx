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

  // Search
  const [showSearch, setShowSearch] = useState(false)
  const [searchCode, setSearchCode] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')

  const handleSearch = async () => {
    const code = searchCode.trim()
    if (!code) return
    setSearchLoading(true)
    setSearchError('')
    try {
      const res = await fetch(`/api/lots/search?code=${encodeURIComponent(code)}`)
      const data = await res.json()
      if (data.ok) {
        setShowSearch(false)
        setSearchCode('')
        onSelectLot(data.lot)
      } else {
        setSearchError(data.error || 'Лот не найден')
      }
    } catch {
      setSearchError('Ошибка соединения')
    }
    setSearchLoading(false)
  }

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

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20 overflow-x-hidden">
      {/* Header */}
      <div className="bg-rz-gold px-4 py-3 flex justify-between items-center sticky top-0 z-40">
        <div>
          <h1 className="font-bold text-lg text-rz-green-dark">RIZALTA</h1>
          <p className="text-xs text-rz-green-dark/70">Каталог апартаментов</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSearch(true)}
            className="w-9 h-9 bg-rz-green-dark/20 rounded-lg flex items-center justify-center hover:bg-rz-green-dark/30 transition-colors"
          >
            <span className="text-rz-green-dark text-lg">🔍</span>
          </button>
          <div className="text-right">
            <p className="text-2xl font-bold text-rz-green-dark">{stats.available}</p>
            <p className="text-xs text-rz-green-dark/70">свободно</p>
          </div>
        </div>
      </div>

      {/* Search Modal */}
      {showSearch && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center pt-20">
          <div className="bg-rz-green-light w-full max-w-sm mx-4 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center">
              <h2 className="font-bold">🔍 Поиск лота</h2>
              <button onClick={() => { setShowSearch(false); setSearchError('') }} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-3">
              <form onSubmit={(e) => { e.preventDefault(); handleSearch() }} className="flex gap-2">
                <input
                  type="text"
                  value={searchCode}
                  onChange={(e) => { setSearchCode(e.target.value); setSearchError('') }}
                  placeholder="Код лота (А101, В615...)"
                  className="flex-1 bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={searchLoading || !searchCode.trim()}
                  className="bg-rz-gold text-rz-green-dark font-bold px-5 py-2.5 rounded-xl disabled:opacity-50 hover:bg-rz-gold-light transition-colors"
                >
                  {searchLoading ? '...' : 'Найти'}
                </button>
              </form>
              {searchError && (
                <p className="text-rz-error text-sm text-center">{searchError}</p>
              )}
              <p className="text-rz-cream-muted text-xs text-center">Поиск по всем корпусам (К1, К2, К3)</p>
            </div>
          </div>
        </div>
      )}

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

      {/* Status filter + advanced filters toggle */}
      <div className="flex gap-2 p-2 sticky top-28 z-20 bg-rz-green items-center">
        <button
          onClick={() => setFilter(filter === 'available' ? 'all' : 'available')}
          className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ${
            filter === 'available'
              ? 'bg-rz-gold text-rz-green-dark font-medium'
              : 'bg-rz-green-mid text-rz-cream-dark'
          }`}
        >
          Свободно ({bStats.available})
        </button>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ${
            hasAdvancedFilters ? 'bg-rz-gold text-rz-green-dark font-medium' : 'bg-rz-green-mid text-rz-cream-dark'
          }`}
        >
          Фильтры
        </button>
      </div>

      {/* Advanced filters panel */}
      {showFilters && (
        <div className="px-2 pb-2 bg-rz-green sticky top-40 z-10 max-w-full">
          <div className="bg-rz-green-light rounded-xl p-3 space-y-3 overflow-hidden">
            <div>
              <p className="text-xs text-rz-cream-dark mb-1.5">Площадь, м²</p>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="от" value={areaMin} onChange={e => setAreaMin(e.target.value)}
                  className="w-full bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold min-w-0"/>
                <input type="number" placeholder="до" value={areaMax} onChange={e => setAreaMax(e.target.value)}
                  className="w-full bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold min-w-0"/>
              </div>
            </div>
            <div>
              <p className="text-xs text-rz-cream-dark mb-1.5">Цена, млн ₽</p>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="от" value={priceMin} onChange={e => setPriceMin(e.target.value)}
                  className="w-full bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold min-w-0"/>
                <input type="number" placeholder="до" value={priceMax} onChange={e => setPriceMax(e.target.value)}
                  className="w-full bg-rz-green-mid rounded-lg px-2 py-1.5 text-xs text-rz-cream outline-none focus:ring-1 focus:ring-rz-gold min-w-0"/>
              </div>
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
