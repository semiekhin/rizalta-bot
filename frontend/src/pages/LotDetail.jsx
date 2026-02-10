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
      <div className="min-h-screen bg-rz-green text-rz-cream flex items-center justify-center pb-20">
        <p className="text-rz-cream-dark">Лот не выбран</p>
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
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">
          ← Назад
        </button>
        <h1 className="font-bold">Апартамент {lot.code}</h1>
      </div>

      {/* Image */}
      <div className="bg-rz-green-mid h-52 flex items-center justify-center">
        {lot.layout_url ? (
          <img src={lot.layout_url} alt={`Планировка ${lot.code}`} className="h-full w-full object-contain bg-white"/>
        ) : (
          <div className="text-center text-rz-cream-dark">
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
            <p className="text-rz-cream-dark text-sm">Стоимость</p>
            <p className="text-2xl font-bold text-rz-gold">{formatPrice(lot.price)} ₽</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            lot.status === 'available' ? 'bg-rz-success text-white'
            : lot.status === 'booked' ? 'bg-rz-gold text-rz-green-dark' : 'bg-rz-cream-muted text-white'
          }`}>
            {lot.status === 'available' ? '✓ Свободен' : lot.status === 'booked' ? '◐ Бронь' : '✕ Продан'}
          </span>
        </div>

        {/* Specs grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-rz-green-light rounded-xl p-3">
            <p className="text-rz-cream-dark text-xs">Площадь</p>
            <p className="font-bold text-lg">{lot.area} м²</p>
          </div>
          <div className="bg-rz-green-light rounded-xl p-3">
            <p className="text-rz-cream-dark text-xs">Этаж</p>
            <p className="font-bold text-lg">{lot.floor}</p>
          </div>
          <div className="bg-rz-green-light rounded-xl p-3">
            <p className="text-rz-cream-dark text-xs">Корпус</p>
            <p className="font-bold text-lg">{lot.building} ({lot.buildingName})</p>
          </div>
          <div className="bg-rz-green-light rounded-xl p-3">
            <p className="text-rz-cream-dark text-xs">Цена за м²</p>
            <p className="font-bold text-lg">{formatPrice(pricePerM2)} ₽</p>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2 pt-2">
          {lot.source !== 'corp3' && (
            <button onClick={() => setShowKP(true)} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
              📄 Получить КП
            </button>
          )}
          <button onClick={handleInstallment} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
            💳 Варианты оплаты
          </button>
          <button onClick={handleROI} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
            📊 Расчёт доходности
          </button>
          <button onClick={handleDeposit} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
            🏦 Сравнить с депозитом
          </button>
          {lot.source !== 'corp3' && (
            <button onClick={handleExcelDownload} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
              📥 Скачать Excel
            </button>
          )}
          <button onClick={() => setShowShowing(true)} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
            📅 Записаться на показ
          </button>
          <button onClick={onChat} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green-light transition-colors">
            💬 Задать вопрос
          </button>
        </div>
      </div>

      {/* KP Modal */}
      {showKP && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center">
              <h2 className="font-bold text-lg">📄 Выберите вариант КП</h2>
              <button onClick={() => setShowKP(false)} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-3">
              {kpLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : (
                <>
                  <button onClick={() => handleKPDownload('100')} className="w-full bg-rz-success text-white py-3 rounded-xl hover:opacity-90">
                    💰 100% оплата (скидка 5%)
                  </button>
                  <button onClick={() => handleKPDownload('12m')} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green">
                    📅 Рассрочка 12 мес (0%)
                  </button>
                  <button onClick={() => handleKPDownload('full')} className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green">
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
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-rz-green-light px-4 py-3 border-b border-rz-green-mid flex justify-between items-center">
              <h2 className="font-bold text-lg">💳 Варианты оплаты</h2>
              <button onClick={() => setShowInstallment(false)} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4">
              {installmentLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : installmentData ? (
                <div className="space-y-4">
                  <div className="bg-rz-green-mid rounded-xl p-3">
                    <p className="text-rz-cream-dark text-sm">Стоимость</p>
                    <p className="font-bold text-lg text-rz-gold">{formatPrice(installmentData.price)} ₽</p>
                  </div>

                  {/* 12 месяцев */}
                  <div className="border border-rz-success rounded-xl p-4">
                    <h3 className="font-bold text-rz-success mb-3">12 месяцев (0%)</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-rz-cream-dark">ПВ 30%</span>
                        <span>{formatPrice(installmentData.i12.pv_30)} ₽ → {formatPrice(installmentData.i12.monthly_30)} ₽/мес</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-rz-cream-dark">ПВ 40%</span>
                        <span>{formatPrice(installmentData.i12.pv_40)} ₽ → 11×200К + {formatPrice(installmentData.i12.last_40)} ₽</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-rz-cream-dark">ПВ 50%</span>
                        <span>{formatPrice(installmentData.i12.pv_50)} ₽ → 11×100К + {formatPrice(installmentData.i12.last_50)} ₽</span>
                      </div>
                    </div>
                  </div>

                  {/* 18 месяцев */}
                  <div className="border border-rz-gold rounded-xl p-4">
                    <h3 className="font-bold text-rz-gold mb-3">18 месяцев</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <div className="flex justify-between">
                          <span className="text-rz-cream-dark">ПВ 30% (+9%)</span>
                          <span>{formatPrice(installmentData.i18.pv_30)} ₽</span>
                        </div>
                        <p className="text-rz-cream-muted text-xs">18 × {formatPrice(installmentData.i18.monthly_30)} ₽ → Итого: {formatPrice(installmentData.i18.final_price_30)} ₽</p>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-rz-cream-dark">ПВ 40% (+7%)</span>
                          <span>{formatPrice(installmentData.i18.pv_40)} ₽</span>
                        </div>
                        <p className="text-rz-cream-muted text-xs">8×250К, 9-й: {formatPrice(installmentData.i18.payment_9)} ₽, 8×250К, 18-й: {formatPrice(installmentData.i18.last_40)} ₽</p>
                      </div>
                      <div>
                        <div className="flex justify-between">
                          <span className="text-rz-cream-dark">ПВ 50% (+4%)</span>
                          <span>{formatPrice(installmentData.i18.pv_50)} ₽</span>
                        </div>
                        <p className="text-rz-cream-muted text-xs">8×150К, 9-й: {formatPrice(installmentData.i18.payment_9)} ₽, 8×150К, 18-й: {formatPrice(installmentData.i18.last_50)} ₽</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-rz-error">Ошибка загрузки</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ROI Modal */}
      {showROI && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-rz-green-light px-4 py-3 border-b border-rz-green-mid flex justify-between items-center z-10">
              <h2 className="font-bold text-lg">📊 Расчёт доходности</h2>
              <button onClick={() => setShowROI(false)} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4">
              {roiLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : roiData ? (
                <div className="space-y-4">
                  {/* Lot info + price per m² */}
                  <div className="bg-rz-green-mid rounded-xl p-4">
                    <p className="text-rz-cream-dark text-sm">Лот {lot.code}</p>
                    <p>{lot.area} м² • {formatPrice(lot.price)} ₽</p>
                    <p className="text-rz-cream-dark text-xs mt-1">Цена за м²: {formatPrice(pricePerM2)} ₽</p>
                  </div>

                  {/* Main ROI */}
                  <div className="bg-rz-success/15 rounded-xl p-4">
                    <p className="text-rz-success text-sm">Доходность за 11 лет</p>
                    <p className="text-3xl font-bold text-rz-success">{roiData.roi_pct}%</p>
                    <p className="text-rz-cream-dark text-sm">~{roiData.avg_annual_pct}% годовых</p>
                  </div>

                  {/* Breakdown */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-rz-green-mid rounded-xl p-3">
                      <p className="text-rz-cream-dark text-xs">От аренды</p>
                      <p className="font-bold text-rz-gold">{formatPrice(roiData.total_rental)} ₽</p>
                    </div>
                    <div className="bg-rz-green-mid rounded-xl p-3">
                      <p className="text-rz-cream-dark text-xs">От роста</p>
                      <p className="font-bold text-rz-gold">{formatPrice(roiData.total_growth)} ₽</p>
                    </div>
                  </div>

                  <div className="bg-rz-green-mid rounded-xl p-4">
                    <p className="text-rz-cream-dark text-sm">Общая прибыль</p>
                    <p className="text-2xl font-bold text-rz-gold">{formatPrice(roiData.total_profit)} ₽</p>
                  </div>

                  <div className="bg-rz-green-mid rounded-xl p-4">
                    <p className="text-rz-cream-dark text-sm">Стоимость в 2035</p>
                    <p className="text-xl font-bold">{formatPrice(roiData.final_value)} ₽</p>
                  </div>

                  {/* Yearly table */}
                  {roiData.years && roiData.years.length > 0 && (
                    <div>
                      <p className="text-rz-cream-dark text-sm font-medium mb-2">Детализация по годам</p>
                      <div className="overflow-x-auto rounded-xl border border-rz-green-mid">
                        <table className="w-full text-xs min-w-[340px]">
                          <thead>
                            <tr className="bg-rz-green-mid text-rz-cream-dark">
                              <th className="py-2 px-2 text-left font-medium">Год</th>
                              <th className="py-2 px-2 text-right font-medium">Рост</th>
                              <th className="py-2 px-2 text-right font-medium">Аренда</th>
                              <th className="py-2 px-2 text-right font-medium">Итого %</th>
                            </tr>
                          </thead>
                          <tbody>
                            {roiData.years.map((yr, i) => (
                              <tr key={yr.year} className={i % 2 === 0 ? 'bg-rz-green-light' : 'bg-rz-green-mid/50'}>
                                <td className="py-1.5 px-2 font-medium">{yr.year}</td>
                                <td className="py-1.5 px-2 text-right text-rz-gold">{formatPrice(yr.growth_profit)} ₽</td>
                                <td className="py-1.5 px-2 text-right text-rz-success">{formatPrice(yr.rental_profit)} ₽</td>
                                <td className="py-1.5 px-2 text-right font-medium">{yr.total_pct}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Excel download */}
                  <button onClick={handleExcelDownload} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
                    📥 Скачать Excel
                  </button>
                  <p className="text-rz-cream-muted text-xs text-center">Подробный расчёт в файле Excel</p>
                </div>
              ) : (
                <p className="text-rz-error">Ошибка загрузки</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Deposit Modal */}
      {showDeposit && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-rz-green-light px-4 py-3 border-b border-rz-green-mid flex justify-between items-center z-10">
              <h2 className="font-bold text-lg">🏦 Сравнение с депозитом</h2>
              <button onClick={() => setShowDeposit(false)} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4">
              {depositLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : depositData ? (
                <div className="space-y-4">
                  <div className="bg-rz-green-mid rounded-xl p-3">
                    <p className="text-rz-cream-dark text-sm">Сумма инвестиций</p>
                    <p className="font-bold text-lg">{formatPrice(lot.price)} ₽ на 11 лет</p>
                  </div>

                  {/* RIZALTA with breakdown */}
                  <div className="bg-rz-success/15 rounded-xl p-4">
                    <h3 className="font-bold text-rz-success mb-2">🏠 RIZALTA</h3>
                    {roiData ? (
                      <>
                        <p className="text-2xl font-bold text-rz-success">{formatPrice(roiData.total_profit)} ₽</p>
                        <p className="text-rz-cream-dark text-sm">ROI: {roiData.roi_pct}% за 11 лет</p>
                        <div className="mt-3 pt-3 border-t border-rz-success/30 grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <p className="text-rz-cream-dark text-xs">Рост стоимости</p>
                            <p className="font-medium text-rz-gold">{formatPrice(roiData.total_growth)} ₽</p>
                          </div>
                          <div>
                            <p className="text-rz-cream-dark text-xs">Аренда</p>
                            <p className="font-medium text-rz-gold">{formatPrice(roiData.total_rental)} ₽</p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="text-rz-cream-dark text-sm">Нажмите "Расчёт доходности" для детализации</p>
                    )}
                  </div>

                  {/* Advantage block */}
                  {roiData && depositData.base && (
                    <div className="bg-rz-gold/15 rounded-xl p-4 border border-rz-gold/30">
                      <p className="font-bold text-rz-gold">
                        ✅ RIZALTA выгоднее на {formatPrice(roiData.total_profit - depositData.base.total_net_interest)} ₽
                        {depositData.base.total_net_interest > 0 && (
                          <span className="text-sm font-medium"> (+{Math.round((roiData.total_profit / depositData.base.total_net_interest - 1) * 100)}%)</span>
                        )}
                      </p>
                      <p className="text-rz-cream-dark text-xs mt-1">по сравнению с базовым сценарием депозита</p>
                    </div>
                  )}

                  {/* Deposits */}
                  <div className="space-y-3">
                    {Object.entries(depositData).map(([key, d]) => (
                      <div key={key} className="bg-rz-green-mid rounded-xl p-4">
                        <h4 className="font-medium text-rz-gold mb-1">{d.scenario_name}</h4>
                        <p className="text-xl font-bold">{formatPrice(d.total_net_interest)} ₽</p>
                        <p className="text-rz-cream-dark text-sm">
                          ROI: {d.total_roi_pct}% • Налог: -{formatPrice(d.total_tax)} ₽
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Key factors */}
                  <div className="bg-rz-green-mid rounded-xl p-4">
                    <p className="text-rz-cream-dark text-xs font-medium mb-2">Ключевые факторы</p>
                    <div className="space-y-1.5 text-xs">
                      <p>📉 ЦБ прогнозирует снижение ставки до 7%</p>
                      <p>💸 Налог 13–15% по депозиту</p>
                      <p>📈 RIZALTA: рост + пассивный доход с 2028</p>
                      <p>🛡 Недвижимость — защита от инфляции</p>
                    </div>
                  </div>

                  {/* Excel download */}
                  <button onClick={handleExcelDownload} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
                    📥 Скачать Excel
                  </button>

                  <p className="text-rz-cream-muted text-xs text-center">
                    Данные по депозитам на основе прогноза ЦБ РФ
                  </p>
                </div>
              ) : (
                <p className="text-rz-error">Ошибка загрузки</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Showing Modal */}
      {showShowing && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center">
              <h2 className="font-bold text-lg">📅 Запись на показ</h2>
              <button onClick={() => {setShowShowing(false); setShowingSent(false)}} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4">
              {showingSent ? (
                <div className="text-center py-6">
                  <p className="text-4xl mb-3">✅</p>
                  <p className="text-xl font-bold text-rz-success">Заявка отправлена!</p>
                  <p className="text-rz-cream-dark mt-2">Мы свяжемся с вами в ближайшее время</p>
                </div>
              ) : (
                <form onSubmit={handleShowingSubmit} className="space-y-4">
                  <div>
                    <label className="text-rz-cream-dark text-sm">Ваше имя</label>
                    <input type="text" required value={showingForm.name}
                      onChange={(e) => setShowingForm({...showingForm, name: e.target.value})}
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold" placeholder="Иван"/>
                  </div>
                  <div>
                    <label className="text-rz-cream-dark text-sm">Телефон</label>
                    <input type="tel" required value={showingForm.phone}
                      onChange={(e) => setShowingForm({...showingForm, phone: e.target.value})}
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold" placeholder="+7 999 123-45-67"/>
                  </div>
                  <div>
                    <label className="text-rz-cream-dark text-sm">Комментарий (необязательно)</label>
                    <textarea value={showingForm.comment}
                      onChange={(e) => setShowingForm({...showingForm, comment: e.target.value})}
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream resize-none outline-none focus:ring-2 focus:ring-rz-gold" rows={2} placeholder="Удобное время для звонка"/>
                  </div>
                  <button type="submit" className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
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
