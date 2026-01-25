import { useState } from 'preact/hooks'

const formatPrice = (p) => new Intl.NumberFormat('ru-RU').format(p)

export default function LotDetail({ lot, onBack, onChat }) {
  const [showROI, setShowROI] = useState(false)
  const [roiData, setRoiData] = useState(null)
  const [roiLoading, setRoiLoading] = useState(false)
  
  const [showShowing, setShowShowing] = useState(false)
  const [showingForm, setShowingForm] = useState({ name: '', phone: '', comment: '' })
  const [showingSent, setShowingSent] = useState(false)

  if (!lot) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center pb-20">
        <p className="text-slate-400">Лот не выбран</p>
      </div>
    )
  }

  const pricePerM2 = Math.round(lot.price / lot.area)

  // === ROI ===
  const handleROI = async () => {
    setShowROI(true)
    setRoiLoading(true)
    try {
      const res = await fetch('/api/calculate-roi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ area: lot.area, price: lot.price })
      })
      const data = await res.json()
      if (data.ok) {
        setRoiData(data.data)
      }
    } catch (e) {
      console.error(e)
    }
    setRoiLoading(false)
  }

  // === Запись на показ ===
  const handleShowingSubmit = async (e) => {
    e.preventDefault()
    try {
      await fetch('/api/book-showing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...showingForm,
          lot_code: lot.code
        })
      })
      setShowingSent(true)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-20">
      {/* Header */}
      <div className="bg-slate-800 px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-slate-400 hover:text-white transition-colors">
          ← Назад
        </button>
        <h1 className="font-bold">Апартамент {lot.code}</h1>
      </div>

      {/* Image */}
      <div className="bg-slate-700 h-52 flex items-center justify-center">
        {lot.layout_url ? (
          <img 
            src={lot.layout_url} 
            alt={`Планировка ${lot.code}`} 
            className="h-full w-full object-contain bg-white"
          />
        ) : (
          <div className="text-center text-slate-400">
            <p className="text-5xl mb-2">🏠</p>
            <p className="text-sm">Планировка {lot.area} м²</p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 space-y-4">
        {/* Price & Status */}
        <div className="flex justify-between items-center">
          <div>
            <p className="text-slate-400 text-sm">Стоимость</p>
            <p className="text-2xl font-bold text-amber-400">{formatPrice(lot.price)} ₽</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            lot.status === 'available' 
              ? 'bg-emerald-500 text-white' 
              : lot.status === 'booked'
                ? 'bg-amber-500 text-black'
                : 'bg-gray-500 text-white'
          }`}>
            {lot.status === 'available' ? '✓ Свободен' : lot.status === 'booked' ? '◐ Бронь' : '✕ Продан'}
          </span>
        </div>

        {/* Specs grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Площадь</p>
            <p className="font-bold text-lg">{lot.area} м²</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Этаж</p>
            <p className="font-bold text-lg">{lot.floor}</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Корпус</p>
            <p className="font-bold text-lg">{lot.building} ({lot.buildingName})</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Цена за м²</p>
            <p className="font-bold text-lg">{formatPrice(pricePerM2)} ₽</p>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2 pt-2">
          <button className="w-full bg-amber-500 text-black font-bold py-3 rounded-xl hover:bg-amber-400 transition-colors">
            📄 Получить КП
          </button>
          <button 
            onClick={handleROI}
            className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors"
          >
            📊 Расчёт доходности
          </button>
          <button 
            onClick={() => setShowShowing(true)}
            className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors"
          >
            📅 Записаться на показ
          </button>
          <button 
            onClick={onChat}
            className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors"
          >
            💬 Задать вопрос
          </button>
        </div>
      </div>

      {/* ROI Modal */}
      {showROI && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-slate-800 w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h2 className="font-bold text-lg">📊 Расчёт доходности</h2>
              <button onClick={() => setShowROI(false)} className="text-slate-400 text-xl">✕</button>
            </div>
            
            <div className="p-4">
              {roiLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : roiData ? (
                <div className="space-y-4">
                  <div className="bg-slate-700 rounded-xl p-4">
                    <p className="text-slate-400 text-sm">Лот {lot.code}</p>
                    <p className="text-white">{lot.area} м² • {formatPrice(lot.price)} ₽</p>
                  </div>
                  
                  <div className="bg-emerald-900/50 rounded-xl p-4">
                    <p className="text-emerald-400 text-sm">Доходность за 11 лет</p>
                    <p className="text-3xl font-bold text-emerald-400">{roiData.roi_pct}%</p>
                    <p className="text-slate-400 text-sm">~{roiData.avg_annual_pct}% годовых</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-700 rounded-xl p-3">
                      <p className="text-slate-400 text-xs">От аренды</p>
                      <p className="font-bold text-amber-400">{formatPrice(roiData.total_rental)} ₽</p>
                    </div>
                    <div className="bg-slate-700 rounded-xl p-3">
                      <p className="text-slate-400 text-xs">От роста</p>
                      <p className="font-bold text-amber-400">{formatPrice(roiData.total_growth)} ₽</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-700 rounded-xl p-4">
                    <p className="text-slate-400 text-sm">Общая прибыль</p>
                    <p className="text-2xl font-bold text-amber-400">{formatPrice(roiData.total_profit)} ₽</p>
                  </div>
                  
                  <div className="bg-slate-700 rounded-xl p-4">
                    <p className="text-slate-400 text-sm">Стоимость в 2035</p>
                    <p className="text-xl font-bold">{formatPrice(roiData.final_value)} ₽</p>
                  </div>
                </div>
              ) : (
                <p className="text-red-400">Ошибка загрузки</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Showing Modal */}
      {showShowing && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-slate-800 w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h2 className="font-bold text-lg">📅 Запись на показ</h2>
              <button onClick={() => {setShowShowing(false); setShowingSent(false)}} className="text-slate-400 text-xl">✕</button>
            </div>
            
            <div className="p-4">
              {showingSent ? (
                <div className="text-center py-6">
                  <p className="text-4xl mb-3">✅</p>
                  <p className="text-xl font-bold text-emerald-400">Заявка отправлена!</p>
                  <p className="text-slate-400 mt-2">Мы свяжемся с вами в ближайшее время</p>
                </div>
              ) : (
                <form onSubmit={handleShowingSubmit} className="space-y-4">
                  <div>
                    <label className="text-slate-400 text-sm">Ваше имя</label>
                    <input
                      type="text"
                      required
                      value={showingForm.name}
                      onChange={(e) => setShowingForm({...showingForm, name: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white"
                      placeholder="Иван"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm">Телефон</label>
                    <input
                      type="tel"
                      required
                      value={showingForm.phone}
                      onChange={(e) => setShowingForm({...showingForm, phone: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white"
                      placeholder="+7 999 123-45-67"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm">Комментарий (необязательно)</label>
                    <textarea
                      value={showingForm.comment}
                      onChange={(e) => setShowingForm({...showingForm, comment: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white resize-none"
                      rows={2}
                      placeholder="Удобное время для звонка"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-amber-500 text-black font-bold py-3 rounded-xl hover:bg-amber-400 transition-colors"
                  >
                    Отправить заявку
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
