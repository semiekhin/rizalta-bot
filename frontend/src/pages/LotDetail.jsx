import { useState } from 'preact/hooks'
// TODO: reuse for Corp4 whitelist
// import { getToken } from '../utils/auth'

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
  const [showingError, setShowingError] = useState('')

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

  // MGP
  const [showMGP, setShowMGP] = useState(false)
  const [mgpData, setMgpData] = useState(null)
  const [mgpLoading, setMgpLoading] = useState(false)

  // Mortgage
  const [showMortgage, setShowMortgage] = useState(false)
  const [mortgageData, setMortgageData] = useState(null)
  const [mortgageLoading, setMortgageLoading] = useState(false)
  const [mortgageDP, setMortgageDP] = useState(30)
  const [mortgageTariff, setMortgageTariff] = useState('base')
  const [mortgageTerm, setMortgageTerm] = useState(360)

  // Tranche Mortgage
  const [showTrancheMortgage, setShowTrancheMortgage] = useState(false)
  const [trancheMortgageData, setTrancheMortgageData] = useState(null)
  const [trancheMortgageLoading, setTrancheMortgageLoading] = useState(false)

  // Summary
  const [showSummary, setShowSummary] = useState(false)
  const [summaryData, setSummaryData] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

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
    const phoneClean = showingForm.phone.replace(/[\s\-\(\)]/g, '')
    if (phoneClean.length < 10) {
      setShowingError('Введите корректный номер телефона')
      return
    }
    setShowingError('')
    try {
      const resp = await fetch('/api/book-showing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...showingForm, lot_code: lot.code })
      })
      const data = await resp.json()
      if (data.ok) {
        setShowingSent(true)
      } else {
        setShowingError('Ошибка отправки. Попробуйте ещё раз.')
      }
    } catch (e) {
      console.error(e)
      setShowingError('Ошибка соединения. Попробуйте ещё раз.')
    }
  }

  // === KP Download ===
  const handleKPDownload = (type) => {
    setKpLoading(true)
    const url = `/api/download-kp/${encodeURIComponent(lot.code)}?type=${type}&building=${lot.building}`

    window.open(url, '_blank')
    setTimeout(() => {
      setKpLoading(false)
      setShowKP(false)
    }, 1000)
  }

  // === Excel Download ===
  const handleExcelDownload = () => {
    const url = `/api/download-xlsx/${encodeURIComponent(lot.code)}?building=${lot.building}`
    window.open(url, '_blank')
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

  // === MGP ===
  const handleMGP = async () => {
    setShowMGP(true)
    setMgpLoading(true)
    try {
      const res = await fetch(`/api/mgp/calculate?area=${lot.area}`)
      const data = await res.json()
      if (data.ok) setMgpData(data)
    } catch (e) {
      console.error(e)
    }
    setMgpLoading(false)
  }

  const handleMGPDownload = () => {
    const url = `/api/mgp/pdf?code=${encodeURIComponent(lot.code)}&area=${lot.area}&building=${lot.building}`
    window.open(url, '_blank')
  }

  // === Mortgage ===
  const handleMortgageCalc = async (dp = mortgageDP, tariff = mortgageTariff, term = mortgageTerm) => {
    setMortgageLoading(true)
    try {
      const res = await fetch('/api/mortgage/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          price: lot.price,
          down_payment_pct: dp,
          tariff: tariff,
          loan_term_months: term,
        })
      })
      const data = await res.json()
      if (data.ok) setMortgageData(data.data)
    } catch (e) {
      console.error(e)
    }
    setMortgageLoading(false)
  }

  // === Tranche Mortgage ===
  const handleTrancheMortgage = async () => {
    setShowTrancheMortgage(true)
    setTrancheMortgageLoading(true)
    try {
      const res = await fetch('/api/tranche-mortgage/all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price: lot.price })
      })
      const data = await res.json()
      if (data.ok) setTrancheMortgageData(data.data)
    } catch (e) {
      console.error(e)
    }
    setTrancheMortgageLoading(false)
  }

  // === Summary ===
  const handleSummary = async () => {
    setShowSummary(true)
    setSummaryLoading(true)
    setSummaryData(null)
    try {
      const [roiRes, installmentRes, depositRes, mgpRes, mortgageRes] = await Promise.all([
        fetch('/api/calculate-roi', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ area: lot.area, price: lot.price })
        }).then(r => r.json()),
        fetch('/api/installment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ price: lot.price })
        }).then(r => r.json()),
        fetch('/api/compare-deposit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount: lot.price, years: 11, scenario: 'all' })
        }).then(r => r.json()),
        fetch(`/api/mgp/calculate?area=${lot.area}`).then(r => r.json()),
        fetch('/api/mortgage/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ price: lot.price, down_payment_pct: 30, tariff: 'base', loan_term_months: 360 })
        }).then(r => r.json()),
      ])
      setSummaryData({
        roi: roiRes.ok ? roiRes.data : null,
        installment: installmentRes.ok ? installmentRes.data : null,
        deposit: depositRes.ok ? depositRes.data : null,
        mgp: mgpRes.ok ? mgpRes : null,
        mortgage: mortgageRes.ok ? mortgageRes.data : null,
      })
    } catch (e) {
      console.error('Summary load error:', e)
      setSummaryData({ error: true })
    }
    setSummaryLoading(false)
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
            <p className="font-bold text-lg">{lot.building} ({{1: 'Family', 2: 'Business', 3: 'Digital'}[lot.building] || lot.buildingName})</p>
          </div>
          <div className="bg-rz-green-light rounded-xl p-3">
            <p className="text-rz-cream-dark text-xs">Цена за м²</p>
            <p className="font-bold text-lg">{formatPrice(pricePerM2)} ₽</p>
          </div>
        </div>

        {/* Actions — 2-col grid of 3D cards */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <button onClick={() => setShowKP(true)} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-gold-light to-rz-gold text-rz-green-dark font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.15)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">📄</span>
            <span className="text-xs leading-tight text-center">Получить КП</span>
          </button>
          <button onClick={handleSummary} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">📈</span>
            <span className="text-xs leading-tight text-center">Инвест. сводка</span>
          </button>
          <button onClick={handleInstallment} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">💳</span>
            <span className="text-xs leading-tight text-center">Рассрочка</span>
          </button>
          <button onClick={handleROI} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">🧮</span>
            <span className="text-xs leading-tight text-center">ROI калькулятор</span>
          </button>
          <button onClick={handleDeposit} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">💰</span>
            <span className="text-xs leading-tight text-center">Сравнить с депозитом</span>
          </button>
          <button onClick={handleMGP} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">🎯</span>
            <span className="text-xs leading-tight text-center">Расчёт МГП</span>
          </button>
          <button onClick={() => setShowMortgage(true)} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">🏠</span>
            <span className="text-xs leading-tight text-center">Ипотека Совкомбанк</span>
          </button>
          <button onClick={handleTrancheMortgage} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">🏗</span>
            <span className="text-xs leading-tight text-center">Транш. ипотека Сбербанк</span>
          </button>
          <button onClick={() => setShowShowing(true)} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">📅</span>
            <span className="text-xs leading-tight text-center">Записаться на показ</span>
          </button>
          <button onClick={onChat} className="flex flex-col items-center justify-center gap-1.5 py-4 px-2 rounded-xl bg-gradient-to-b from-rz-green-light to-rz-green-mid text-rz-cream font-semibold shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_1px_0_rgba(255,255,255,0.08)] hover:shadow-[0_1px_2px_rgba(0,0,0,0.3)] hover:translate-y-0.5 active:translate-y-1 active:shadow-none transition-all duration-150">
            <span className="text-2xl">💬</span>
            <span className="text-xs leading-tight text-center">Чат с AI</span>
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
                  <button
                    onClick={() => window.open(`/api/payment-pdf?price=${lot.price}&code=${encodeURIComponent(lot.code)}`, '_blank')}
                    className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors"
                  >
                    📄 Скачать PDF
                  </button>
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
            <div className="p-4 pb-24">
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
            <div className="p-4 pb-24">
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

                  {/* Compare PDF download */}
                  <button onClick={() => window.open(`/api/download-compare-pdf?amount=${lot.price}&years=11&area=${lot.area}`, "_blank")} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
                    📄 Скачать PDF сравнение
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
              <button onClick={() => {setShowShowing(false); setShowingSent(false); setShowingError('')}} className="text-rz-cream-dark text-xl">✕</button>
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
                  {showingError && (
                    <p className="text-rz-error text-sm text-center">{showingError}</p>
                  )}
                  <button type="submit" className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
                    Отправить заявку
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mortgage Modal */}
      {showMortgage && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[90vh] overflow-auto pb-24">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center sticky top-0 bg-rz-green-light z-10">
              <h2 className="font-bold text-lg">🏦 Ипотека Совкомбанк</h2>
              <button onClick={() => { setShowMortgage(false); setMortgageData(null) }} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-rz-cream-dark text-xs">Акция «Сниженный платёж»</p>

              {/* Down payment selector */}
              <div>
                <p className="text-xs text-rz-cream-muted mb-1">Первоначальный взнос</p>
                <div className="flex gap-2">
                  {[30, 40, 50].map(dp => (
                    <button key={dp} onClick={() => { setMortgageDP(dp); handleMortgageCalc(dp, mortgageTariff, mortgageTerm) }}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        mortgageDP === dp ? 'bg-rz-gold text-rz-green-dark' : 'bg-rz-green-mid text-rz-cream'
                      }`}>
                      {dp}%
                    </button>
                  ))}
                </div>
              </div>

              {/* Tariff selector */}
              <div>
                <p className="text-xs text-rz-cream-muted mb-1">Тариф</p>
                <div className="flex gap-2">
                  {[['base', 'Базовый'], ['profitable', 'Выгодный']].map(([key, label]) => (
                    <button key={key} onClick={() => { setMortgageTariff(key); handleMortgageCalc(mortgageDP, key, mortgageTerm) }}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        mortgageTariff === key ? 'bg-rz-gold text-rz-green-dark' : 'bg-rz-green-mid text-rz-cream'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Term selector */}
              <div>
                <p className="text-xs text-rz-cream-muted mb-1">Срок кредита</p>
                <div className="flex gap-2">
                  {[[240, '20 лет'], [360, '30 лет']].map(([months, label]) => (
                    <button key={months} onClick={() => { setMortgageTerm(months); handleMortgageCalc(mortgageDP, mortgageTariff, months) }}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        mortgageTerm === months ? 'bg-rz-gold text-rz-green-dark' : 'bg-rz-green-mid text-rz-cream'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Calculate button */}
              {!mortgageData && !mortgageLoading && (
                <button onClick={() => handleMortgageCalc()} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl">
                  Рассчитать
                </button>
              )}

              {mortgageLoading && (
                <div className="flex justify-center py-4">
                  <div className="w-6 h-6 border-3 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              )}

              {/* Results */}
              {mortgageData && (
                <div className="space-y-3 bg-rz-green-mid rounded-xl p-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-rz-cream-dark">Первонач. взнос</span>
                    <span className="font-bold">{formatPrice(mortgageData.down_payment)} ₽</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-rz-cream-dark">Удорожание ({mortgageData.markup_pct}%)</span>
                    <span>{formatPrice(mortgageData.markup)} ₽</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-rz-cream-dark">Сумма кредита</span>
                    <span className="font-bold">{formatPrice(mortgageData.loan_amount)} ₽</span>
                  </div>
                  <div className="border-t border-rz-green-mid pt-2">
                    <p className="text-xs text-rz-cream-muted mb-1">Льготный период ({mortgageData.grace_months} мес)</p>
                    <div className="flex justify-between text-sm">
                      <span className="text-rz-cream-dark">Платёж</span>
                      <span className="font-bold text-rz-gold">{formatPrice(mortgageData.grace_payment)} ₽/мес</span>
                    </div>
                    <p className="text-xs text-rz-cream-muted">комиссия аккредитива {mortgageData.accreditive_pct}%</p>
                  </div>
                  <div className="border-t border-rz-green-mid pt-2">
                    <p className="text-xs text-rz-cream-muted mb-1">После льготного ({mortgageData.remaining_months} мес)</p>
                    <div className="flex justify-between text-sm">
                      <span className="text-rz-cream-dark">Платёж</span>
                      <span className="font-bold">{formatPrice(mortgageData.regular_payment)} ₽/мес</span>
                    </div>
                    <p className="text-xs text-rz-cream-muted">ставка {mortgageData.rate_after_grace}% годовых</p>
                  </div>
                  <p className="text-xs text-rz-cream-muted text-center pt-2 border-t border-rz-green-mid">
                    Расчёт предварительный. Точные условия уточняйте в банке.
                  </p>
                  <button
                    onClick={() => window.open(`/api/mortgage/pdf?price=${lot.price}&down_payment_pct=${mortgageDP}&tariff=${mortgageTariff}&loan_term_months=${mortgageTerm}`, '_blank')}
                    className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors mt-3"
                  >
                    📄 Скачать PDF
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MGP Modal */}
      {showMGP && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[90vh] overflow-auto pb-24">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center sticky top-0 bg-rz-green-light z-10">
              <h2 className="font-bold text-lg">📊 Расчёт МГП</h2>
              <button onClick={() => { setShowMGP(false); setMgpData(null) }} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-rz-cream-dark text-xs">Минимальный гарантированный платёж • {lot.code} • {lot.area} м²</p>

              {mgpLoading && (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              )}

              {mgpData && (
                <div className="space-y-3">
                  <div className="overflow-x-auto rounded-xl border border-rz-green-mid">
                    <table className="w-full text-xs min-w-[320px]">
                      <thead>
                        <tr className="bg-rz-green-mid text-rz-cream-dark">
                          <th className="py-2 px-2 text-left font-medium">Год</th>
                          <th className="py-2 px-2 text-right font-medium">Номерной, ₽</th>
                          <th className="py-2 px-2 text-right font-medium">Коммерч., ₽</th>
                        </tr>
                      </thead>
                      <tbody>
                        {mgpData.years.map((yr, i) => (
                          <tr key={yr.year} className={i % 2 === 0 ? 'bg-rz-green-light' : 'bg-rz-green-mid/50'}>
                            <td className="py-1.5 px-2 font-medium">{yr.year}</td>
                            <td className="py-1.5 px-2 text-right text-rz-gold">{formatPrice(yr.nominal)} ₽</td>
                            <td className="py-1.5 px-2 text-right text-rz-cream-dark">{formatPrice(yr.commercial)} ₽</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="bg-rz-green-mid font-bold">
                          <td className="py-2 px-2">Итого</td>
                          <td className="py-2 px-2 text-right text-rz-gold">{formatPrice(mgpData.total_nominal)} ₽</td>
                          <td className="py-2 px-2 text-right text-rz-cream-dark">{formatPrice(mgpData.total_commercial)} ₽</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>

                  <button onClick={handleMGPDownload} className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors">
                    📄 Скачать PDF
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tranche Mortgage Modal */}
      {showTrancheMortgage && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[90vh] overflow-auto pb-24">
            <div className="px-4 py-3 border-b border-rz-green-mid flex justify-between items-center sticky top-0 bg-rz-green-light z-10">
              <h2 className="font-bold text-lg">🏗 Траншевая ипотека</h2>
              <button onClick={() => { setShowTrancheMortgage(false); setTrancheMortgageData(null) }} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-rz-cream-dark text-xs">3 транша • 20 лет • Сервисный сбор 150 000 ₽</p>

              {trancheMortgageLoading && (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              )}

              {trancheMortgageData && trancheMortgageData.length > 0 && (
                <div className="space-y-3">
                  {trancheMortgageData.map((sc) => (
                    <div key={sc.down_payment_pct} className="bg-rz-green-mid rounded-xl p-4 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-rz-gold">ПВ {sc.down_payment_pct}%</span>
                        <span className="text-sm text-rz-cream-dark">Ставка {sc.rate}%</span>
                      </div>
                      <div className="space-y-1.5 text-sm">
                        <div className="flex justify-between">
                          <span className="text-rz-cream-dark">Первоначальный взнос</span>
                          <span className="font-bold">{formatPrice(sc.down_payment)} ₽</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-rz-cream-dark">Сумма ипотеки</span>
                          <span className="font-bold">{formatPrice(sc.mortgage_total)} ₽</span>
                        </div>
                      </div>
                      <div className="border-t border-rz-green-light pt-2">
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="bg-rz-green/50 rounded-lg p-2">
                            <p className="text-[10px] text-rz-cream-muted">1 транш</p>
                            <p className="text-xs text-rz-cream-dark">({sc.tranche_period} мес.)</p>
                            <p className="text-sm font-bold text-rz-gold mt-1">{formatPrice(sc.ep_1)} ₽</p>
                          </div>
                          <div className="bg-rz-green/50 rounded-lg p-2">
                            <p className="text-[10px] text-rz-cream-muted">2 транш</p>
                            <p className="text-xs text-rz-cream-dark">({sc.tranche_period} мес.)</p>
                            <p className="text-sm font-bold text-rz-gold mt-1">{formatPrice(sc.ep_2)} ₽</p>
                          </div>
                          <div className="bg-rz-green/50 rounded-lg p-2">
                            <p className="text-[10px] text-rz-cream-muted">3 транш</p>
                            <p className="text-xs text-rz-cream-dark">({sc.term_months - 2 * sc.tranche_period} мес.)</p>
                            <p className="text-sm font-bold text-rz-gold mt-1">{formatPrice(sc.ep_3)} ₽</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => window.open(`/api/tranche-mortgage/pdf?code=${encodeURIComponent(lot.code)}&building=${lot.building}`, '_blank')}
                    className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors"
                  >
                    📄 Скачать PDF
                  </button>
                  <p className="text-xs text-rz-cream-muted text-center pt-2">
                    Расчёт предварительный. Точные условия уточняйте в банке.
                  </p>
                </div>
              )}

              {trancheMortgageData && trancheMortgageData.length === 0 && (
                <p className="text-rz-error text-center">Нет доступных сценариев для данной цены</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Summary Modal */}
      {showSummary && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end sm:items-center justify-center">
          <div className="bg-rz-green-light w-full sm:max-w-md sm:rounded-xl rounded-t-xl max-h-[90vh] overflow-auto pb-24">
            <div className="sticky top-0 bg-rz-green-light px-4 py-3 border-b border-rz-green-mid flex justify-between items-center z-10">
              <h2 className="font-bold text-lg">📊 Инвестиционная сводка</h2>
              <button onClick={() => setShowSummary(false)} className="text-rz-cream-dark text-xl">✕</button>
            </div>
            <div className="p-4 space-y-4">
              {summaryLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-4 border-rz-gold border-t-transparent rounded-full animate-spin"/>
                </div>
              ) : summaryData?.error ? (
                <p className="text-rz-error text-center">Ошибка загрузки данных</p>
              ) : summaryData ? (
                <>
                  {/* 1. Header */}
                  <div className="bg-rz-green-mid rounded-xl p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-xl text-rz-gold">{lot.code}</p>
                        <p className="text-sm text-rz-cream-dark">
                          Корпус {lot.building} «{{1:'Family',2:'Business',3:'Digital'}[lot.building] || ''}» • {lot.area} м² • этаж {lot.floor}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-xl">{formatPrice(lot.price)} ₽</p>
                        <p className="text-xs text-rz-cream-muted">{formatPrice(pricePerM2)} ₽/м²</p>
                      </div>
                    </div>
                  </div>

                  {/* 2. Profitability 11 years */}
                  {summaryData.roi && (() => {
                    const r = summaryData.roi
                    return (
                      <div className="bg-rz-success/15 rounded-xl p-4">
                        <div className="flex justify-between items-center mb-2">
                          <p className="text-sm text-rz-success font-medium">Доходность за 11 лет</p>
                          <p className="text-2xl font-bold text-rz-success">{r.roi_pct}%</p>
                        </div>
                        <p className="text-xs text-rz-cream-dark">~{r.avg_annual_pct}% годовых</p>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <div className="bg-rz-green-mid/50 rounded-lg p-2">
                            <p className="text-xs text-rz-cream-muted">Аренда</p>
                            <p className="text-sm font-bold text-rz-gold">{formatPrice(r.total_rental)} ₽</p>
                          </div>
                          <div className="bg-rz-green-mid/50 rounded-lg p-2">
                            <p className="text-xs text-rz-cream-muted">Рост стоимости</p>
                            <p className="text-sm font-bold text-rz-gold">{formatPrice(r.total_growth)} ₽</p>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-rz-success/20 flex justify-between">
                          <div>
                            <p className="text-xs text-rz-cream-muted">Общая прибыль</p>
                            <p className="font-bold text-rz-gold">{formatPrice(r.total_profit)} ₽</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-rz-cream-muted">Стоимость в 2035</p>
                            <p className="font-bold">{formatPrice(r.final_value)} ₽</p>
                          </div>
                        </div>
                      </div>
                    )
                  })()}

                  {/* 4. Payment options */}
                  {summaryData.installment && (() => {
                    const d = summaryData.installment
                    return (
                      <div>
                        <p className="text-xs text-rz-cream-muted font-medium mb-2">ВАРИАНТЫ ОПЛАТЫ</p>
                        <div className="space-y-3">
                          <div className="bg-rz-success/15 rounded-xl p-3">
                            <p className="text-sm font-bold text-rz-success mb-1">💰 100% оплата (скидка 5%)</p>
                            <p className="text-lg font-bold">{formatPrice(Math.round(lot.price * 0.95))} ₽</p>
                            <p className="text-xs text-rz-cream-muted">Экономия: {formatPrice(Math.round(lot.price * 0.05))} ₽</p>
                          </div>
                          <div className="border border-rz-success/30 rounded-xl p-3">
                            <p className="text-sm font-bold text-rz-success mb-2">12 месяцев (0%)</p>
                            <div className="space-y-1.5 text-sm">
                              <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 30%</span><span>{formatPrice(d.i12.pv_30)} ₽ → {formatPrice(d.i12.monthly_30)} ₽/мес</span></div>
                              <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 40%</span><span>{formatPrice(d.i12.pv_40)} ₽ → 11×200К + {formatPrice(d.i12.last_40)} ₽</span></div>
                              <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 50%</span><span>{formatPrice(d.i12.pv_50)} ₽ → 11×100К + {formatPrice(d.i12.last_50)} ₽</span></div>
                            </div>
                          </div>
                          <div className="border border-rz-gold/30 rounded-xl p-3">
                            <p className="text-sm font-bold text-rz-gold mb-2">18 месяцев</p>
                            <div className="space-y-2 text-sm">
                              <div>
                                <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 30% (+9%)</span><span>{formatPrice(d.i18.pv_30)} ₽</span></div>
                                <p className="text-rz-cream-muted text-xs">18 × {formatPrice(d.i18.monthly_30)} ₽ → Итого: {formatPrice(d.i18.final_price_30)} ₽</p>
                              </div>
                              <div>
                                <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 40% (+7%)</span><span>{formatPrice(d.i18.pv_40)} ₽</span></div>
                                <p className="text-rz-cream-muted text-xs">8×250К, 9-й: {formatPrice(d.i18.payment_9)} ₽, 8×250К, 18-й: {formatPrice(d.i18.last_40)} ₽</p>
                              </div>
                              <div>
                                <div className="flex justify-between"><span className="text-rz-cream-dark">ПВ 50% (+4%)</span><span>{formatPrice(d.i18.pv_50)} ₽</span></div>
                                <p className="text-rz-cream-muted text-xs">8×150К, 9-й: {formatPrice(d.i18.payment_9)} ₽, 8×150К, 18-й: {formatPrice(d.i18.last_50)} ₽</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })()}

                  {/* 5. Deposit comparison */}
                  {summaryData.deposit && (() => {
                    const dep = summaryData.deposit
                    const r = summaryData.roi
                    const advantage = r ? r.total_profit - (dep.base?.total_net_interest || 0) : 0
                    const DEPOSIT_LABELS = {
                      pessimistic: 'Ставка остаётся высокой',
                      base: 'Базовый (прогноз ЦБ)',
                      optimistic: 'Ставка снижается быстро',
                    }
                    const DEPOSIT_ORDER = ['pessimistic', 'base', 'optimistic']
                    return (
                      <div>
                        <p className="text-xs text-rz-cream-muted font-medium mb-2">RIZALTA vs ДЕПОЗИТ (11 лет)</p>
                        {r && dep.base && advantage > 0 && (
                          <div className="bg-rz-gold/20 rounded-xl p-4 border-2 border-rz-gold/50 mb-3">
                            <p className="text-xl font-bold text-rz-gold">
                              ✅ RIZALTA выгоднее на {formatPrice(advantage)} ₽
                            </p>
                            <p className="text-rz-cream-dark text-sm mt-1">по сравнению с базовым прогнозом ЦБ</p>
                          </div>
                        )}
                        {r && (
                          <div className="bg-rz-success/15 rounded-xl p-3 mb-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-rz-success">🏠 RIZALTA</span>
                              <span className="font-bold text-rz-success text-lg">{formatPrice(r.total_profit)} ₽</span>
                            </div>
                            <p className="text-xs text-rz-cream-dark">ROI: {r.roi_pct}% за 11 лет</p>
                          </div>
                        )}
                        <p className="text-xs text-rz-cream-muted font-medium mb-1 mt-3">Доходность по депозиту за 11 лет:</p>
                        <div className="space-y-2">
                          {DEPOSIT_ORDER.filter(k => dep[k]).map(key => {
                            const d = dep[key]
                            return (
                              <div key={key} className="bg-rz-green-mid rounded-xl p-3">
                                <div className="flex justify-between items-center">
                                  <span className="text-sm text-rz-cream-dark">{DEPOSIT_LABELS[key] || d.scenario_name}</span>
                                  <span className="font-bold">{formatPrice(d.total_net_interest)} ₽</span>
                                </div>
                                <p className="text-xs text-rz-cream-muted">ROI: {d.total_roi_pct}%</p>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {/* 6. MGP */}
                  {summaryData.mgp && summaryData.mgp.years && (
                    <div>
                      <p className="text-xs text-rz-cream-muted font-medium mb-2">МИНИМАЛЬНЫЙ ГАРАНТИРОВАННЫЙ ПЛАТЁЖ</p>
                      <div className="overflow-x-auto rounded-xl border border-rz-green-mid">
                        <table className="w-full text-xs min-w-[320px]">
                          <thead>
                            <tr className="bg-rz-green-mid text-rz-cream-dark">
                              <th className="py-2 px-2 text-left font-medium">Год</th>
                              <th className="py-2 px-2 text-right font-medium">Номерной, ₽</th>
                              <th className="py-2 px-2 text-right font-medium">Коммерч., ₽</th>
                            </tr>
                          </thead>
                          <tbody>
                            {summaryData.mgp.years.map((yr, i) => (
                              <tr key={yr.year} className={i % 2 === 0 ? 'bg-rz-green-light' : 'bg-rz-green-mid/50'}>
                                <td className="py-1.5 px-2 font-medium">{yr.year}</td>
                                <td className="py-1.5 px-2 text-right text-rz-gold">{formatPrice(yr.nominal)} ₽</td>
                                <td className="py-1.5 px-2 text-right text-rz-cream-dark">{formatPrice(yr.commercial)} ₽</td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot>
                            <tr className="bg-rz-green-mid font-bold">
                              <td className="py-2 px-2">Итого</td>
                              <td className="py-2 px-2 text-right text-rz-gold">{formatPrice(summaryData.mgp.total_nominal)} ₽</td>
                              <td className="py-2 px-2 text-right text-rz-cream-dark">{formatPrice(summaryData.mgp.total_commercial)} ₽</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* 7. Mortgage */}
                  {summaryData.mortgage && (
                    <div>
                      <p className="text-xs text-rz-cream-muted font-medium mb-2">ИПОТЕКА (Совкомбанк)</p>
                      <div className="bg-rz-green-mid rounded-xl p-4 space-y-2">
                        <p className="text-xs text-rz-cream-muted">Базовый тариф • ПВ 30% • 30 лет</p>
                        <div className="flex justify-between text-sm">
                          <span className="text-rz-cream-dark">Первонач. взнос</span>
                          <span className="font-bold">{formatPrice(summaryData.mortgage.down_payment)} ₽</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-rz-cream-dark">Сумма кредита</span>
                          <span className="font-bold">{formatPrice(summaryData.mortgage.loan_amount)} ₽</span>
                        </div>
                        <div className="border-t border-rz-green-light pt-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-rz-cream-dark">Платёж (льготный)</span>
                            <span className="font-bold text-rz-gold">{formatPrice(summaryData.mortgage.grace_payment)} ₽/мес</span>
                          </div>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-rz-cream-dark">Платёж (после)</span>
                          <span className="font-bold">{formatPrice(summaryData.mortgage.regular_payment)} ₽/мес</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-rz-cream-dark">Ставка</span>
                          <span>{summaryData.mortgage.rate_after_grace}% годовых</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* PDF buttons */}
                  <div className="space-y-2 pt-2">
                    <button
                      onClick={async () => {
                        try {
                          const resp = await fetch('/api/lot-summary-pdf', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              lot: { code: lot.code, building: lot.building, area: lot.area, floor: lot.floor, price: lot.price },
                              roi: summaryData.roi,
                              installment: summaryData.installment,
                              deposit: summaryData.deposit,
                              mgp: summaryData.mgp,
                              mortgage: summaryData.mortgage,
                            }),
                          })
                          if (!resp.ok) throw new Error('PDF failed')
                          const blob = await resp.blob()
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `RIZALTA_${lot.code}_Summary.pdf`
                          a.click()
                          URL.revokeObjectURL(url)
                        } catch (e) { console.error('Summary PDF error:', e) }
                      }}
                      className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors"
                    >
                      📄 Скачать полный отчёт
                    </button>
                    <button onClick={() => window.open(`/api/payment-pdf?price=${lot.price}&code=${encodeURIComponent(lot.code)}`, '_blank')}
                      className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green transition-colors">
                      📄 PDF вариантов оплаты
                    </button>
                    <button onClick={() => window.open(`/api/download-compare-pdf?amount=${lot.price}&years=11&area=${lot.area}`, '_blank')}
                      className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green transition-colors">
                      📄 PDF сравнение с депозитом
                    </button>
                    <button onClick={() => window.open(`/api/mgp/pdf?code=${encodeURIComponent(lot.code)}&area=${lot.area}&building=${lot.building}`, '_blank')}
                      className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green transition-colors">
                      📄 PDF расчёт МГП
                    </button>
                    <button onClick={() => window.open(`/api/mortgage/pdf?price=${lot.price}&down_payment_pct=30&tariff=base&loan_term_months=360`, '_blank')}
                      className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green transition-colors">
                      📄 PDF ипотека
                    </button>
                    <button onClick={() => window.open(`/api/download-xlsx/${encodeURIComponent(lot.code)}?building=${lot.building}`, '_blank')}
                      className="w-full bg-rz-green-mid text-rz-cream py-3 rounded-xl hover:bg-rz-green transition-colors">
                      📥 Скачать Excel
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
