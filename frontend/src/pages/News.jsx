import React, { useState, useEffect } from 'react'

export default function News({ onBack }) {
  const [currency, setCurrency] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/news/currency')
      .then(r => r.json())
      .then(d => {
        if (d.ok) setCurrency(d.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">📰 Новости</h1>
      </div>

      <div className="p-4 space-y-4">
        <p className="text-rz-cream-dark text-sm font-medium">💱 Курсы валют ЦБ РФ</p>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
          </div>
        ) : currency ? (
          <div className="space-y-2">
            {currency.map(c => (
              <div key={c.code} className="bg-rz-green-light rounded-xl p-4 flex justify-between items-center border border-rz-green-mid">
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-rz-cream-dark">{c.code}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-rz-gold">{c.value} ₽</p>
                  <p className={`text-xs ${c.change >= 0 ? 'text-rz-success' : 'text-rz-error'}`}>
                    {c.change >= 0 ? '+' : ''}{c.change}
                  </p>
                </div>
              </div>
            ))}
            {currency.length > 0 && (
              <p className="text-xs text-rz-cream-muted text-center mt-2">Данные ЦБ РФ на {currency[0].date || 'сегодня'}</p>
            )}
          </div>
        ) : (
          <p className="text-rz-cream-dark text-center py-8">Не удалось загрузить курсы валют</p>
        )}
      </div>
    </div>
  )
}
