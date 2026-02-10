import React, { useState, useEffect } from 'react'
import { authFetch, getToken } from '../utils/auth'

const formatPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)} млн` : `${Math.round(p/1e3)} тыс`
const shortPrice = (p) => p >= 1e6 ? `${(p/1e6).toFixed(1)}` : `${Math.round(p/1e3)}т`

export default function Corp3({ onSelectLot, onBack }) {
  const [lots, setLots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [floor, setFloor] = useState(null)
  const [filter, setFilter] = useState('all')
  const [showFilters, setShowFilters] = useState(false)
  const [areaMin, setAreaMin] = useState('')
  const [areaMax, setAreaMax] = useState('')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')

  useEffect(() => {
    authFetch('/api/corp3/lots')
      .then(r => {
        if (r.status === 403) {
          setError('denied')
          setLoading(false)
          return null
        }
        return r.json()
      })
      .then(d => {
        if (d && d.ok) setLots(d.lots || [])
        setLoading(false)
      })
      .catch(() => { setError('network'); setLoading(false) })
  }, [])

  const hasAdvancedFilters = areaMin || areaMax || priceMin || priceMax

  const resetFilters = () => {
    setAreaMin(''); setAreaMax(''); setPriceMin(''); setPriceMax(''); setFilter('all')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-rz-green flex flex-col items-center justify-center text-rz-cream pb-20">
        <div className="w-10 h-10 border-4 border-rz-gold border-t-transparent rounded-full animate-spin mb-4"/>
        <p>Загрузка лотов К3...</p>
      </div>
    )
  }

  if (error === 'denied') {
    return (
      <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
        <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
          <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
          <h1 className="font-bold">🏗 Корпус 3 «Digital»</h1>
        </div>
        <div className="p-4">
          <div className="bg-rz-green-light rounded-xl p-6 text-center border border-rz-green-mid">
            <p className="text-4xl mb-4">🔒</p>
            <h2 className="text-lg font-bold mb-2">Доступ ограничен</h2>
            <p className="text-rz-cream-dark text-sm">Корпус 3 доступен только по приглашению.</p>
          </div>
        </div>
      </div>
    )
  }

  const floors = [...new Set(lots.map(l => l.floor))].sort((a, b) => b - a)
  const availCount = lots.filter(l => l.status === 'available').length

  const applyFilters = (list) => {
    let result = list
    if (filter === 'available') result = result.filter(l => l.status === 'available')
    if (areaMin) result = result.filter(l => l.area >= parseFloat(areaMin))
    if (areaMax) result = result.filter(l => l.area <= parseFloat(areaMax))
    if (priceMin) result = result.filter(l => l.price >= parseFloat(priceMin) * 1e6)
    if (priceMax) result = result.filter(l => l.price <= parseFloat(priceMax) * 1e6)
    return result
  }

  const filteredTotal = applyFilters(lots).length

  const getFloorLots = (f) => {
    const fl = lots.filter(l => l.floor === f).sort((a, b) => a.area - b.area)
    return applyFilters(fl)
  }

  const token = getToken()

  const handleSelectLot = (lot) => {
    onSelectLot({
      ...lot,
      buildingName: 'Digital',
      layout_url: lot.layout_path ? `/api/corp3/layout/${encodeURIComponent(lot.code)}?token=${encodeURIComponent(token)}` : null,
      source: 'corp3'
    })
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20 overflow-x-hidden">
      {/* Header */}
      <div className="bg-rz-gold px-4 py-3 flex justify-between items-center sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="text-rz-green-dark hover:text-rz-green transition-colors font-bold">←</button>
          <div>
            <h1 className="font-bold text-lg text-rz-green-dark">Корпус 3 «Digital»</h1>
            <p className="text-xs text-rz-green-dark/70">Эксклюзивные апартаменты</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-rz-green-dark">{lots.length}</p>
          <p className="text-xs text-rz-green-dark/70">лотов</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 p-2 sticky top-14 z-20 bg-rz-green items-center">
        <button
          onClick={() => setFilter(filter === 'available' ? 'all' : 'available')}
          className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition-colors ${
            filter === 'available'
              ? 'bg-rz-gold text-rz-green-dark font-medium'
              : 'bg-rz-green-mid text-rz-cream-dark'
          }`}
        >
          Свободно ({availCount})
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
        <div className="px-2 pb-2 bg-rz-green sticky top-28 z-10 max-w-full">
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
              <p className="text-xs text-rz-cream-dark">Найдено: <span className="text-rz-gold font-medium">{filteredTotal}</span> из {lots.length}</p>
              {hasAdvancedFilters && (
                <button onClick={resetFilters} className="text-xs text-rz-cream-muted hover:text-rz-cream">Сброс</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Found counter */}
      {!showFilters && hasAdvancedFilters && (
        <div className="px-4 py-1">
          <p className="text-xs text-rz-cream-dark">Найдено: <span className="text-rz-gold font-medium">{filteredTotal}</span> из {lots.length}</p>
        </div>
      )}

      {/* Floors */}
      <div className="p-2 space-y-2">
        {floors.map(f => {
          const floorLots = getFloorLots(f)
          const allFloorLots = lots.filter(l => l.floor === f)
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
                      onClick={() => handleSelectLot(l)}
                      className="rounded-lg p-2 flex flex-col items-center justify-center transition-transform bg-rz-success hover:scale-105"
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
