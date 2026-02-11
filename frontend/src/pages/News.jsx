import React, { useState, useEffect } from 'react'

const TABS = [
  { id: 'currency', label: '💵 Курсы' },
  { id: 'weather', label: '☀️ Погода' },
  { id: 'flights', label: '✈️ Билеты' },
  { id: 'digest', label: '📊 Дайджест' },
]

function fmt(n) {
  return n.toLocaleString('ru-RU')
}

export default function News({ onBack }) {
  const [tab, setTab] = useState('currency')
  const [currency, setCurrency] = useState(null)
  const [weather, setWeather] = useState(null)
  const [flights, setFlights] = useState(null)
  const [digest, setDigest] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadTab(tab)
  }, [tab])

  async function loadTab(t) {
    setLoading(true)
    setError(null)
    try {
      if (t === 'currency' && !currency) {
        const res = await fetch('/api/news/currency')
        const data = await res.json()
        if (data.ok) setCurrency(data.data)
        else setError(data.error)
      } else if (t === 'weather' && !weather) {
        const res = await fetch('/api/news/weather')
        const data = await res.json()
        if (data.ok) setWeather(data.data)
        else setError(data.error)
      } else if (t === 'flights' && !flights) {
        const res = await fetch('/api/news/flights')
        const data = await res.json()
        if (data.ok) setFlights(data.data)
        else setError(data.error)
      } else if (t === 'digest' && !digest) {
        const res = await fetch('/api/news/digest')
        const data = await res.json()
        if (data.ok) setDigest(data.data)
        else setError(data.error)
      }
    } catch {
      setError('Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  async function refresh() {
    if (tab === 'currency') setCurrency(null)
    else if (tab === 'weather') setWeather(null)
    else if (tab === 'flights') setFlights(null)
    else if (tab === 'digest') setDigest(null)
    setTimeout(() => loadTab(tab), 50)
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-24">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold flex-1">📰 Инвест-дайджест</h1>
        <button onClick={refresh} className="text-rz-cream-dark hover:text-rz-cream text-sm">🔄</button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-2 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
              tab === t.id
                ? 'bg-rz-gold text-rz-green-dark'
                : 'bg-rz-green-light text-rz-cream-dark'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {loading && <p className="text-rz-cream-muted text-sm text-center py-8">Загрузка...</p>}
        {error && <p className="text-rz-error text-sm text-center py-4">{error}</p>}

        {/* Currency */}
        {tab === 'currency' && currency && (
          <div className="space-y-3">
            {currency.map(c => (
              <div key={c.code} className="bg-rz-green-light rounded-xl p-4 flex items-center justify-between border border-rz-green-mid">
                <div>
                  <span className="text-sm font-medium">{c.code === 'USD' ? '🇺🇸' : c.code === 'EUR' ? '🇪🇺' : '🇨🇳'} {c.name}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold">{c.value.toFixed(2)} ₽</span>
                  <span className={`ml-2 text-xs ${c.change > 0 ? 'text-rz-error' : c.change < 0 ? 'text-rz-success' : 'text-rz-cream-muted'}`}>
                    {c.change > 0 ? '↑' : c.change < 0 ? '↓' : '—'}{Math.abs(c.change).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
            <p className="text-rz-cream-muted text-xs text-center mt-2">
              Источник: ЦБ РФ{currency[0]?.date ? ` на ${currency[0].date}` : ''}
            </p>
          </div>
        )}

        {/* Weather */}
        {tab === 'weather' && weather && (
          <div className="bg-rz-green-light rounded-xl p-5 border border-rz-green-mid">
            <div className="text-center mb-4">
              <span className="text-4xl">{weather.icon}</span>
              <p className="text-3xl font-bold mt-2">{weather.temp}°C</p>
              <p className="text-rz-cream-dark text-sm">{weather.description}</p>
            </div>
            <div className="flex justify-center gap-6 text-sm text-rz-cream-dark mb-4">
              <span>💨 {weather.wind} м/с</span>
              <span>💧 {weather.humidity}%</span>
            </div>
            {weather.forecast && weather.forecast.length > 0 && (
              <div className="border-t border-rz-green-mid pt-3 mt-3">
                <p className="text-xs text-rz-cream-muted mb-2 text-center">Прогноз:</p>
                <div className="flex justify-center gap-4">
                  {weather.forecast.map((f, i) => (
                    <div key={i} className="text-center text-sm">
                      <span>{f.icon}</span>
                      <p className="font-medium">{f.temp}°C</p>
                      <p className="text-xs text-rz-cream-muted">{f.hour}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="text-rz-cream-muted text-xs text-center mt-4">
              🏔 Белокуриха — 260+ солнечных дней в году
            </p>
          </div>
        )}

        {/* Flights */}
        {tab === 'flights' && flights && (
          <div className="space-y-3">
            <div className="bg-rz-green-light rounded-xl p-4 border border-rz-green-mid text-center">
              <p className="text-sm text-rz-cream-dark">Минимальная цена</p>
              <p className="text-2xl font-bold text-rz-gold">{fmt(flights.min_price)} ₽</p>
              <p className="text-xs text-rz-cream-muted">Москва → Горно-Алтайск</p>
            </div>

            {flights.min_direct && (
              <div className="bg-rz-green-light rounded-xl p-4 border border-rz-gold/30">
                <p className="text-xs text-rz-gold font-medium mb-1">🎯 Лучший прямой рейс</p>
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-sm font-medium">{flights.min_direct.airline}</span>
                    <span className="text-xs text-rz-cream-muted ml-2">{flights.min_direct.date}</span>
                  </div>
                  <span className="font-bold">{fmt(flights.min_direct.price)} ₽</span>
                </div>
                <p className="text-xs text-rz-cream-muted">{flights.min_direct.duration}</p>
              </div>
            )}

            <p className="text-xs text-rz-cream-dark font-medium pt-1">Лучшие цены:</p>
            {flights.cheapest.map((f, i) => (
              <div key={i} className="bg-rz-green-light rounded-xl p-3 border border-rz-green-mid flex justify-between items-center">
                <div>
                  <span className="text-sm font-medium">{f.airline}</span>
                  <span className="text-xs text-rz-cream-muted ml-2">{f.date}</span>
                  <p className="text-xs text-rz-cream-muted">{f.transfer_text} • {f.duration}</p>
                </div>
                <span className="font-bold text-sm">{fmt(f.price)} ₽</span>
              </div>
            ))}

            <p className="text-rz-cream-muted text-xs text-center mt-2">
              Найдено рейсов: {flights.total_found}
            </p>
            <p className="text-rz-cream-muted text-xs text-center">
              💡 Прилетайте на осмотр — мы организуем трансфер!
            </p>
          </div>
        )}

        {/* Digest */}
        {tab === 'digest' && digest && (
          <div className="space-y-2">
            {digest.length === 0 && (
              <p className="text-rz-cream-muted text-sm text-center py-8">Нет новостей</p>
            )}
            {digest.map((item, i) => (
              <a
                key={i}
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-rz-green-light rounded-xl p-3 border border-rz-green-mid hover:border-rz-gold/30 transition-colors"
              >
                <p className="text-sm font-medium leading-snug">{item.title}</p>
                <p className="text-xs text-rz-cream-muted mt-1">{item.source}</p>
              </a>
            ))}
            <p className="text-rz-cream-muted text-xs text-center mt-4">
              💡 Следите за рынком — инвестируйте в недвижимость вовремя!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
