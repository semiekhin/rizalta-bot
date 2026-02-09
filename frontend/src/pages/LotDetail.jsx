import { useState } from 'preact/hooks'

const formatPrice = (p) => new Intl.NumberFormat('ru-RU').format(p)

export default function LotDetail({ lot, onBack, onChat }) {
  // ROI
  const [showROI, setShowROI] = useState(false)
  const [roiData, setRoiData] = useState(null)
  const [roiLoading, setRoiLoading] = useState(false)
  
  // Showing
  const [showShowing, setShowShowing] = useState(false)
  const [showingForm, setShowingForm] = useState({ name: '', phone: '', comment: '' })
  const [showingSent, setShowingSent] = useState(false)

  // KP
  const [showKP, setShowKP] = useState(false)
  const [kpLoading, setKpLoading] = useState(false)

  // Installment
  const [showInstallment, setShowInstallment] = useState(false)
  const [installmentData, setInstallmentData] = useState(null)
  const [installmentLoading, setInstallmentLoading] = useState(false)

  // Deposit
  const [showDeposit, setShowDeposit] = useState(false)
  const [depositData, setDepositData] = useState(null)
  const [depositLoading, setDepositLoading] = useState(false)

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
      if (data.ok) setRoiData(data.data)
    } catch (e) {
      console.error(e)
    }
    setRoiLoading(false)
  }

  // === Showing ===
  const handleShowingSubmit = async (e) => {
    e.preventDefault()
    try {
      await fetch('/api/book-showing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...showingForm, lot_code: lot.code })
      })
      setShowingSent(true)
    } catch (e) {
      console.error(e)
    }
  }

  // === KP Download ===
  const handleKPDownload = (type) => {
    setKpLoading(true)
    const url = `/api/download-kp/${encodeURIComponent(lot.code)}?type=${type}`
    
    // Telegram WebApp
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openLink(window.location.origin + url)
    } else {
      const a = document.createElement('a')
      a.href = url
      a.download = `KP_${lot.code}_${type}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    }
    setTimeout(() => {
      setKpLoading(false)
      setShowKP(false)
    }, 1000)
  }

  // === Excel Download ===
  const handleExcelDownload = () => {
    const url = `/api/download-xlsx/${encodeURIComponent(lot.code)}`
    
    // Telegram WebApp
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.openLink(window.location.origin + url)
    } else {
      const a = document.createElement('a')
      a.href = url
      a.download = `ROI_${lot.code}.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    }
  }

  // === Installment ===
  const handleInstallment = async () => {
    setShowInstallment(true)
    setInstallmentLoading(true)
    try {
      const res = await fetch('/api/installment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: lot.price })
      })
      const data = await res.json()
      if (data.ok) setInstallmentData(data.data)
    } catch (e) {
      console.error(e)
    }
    setInstallmentLoading(false)
  }

  // === Deposit Comparison ===
  const handleDeposit = async () => {
    setShowDeposit(true)
    setDepositLoading(true)
    try {
      const res = await fetch('/api/compare-deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: lot.price, years: 11, scenario: 'all' })
      })
      const data = await res.json()
      if (data.ok) setDepositData(data.data)
    } catch (e) {
      console.error(e)
    }
    setDepositLoading(false)
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
          <img src={lot.layout_url} alt={`Планировка ${lot.code}`} className="h-full w-full object-contain bg-white"/>
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
            lot.status === 'available' ? 'bg-emerald-500 text-white' 
            : lot.status === 'booked' ? 'bg-amber-500 text-black' : 'bg-gray-500 text-white'
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
          <button onClick={() => setShowKP(true)} className="w-full bg-amber-500 text-black font-bold py-3 rounded-xl hover:bg-amber-400 transition-colors">
            📄 Получить КП
          </button>
          <button onClick={handleInstallment} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            💳 Варианты оплаты
          </button>
          <button onClick={handleROI} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            📊 Расчёт доходности
          </button>
          <button onClick={handleDeposit} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            🏦 Сравнить с депозитом
          </button>
          <button onClick={handleExcelDownload} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            📥 Скачать Excel
          </button>
          <button onClick={() => setShowShowing(true)} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            📅 Записаться на показ
          </button>
          <button onClick={onChat} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            💬 Задать вопрос
          </button>
        </div>
      </div>

      {/* KP Modal */}
      {showKP && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-slate-800 w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h2 className="font-bold text-lg">📄 Выберите вариант КП</h2>
              <button onClick={() => setShowKP(false)} className="text-slate-400 text-xl">✕</button>
            </div>
            <div className="p-4 space-y-3">
              {kpLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : (
                <>
                  <button onClick={() => handleKPDownload('100')} className="w-full bg-emerald-600 text-white py-3 rounded-xl hover:bg-emerald-500">
                    💰 100% оплата (скидка 5%)
                  </button>
                  <button onClick={() => handleKPDownload('12m')} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600">
                    📅 Рассрочка 12 мес (0%)
                  </button>
                  <button onClick={() => handleKPDownload('full')} className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600">
                    📋 Полное КП (12 + 18 мес)
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Installment Modal */}
      {showInstallment && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-slate-800 w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h2 className="font-bold text-lg">💳 Варианты оплаты</h2>
              <button onClick={() => setShowInstallment(false)} className="text-slate-400 text-xl">✕</button>
            </div>
            <div className="p-4">
              {installmentLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : installmentData ? (
                <div className="space-y-4">
                  <div className="bg-slate-700 rounded-xl p-3">
                    <p className="text-slate-400 text-sm">Стоимость</p>
                    <p className="font-bold text-lg text-amber-400">{formatPrice(installmentData.price)} ₽</p>
                  </div>

                  {/* 12 месяцев */}
                  <div className="border border-emerald-500 rounded-xl p-4">
                    <h3 className="font-bold text-emerald-400 mb-3">12 месяцев (0%)</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">ПВ 30%</span>
                        <span>{formatPrice(installmentData.i12.pv_30)} ₽ → {formatPrice(installmentData.i12.monthly_30)} ₽/мес</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">ПВ 40%</span>
                        <span>{formatPrice(installmentData.i12.pv_40)} ₽ → 11×200К + {formatPrice(installmentData.i12.last_40)} ₽</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">ПВ 50%</span>
                        <span>{formatPrice(installmentData.i12.pv_50)} ₽ → 11×100К + {formatPrice(installmentData.i12.last_50)} ₽</span>
                      </div>
                    </div>
                  </div>

                  {/* 18 месяцев */}
                  <div className="border border-amber-500 rounded-xl p-4">
                    <h3 className="font-bold text-amber-400 mb-3">18 месяцев</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">ПВ 30% (+9%)</span>
                          <span>{formatPrice(installmentData.i18.pv_30)} ₽</span>
                        </div>
                        <p className="text-slate-500 text-xs">18 × {formatPrice(installmentData.i18.monthly_30)} ₽ → Итого: {formatPrice(installmentData.i18.final_price_30)} ₽</p>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">ПВ 40% (+7%)</span>
                          <span>{formatPrice(installmentData.i18.pv_40)} ₽</span>
                        </div>
                        <p className="text-slate-500 text-xs">8×250К, 9-й: {formatPrice(installmentData.i18.payment_9)} ₽, 8×250К, 18-й: {formatPrice(installmentData.i18.last_40)} ₽</p>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">ПВ 50% (+4%)</span>
                          <span>{formatPrice(installmentData.i18.pv_50)} ₽</span>
                        </div>
                        <p className="text-slate-500 text-xs">8×150К, 9-й: {formatPrice(installmentData.i18.payment_9)} ₽, 8×150К, 18-й: {formatPrice(installmentData.i18.last_50)} ₽</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-red-400">Ошибка загрузки</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ROI Modal */}
      {showROI && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
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

      {/* Deposit Modal */}
      {showDeposit && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-slate-800 w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h2 className="font-bold text-lg">🏦 Сравнение с депозитом</h2>
              <button onClick={() => setShowDeposit(false)} className="text-slate-400 text-xl">✕</button>
            </div>
            <div className="p-4">
              {depositLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : depositData ? (
                <div className="space-y-4">
                  <div className="bg-slate-700 rounded-xl p-3">
                    <p className="text-slate-400 text-sm">Сумма инвестиций</p>
                    <p className="font-bold text-lg">{formatPrice(lot.price)} ₽ на 11 лет</p>
                  </div>

                  {/* RIZALTA */}
                  <div className="bg-emerald-900/50 rounded-xl p-4">
                    <h3 className="font-bold text-emerald-400 mb-2">🏠 RIZALTA</h3>
                    {roiData ? (
                      <>
                        <p className="text-2xl font-bold text-emerald-400">{formatPrice(roiData.total_profit)} ₽</p>
                        <p className="text-slate-400 text-sm">ROI: {roiData.roi_pct}% за 11 лет</p>
                      </>
                    ) : (
                      <p className="text-slate-400 text-sm">Нажмите "Расчёт доходности"</p>
                    )}
                  </div>

                  {/* Депозиты */}
                  <div className="space-y-3">
                    {Object.entries(depositData).map(([key, d]) => (
                      <div key={key} className="bg-slate-700 rounded-xl p-4">
                        <h4 className="font-medium text-amber-400 mb-1">{d.scenario_name}</h4>
                        <p className="text-xl font-bold">{formatPrice(d.total_net_interest)} ₽</p>
                        <p className="text-slate-400 text-sm">
                          ROI: {d.total_roi_pct}% • Налог: -{formatPrice(d.total_tax)} ₽
                        </p>
                      </div>
                    ))}
                  </div>

                  <p className="text-slate-500 text-xs text-center">
                    Данные по депозитам на основе прогноза ЦБ РФ
                  </p>
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
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
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
                    <input type="text" required value={showingForm.name}
                      onChange={(e) => setShowingForm({...showingForm, name: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white" placeholder="Иван"/>
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm">Телефон</label>
                    <input type="tel" required value={showingForm.phone}
                      onChange={(e) => setShowingForm({...showingForm, phone: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white" placeholder="+7 999 123-45-67"/>
                  </div>
                  <div>
                    <label className="text-slate-400 text-sm">Комментарий (необязательно)</label>
                    <textarea value={showingForm.comment}
                      onChange={(e) => setShowingForm({...showingForm, comment: e.target.value})}
                      className="w-full bg-slate-700 rounded-xl px-4 py-3 mt-1 text-white resize-none" rows={2} placeholder="Удобное время для звонка"/>
                  </div>
                  <button type="submit" className="w-full bg-amber-500 text-black font-bold py-3 rounded-xl hover:bg-amber-400 transition-colors">
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
