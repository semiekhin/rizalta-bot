import React, { useState, useRef, useEffect, useCallback } from 'react'

const WELCOME_MSG = {
  role: 'assistant',
  content: 'Здравствуйте! Я AI-консультант RIZALTA. Помогу подобрать апартамент, рассчитать доходность или ответить на вопросы об инвестициях. Что вас интересует?'
}

// Map navigate "to" paths to internal screen names
function resolveNavigation(to, onNavigate) {
  // Parse path like /catalog/А209?modal=roi or /lots or /booking
  const [path, query] = to.split('?')
  const segments = path.split('/').filter(Boolean)

  const screen = segments[0]
  const screenMap = {
    lots: 'lots',
    catalog: 'lots',
    booking: 'booking',
    presentations: 'presentations',
    documents: 'documents',
    media: 'media',
    news: 'news',
    secretary: 'secretary',
    fixation: 'fixation',
  }

  const targetScreen = screenMap[screen]
  if (targetScreen) {
    onNavigate(targetScreen)
  }
}

const fmt = (v) => new Intl.NumberFormat('ru-RU').format(Math.round(v || 0))
const BNAMES = { 1: 'Family', 2: 'Business', 3: 'Digital' }

function renderText(text) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*)/)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
    }
    return part
  })
}

function MetricCell({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-lg p-2 ${highlight ? 'bg-rz-gold/15' : 'bg-rz-green-mid/50'}`}>
      <p className="text-[10px] uppercase tracking-wide text-rz-cream-muted">{label}</p>
      <p className={`text-sm font-bold ${highlight ? 'text-rz-gold' : 'text-rz-cream'}`}>{value}</p>
      {sub && <p className="text-[10px] text-rz-cream-muted">{sub}</p>}
    </div>
  )
}

function LotReportCard({ data }) {
  const lot = data.lot || {}
  const roi = data.roi || {}
  const metrics = data.metrics || {}
  const inst = data.installment || {}
  const dep = data.deposit_comparison || {}
  const bname = BNAMES[lot.building_num] || ''
  const depBase = dep.base || {}
  const totalProfit = roi.total_profit_rub || 0
  const depInterest = depBase.total_net_interest || 0
  const advantage = totalProfit - depInterest
  const i12 = inst.installment_12m || {}
  const i18 = inst.installment_18m || {}

  return (
    <div className="space-y-3">
      <div className="bg-rz-green-mid rounded-xl p-3">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-bold text-lg text-rz-gold">{lot.code}</p>
            <p className="text-sm text-rz-cream-dark">
              Корпус {lot.building_num} {bname && `\u00AB${bname}\u00BB`} &bull; {lot.area_m2} м&sup2; &bull; этаж {lot.floor}
            </p>
          </div>
          <div className="text-right">
            <p className="font-bold text-lg">{fmt(lot.price_rub)} &#8381;</p>
            <p className="text-xs text-rz-cream-muted">ПВ 30%: {fmt(lot.price_rub * 0.3)} &#8381;</p>
          </div>
        </div>
      </div>

      {metrics.noi != null && (
        <div className="grid grid-cols-3 gap-2">
          <MetricCell label="Чистый доход / год" value={`${fmt(metrics.noi)} \u20BD`} sub="стабилиз. 2030" highlight />
          <MetricCell label="Доходность (Cap Rate)" value={`${metrics.cap_rate}%`} sub="NOI / цена" highlight />
          <MetricCell label="ROI 11 лет" value={`${metrics.roi_pct}%`} sub={`~${metrics.avg_annual_pct}% / год`} />
          <MetricCell label="Доход на вложенное (100%)" value={`${metrics.coc_full}%`} sub="скидка 5%" />
          <MetricCell label="Доход на вложенное (30%)" value={`${metrics.coc_installment}%`} sub="рассрочка" />
          <MetricCell label="Мультипликатор капитала" value={`${metrics.equity_multiple_full}x`} sub={`рассрочка ${metrics.equity_multiple_installment}x`} />
        </div>
      )}

      <div className="bg-rz-success/15 rounded-xl p-3">
        <div className="flex justify-between items-center mb-2">
          <p className="text-sm text-rz-success font-medium">Доходность за 11 лет</p>
          <p className="text-2xl font-bold text-rz-success">{(roi.roi_pct || 0).toFixed(0)}%</p>
        </div>
        <p className="text-xs text-rz-cream-dark">~{(roi.avg_annual_pct || 0).toFixed(1)}% годовых</p>
        <div className="grid grid-cols-2 gap-2 mt-2">
          <div className="bg-rz-green-mid/50 rounded-lg p-2">
            <p className="text-xs text-rz-cream-muted">Аренда</p>
            <p className="text-sm font-bold text-rz-gold">{fmt(roi.total_rental_income)} &#8381;</p>
          </div>
          <div className="bg-rz-green-mid/50 rounded-lg p-2">
            <p className="text-xs text-rz-cream-muted">Рост стоимости</p>
            <p className="text-sm font-bold text-rz-gold">{fmt(roi.total_growth)} &#8381;</p>
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-rz-success/20 flex justify-between">
          <div>
            <p className="text-xs text-rz-cream-muted">Общая прибыль</p>
            <p className="font-bold text-rz-gold">{fmt(totalProfit)} &#8381;</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-rz-cream-muted">Стоимость в 2035</p>
            <p className="font-bold">{fmt(roi.final_value_rub)} &#8381;</p>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-rz-cream-muted font-medium">Варианты оплаты</p>
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-rz-green-mid rounded-lg p-2">
            <p className="text-xs text-rz-success font-medium">100%</p>
            <p className="text-sm font-bold">{fmt(lot.price_rub * 0.95)} &#8381;</p>
            <p className="text-xs text-rz-cream-muted">скидка 5%</p>
          </div>
          <div className="bg-rz-green-mid rounded-lg p-2">
            <p className="text-xs text-rz-gold font-medium">12 мес</p>
            <p className="text-sm font-bold">{fmt(i12.monthly_30)} &#8381;/мес</p>
            <p className="text-xs text-rz-cream-muted">ПВ {fmt(i12.pv_30)} &#8381;</p>
          </div>
          <div className="bg-rz-green-mid rounded-lg p-2">
            <p className="text-xs text-rz-gold font-medium">18 мес</p>
            <p className="text-sm font-bold">{fmt(i18.monthly_30)} &#8381;/мес</p>
            <p className="text-xs text-rz-cream-muted">ПВ {fmt(i18.pv_30)} &#8381;</p>
          </div>
        </div>
      </div>

      {depBase.total_net_interest != null && (
        <div className="bg-rz-gold/10 rounded-xl p-3 border border-rz-gold/20">
          <p className="text-xs text-rz-cream-muted font-medium mb-2">RIZALTA vs Депозит (11 лет)</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-rz-success">RIZALTA</p>
              <p className="font-bold text-rz-success">{fmt(totalProfit)} &#8381;</p>
              <p className="text-xs text-rz-cream-muted">ROI {(roi.roi_pct || 0).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-xs text-rz-cream-dark">Депозит</p>
              <p className="font-bold">{fmt(depInterest)} &#8381;</p>
              <p className="text-xs text-rz-cream-muted">ROI {(depBase.total_roi_pct || 0).toFixed(0)}%</p>
            </div>
          </div>
          {advantage > 0 && (
            <p className="text-sm font-bold text-rz-gold mt-2 pt-2 border-t border-rz-gold/20">
              RIZALTA выгоднее на {fmt(advantage)} &#8381;
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function PortfolioReportCard({ data }) {
  const budget = data.budget || 0
  const sa = data.strategy_a || {}
  const sb = data.strategy_b || {}
  const roiMap = data.roi || {}
  const metricsMap = data.metrics || {}
  const dep = data.deposit_comparison || {}
  const depBase = dep.base || {}
  const lotsA = sa.lots?.lots || []
  const lotsB = sb.lots?.lots || []

  const LotRow = ({ lot, strategy }) => {
    const r = roiMap[lot.code] || {}
    const m = metricsMap[lot.code] || {}
    return (
      <div className="bg-rz-green-mid/50 rounded-lg p-2 text-sm">
        <div className="flex justify-between items-center">
          <div>
            <span className="font-medium">{lot.code}</span>
            <span className="text-rz-cream-muted text-xs ml-2">{lot.area_m2} м&sup2;</span>
          </div>
          <span className="text-rz-gold font-medium">{fmt(lot.price_rub)} &#8381;</span>
        </div>
        <div className="flex gap-3 mt-1 text-xs text-rz-cream-dark">
          {r.roi_pct != null && <span className="text-rz-success">ROI {r.roi_pct.toFixed(0)}%</span>}
          {m.cap_rate != null && <span>Cap {m.cap_rate}%</span>}
          {strategy === 'a' && m.coc_full != null && <span>CoC {m.coc_full}%</span>}
          {strategy === 'b' && m.coc_installment != null && <span>CoC {m.coc_installment}%</span>}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="bg-rz-green-mid rounded-xl p-3">
        <p className="text-xs text-rz-cream-muted">Портфельный анализ</p>
        <p className="font-bold text-lg text-rz-gold">{fmt(budget)} &#8381;</p>
      </div>

      <div className="border border-rz-success/30 rounded-xl p-3">
        <p className="text-sm font-bold text-rz-success mb-2">{sa.name || 'Стратегия A'}</p>
        {lotsA.length > 0 ? (
          <div className="space-y-1.5">
            {lotsA.slice(0, 3).map(lot => <LotRow key={lot.code} lot={lot} strategy="a" />)}
          </div>
        ) : (
          <p className="text-rz-cream-muted text-sm">Нет подходящих лотов</p>
        )}
      </div>

      <div className="border border-rz-gold/30 rounded-xl p-3">
        <p className="text-sm font-bold text-rz-gold mb-1">{sb.name || 'Стратегия B'}</p>
        <p className="text-xs text-rz-cream-muted mb-2">Макс. цена лота: {fmt(sb.max_lot_price)} &#8381;</p>
        {lotsB.length > 0 ? (
          <div className="space-y-1.5">
            {lotsB.slice(0, 3).map(lot => <LotRow key={lot.code} lot={lot} strategy="b" />)}
          </div>
        ) : (
          <p className="text-rz-cream-muted text-sm">Нет подходящих лотов</p>
        )}
      </div>

      {depBase.total_net_interest != null && (
        <div className="bg-rz-gold/10 rounded-xl p-3 border border-rz-gold/20">
          <p className="text-xs text-rz-cream-muted font-medium mb-1">Депозит для сравнения (11 лет)</p>
          <p className="font-bold">{fmt(depBase.final_balance)} &#8381;</p>
          <p className="text-xs text-rz-cream-dark">Проценты: {fmt(depBase.total_net_interest)} &#8381; &bull; ROI {(depBase.total_roi_pct || 0).toFixed(0)}%</p>
        </div>
      )}
    </div>
  )
}

function ScenarioCard({ title, icon, color, subtitle, vsDeposit, children }) {
  const borderColor = color === 'gold' ? 'border-rz-gold/30' : color === 'green' ? 'border-rz-success/30' : 'border-rz-cream-muted/30'
  const titleColor = color === 'gold' ? 'text-rz-gold' : color === 'green' ? 'text-rz-success' : 'text-rz-cream'
  return (
    <div className={`border ${borderColor} rounded-xl p-3`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className={`text-sm font-bold ${titleColor}`}>{icon} {title}</p>
          {subtitle && <p className="text-xs text-rz-cream-muted mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {children}
      {vsDeposit != null && (
        <p className={`text-xs font-bold mt-2 pt-2 border-t ${borderColor} ${vsDeposit > 0 ? 'text-rz-success' : 'text-rz-error'}`}>
          {vsDeposit > 0 ? '+' : ''}{fmt(vsDeposit)} &#8381; vs депозит
        </p>
      )}
    </div>
  )
}

function PortfolioReportCardV2({ data }) {
  const budget = data.budget || 0
  const sp = data.scenario_premium || {}
  const sf = data.scenario_portfolio || {}
  const sl = data.scenario_leverage || {}
  const dep = data.deposit_comparison || {}
  const depBase = dep.base || {}

  return (
    <div className="space-y-3">
      <div className="bg-rz-green-mid rounded-xl p-3">
        <p className="text-xs text-rz-cream-muted">Портфельный анализ — 3 сценария</p>
        <p className="font-bold text-lg text-rz-gold">{fmt(budget)} &#8381;</p>
      </div>

      {/* Scenario 1: Premium */}
      <ScenarioCard title={sp.name || 'Премиальный лот'} icon="◆" color="gold" subtitle={sp.lot ? `${sp.lot.code}, ${sp.lot.area_m2} м², корпус ${sp.lot.building} · ROI ${sp.roi_pct}%` : null} vsDeposit={sp.vs_deposit}>
        {sp.lot ? (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <MetricCell label="Цена (скидка 5%)" value={`${fmt(sp.discounted_price)} \u20BD`} />
              <MetricCell label="Остаток" value={`${fmt(sp.remaining_cash)} \u20BD`} />
            </div>
            {sp.metrics && (
              <div className="grid grid-cols-2 gap-2">
                <MetricCell label="Чистый доход / год" value={`${fmt(sp.metrics.noi)} \u20BD`} highlight />
                <MetricCell label="Доходность (Cap Rate)" value={`${sp.metrics.cap_rate}%`} highlight />
                <MetricCell label="ROI 11 лет" value={`${sp.roi_pct}%`} sub={`~${sp.metrics.avg_annual_pct}% / год`} />
                <MetricCell label="Доход на вложенное" value={`${sp.metrics.coc_full}%`} sub="при 100% оплате" />
              </div>
            )}
            <div className="bg-rz-success/10 rounded-lg p-2 flex justify-between text-sm">
              <span className="text-rz-cream-muted">Прибыль 11 лет</span>
              <span className="font-bold text-rz-success">{fmt(sp.total_profit)} &#8381; ({sp.roi_pct}%)</span>
            </div>
            {sp.reasoning && <p className="text-xs text-rz-cream-muted italic mt-1">{sp.reasoning}</p>}
          </div>
        ) : (
          <p className="text-rz-cream-muted text-sm">Нет подходящих лотов в бюджете</p>
        )}
      </ScenarioCard>

      {/* Scenario 2: Portfolio 100% */}
      <ScenarioCard title={sf.name || 'Портфель 100%'} icon="◈" color="green" subtitle={sf.lot_count ? `${sf.lot_count} лотов, вложено ${fmt(sf.total_invested)} \u20BD` : null} vsDeposit={sf.vs_deposit}>
        {sf.lots && sf.lots.length > 0 ? (
          <div className="space-y-2">
            <div className="space-y-1">
              {sf.lots.slice(0, 5).map(l => (
                <div key={`${l.code}-${l.building}`} className="bg-rz-green-mid/50 rounded-lg p-2 text-sm flex justify-between">
                  <div>
                    <span className="font-medium">{l.code}</span>
                    <span className="text-rz-cream-muted text-xs ml-1">К{l.building}, {l.floor}эт.</span>
                    <span className="text-rz-cream-muted text-xs ml-2">{l.area_m2} м&sup2;</span>
                  </div>
                  <div className="text-right">
                    <span className="text-rz-gold">{fmt(l.discounted_price)} &#8381;</span>
                    <span className="text-rz-success text-xs ml-2">ROI {l.roi_pct}%</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MetricCell label="Чистый доход / год" value={`${fmt(sf.total_noi)} \u20BD`} sub="суммарный" highlight />
              <MetricCell label="Доходность (Cap Rate)" value={`${sf.avg_cap_rate || 0}%`} sub="средняя" highlight />
              <MetricCell label="ROI 11 лет" value={`${sf.avg_roi_pct}%`} sub="средний" />
              <MetricCell label="Доход на вложенное" value={`${sf.avg_coc_full || 0}%`} sub="средний CoC" />
            </div>
            <div className="bg-rz-success/10 rounded-lg p-2 flex justify-between text-sm">
              <span className="text-rz-cream-muted">Прибыль 11 лет</span>
              <span className="font-bold text-rz-success">{fmt(sf.total_profit)} &#8381;</span>
            </div>
            {sf.reasoning && <p className="text-xs text-rz-cream-muted italic mt-1">{sf.reasoning}</p>}
          </div>
        ) : (
          <p className="text-rz-cream-muted text-sm">Нет подходящих лотов</p>
        )}
      </ScenarioCard>

      {/* Scenario 3: Max leverage */}
      <ScenarioCard title={sl.name || 'Максимальное плечо'} icon="◇" color="default" subtitle={sl.lot_count ? `${sl.lot_count} лотов, портфель ${fmt(sl.total_portfolio_value)} \u20BD` : null} vsDeposit={sl.vs_deposit}>
        {sl.lots && sl.lots.length > 0 ? (
          <div className="space-y-2">
            <div className="space-y-1">
              {sl.lots.slice(0, 5).map(l => (
                <div key={`${l.code}-${l.building}`} className="bg-rz-green-mid/50 rounded-lg p-2 text-sm">
                  <div className="flex justify-between">
                    <div>
                      <span className="font-medium">{l.code}</span>
                      <span className="text-rz-cream-muted text-xs ml-1">К{l.building}, {l.floor}эт.</span>
                    </div>
                    <div className="text-right">
                      <span className="text-rz-cream-dark">{fmt(l.price_rub)} &#8381;</span>
                      <span className="text-rz-success text-xs ml-2">ROI {l.roi_pct}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-rz-cream-muted mt-0.5">
                    <span>ПВ {fmt(l.down_payment)} &#8381;</span>
                    {l.monthly_payment && <span>{fmt(l.monthly_payment)} &#8381;/мес</span>}
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2">
              <MetricCell label="Чистый доход / год" value={`${fmt(sl.total_noi)} \u20BD`} sub="суммарный" highlight />
              <MetricCell label="Доходность (Cap Rate)" value={`${sl.avg_cap_rate || 0}%`} sub="средняя" highlight />
              <MetricCell label="ROI 11 лет" value={`${sl.avg_roi_pct || 0}%`} sub="средний" />
              <MetricCell label="Первоначальный взнос" value={`${fmt(sl.total_down_payment)} \u20BD`} />
              {sl.total_monthly != null && <MetricCell label="Платёж / мес" value={`${fmt(sl.total_monthly)} \u20BD`} sub="рассрочка 18м" highlight />}
              <MetricCell label="Переплата" value={`${fmt(sl.total_markup)} \u20BD`} sub="за 18 месяцев" />
            </div>
            <div className="bg-rz-success/10 rounded-lg p-2 flex justify-between text-sm">
              <span className="text-rz-cream-muted">Чистая прибыль</span>
              <span className="font-bold text-rz-success">{fmt(sl.net_profit)} &#8381;</span>
            </div>
            {sl.reasoning && <p className="text-xs text-rz-cream-muted italic mt-1">{sl.reasoning}</p>}
          </div>
        ) : (
          <p className="text-rz-cream-muted text-sm">Нет подходящих лотов</p>
        )}
      </ScenarioCard>

      {/* Deposit baseline */}
      {depBase.total_net_interest != null && (
        <div className="bg-rz-gold/10 rounded-xl p-3 border border-rz-gold/20">
          <p className="text-xs text-rz-cream-muted font-medium mb-1">Депозит для сравнения (11 лет)</p>
          <p className="font-bold">{fmt(depBase.final_balance)} &#8381;</p>
          <p className="text-xs text-rz-cream-dark">Проценты: {fmt(depBase.total_net_interest)} &#8381; &bull; ROI {(depBase.total_roi_pct || 0).toFixed(0)}%</p>
        </div>
      )}
    </div>
  )
}

export default function Chat({ lots, onNavigate }) {
  const [messages, setMessages] = useState([WELCOME_MSG])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const [showLotInput, setShowLotInput] = useState(false)
  const [showBudgetInput, setShowBudgetInput] = useState(false)
  const [lotCode, setLotCode] = useState('')
  const [budget, setBudget] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const abortRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }
  }, [input])

  // Shared SSE stream handler
  const handleStream = async (body) => {
    setError(null)
    setIsStreaming(true)
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (response.status === 429) {
        setError('Слишком много запросов. Подождите минуту.')
        setMessages(prev => prev.slice(0, -1))
        setIsStreaming(false)
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const contentType = response.headers.get('content-type') || ''

      // Action response (JSON)
      if (contentType.includes('application/json')) {
        const data = await response.json()
        if (data.type === 'action') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: 'assistant',
              content: data.message,
              actions: data.actions,
            }
            return updated
          })
          setIsStreaming(false)
          return
        }
      }

      // SSE streaming response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6)
          if (!jsonStr) continue

          try {
            const event = JSON.parse(jsonStr)
            if (event.type === 'token') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + event.content,
                    thinking: null,
                  }
                }
                return updated
              })
            } else if (event.type === 'thinking') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    thinking: event.label,
                  }
                }
                return updated
              })
            } else if (event.type === 'actions') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    actions: event.actions,
                  }
                }
                return updated
              })
            } else if (event.type === 'strategy_data') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    strategyData: event.data,
                  }
                }
                return updated
              })
            } else if (event.type === 'report_card') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    reportCard: { card_type: event.card_type, data: event.data },
                  }
                }
                return updated
              })
            } else if (event.type === 'error') {
              setError(event.content)
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError('Не удалось связаться с AI. Попробуйте позже.')
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant' && !last.content) {
            return prev.slice(0, -1)
          }
          return prev
        })
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  const sendMessage = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || isStreaming) return

    setInput('')

    // Add user message
    const userMsg = { role: 'user', content: trimmed }
    setMessages(prev => [...prev, userMsg])

    // Prepare history
    const history = [...messages, userMsg]
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }))
      .slice(0, -1)

    await handleStream({ message: trimmed, history })
  }

  const sendReport = async (mode, code = null, budgetVal = null) => {
    if (isStreaming) return
    setShowLotInput(false)
    setShowBudgetInput(false)

    const userMsg = mode === 'lot_report'
      ? `Фин. отчёт по лоту ${code}`
      : `Портфель на ${(budgetVal / 1000000).toFixed(0)} млн ₽`

    setMessages(prev => [...prev, { role: 'user', content: userMsg }])

    const body = { message: userMsg, history: [], mode }
    if (code) body.lot_code = code
    if (budgetVal) body.budget = parseInt(budgetVal)

    await handleStream(body)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const downloadStrategyPdf = async (data) => {
    try {
      const resp = await fetch('/api/strategy-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (!resp.ok) throw new Error('PDF generation failed')
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `RIZALTA_Strategy_${Date.now()}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('PDF download error:', e)
    }
  }

  const quickActions = [
    { label: 'Подобрать апартамент', action: () => onNavigate('lots') },
    { label: 'Доходность', query: 'Какая доходность у апартаментов RIZALTA?' },
    { label: 'Условия рассрочки', query: 'Расскажи про условия рассрочки' },
  ]

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream flex flex-col">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-3 sticky top-0 z-40">
        <div className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center text-rz-green-dark font-bold">
          R
        </div>
        <div>
          <p className="font-semibold">AI Консультант</p>
          <p className="text-xs text-rz-success">● Онлайн</p>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 p-4 space-y-4 overflow-auto pb-36">
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.reportCard ? (
              <div className="flex gap-2">
                <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0 mt-1">
                  R
                </div>
                <div className="flex-1 min-w-0 space-y-2">
                  {msg.reportCard.card_type === 'lot_report'
                    ? <LotReportCard data={msg.reportCard.data} />
                    : msg.reportCard.card_type === 'portfolio_report_v2'
                      ? <PortfolioReportCardV2 data={msg.reportCard.data} />
                      : <PortfolioReportCard data={msg.reportCard.data} />}
                  {msg.thinking && (
                    <div className="flex items-center gap-2 text-rz-cream-muted text-sm">
                      <span className="animate-pulse">●</span>
                      <span>{msg.thinking}</span>
                    </div>
                  )}
                  {msg.content && (
                    <div className="bg-rz-green-light rounded-2xl rounded-tl-none px-4 py-2.5">
                      <p className="text-sm whitespace-pre-line leading-relaxed">{renderText(msg.content)}</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'gap-2'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0 mt-1">
                    R
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                  msg.role === 'user'
                    ? 'bg-rz-gold text-rz-green-dark rounded-tr-none'
                    : 'bg-rz-green-light rounded-tl-none'
                }`}>
                  <p className="text-sm whitespace-pre-line leading-relaxed">{renderText(msg.content)}</p>
                  {msg.thinking && (
                    <div className="flex items-center gap-2 text-rz-cream-muted text-sm mt-1">
                      <span className="animate-pulse">●</span>
                      <span>{msg.thinking}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action buttons */}
            {msg.actions && msg.actions.length > 0 && (
              <div className="flex flex-wrap gap-2 pl-10 mt-2">
                {msg.actions.map((action, j) => (
                  <button
                    key={j}
                    onClick={() => {
                      if (action.type === 'navigate') {
                        resolveNavigation(action.to, onNavigate)
                      }
                    }}
                    className="bg-transparent border border-rz-gold text-rz-gold text-sm px-4 py-2 rounded-xl hover:bg-rz-gold hover:text-rz-green-dark transition-colors font-medium"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}

            {/* Strategy PDF download button */}
            {msg.strategyData && (
              <div className="pl-10 mt-2">
                <button
                  onClick={() => downloadStrategyPdf(msg.strategyData)}
                  className="flex items-center gap-2 px-4 py-2 bg-rz-gold text-rz-green-dark rounded-lg font-medium hover:bg-rz-gold-light transition-colors text-sm"
                >
                  <span>📄</span>
                  <span>Скачать PDF отчёт</span>
                </button>
              </div>
            )}
          </div>
        ))}

        {/* Report buttons + quick actions after welcome */}
        {messages.length === 1 && !isStreaming && (
          <>
            <div className="flex gap-3 pl-10">
              <button
                onClick={() => { setShowLotInput(true); setShowBudgetInput(false) }}
                className="flex-1 bg-rz-green-light border border-rz-gold/30 rounded-xl p-3 text-left hover:border-rz-gold transition"
              >
                <div className="text-rz-gold font-semibold text-sm">Фин. отчёт по лоту</div>
                <div className="text-rz-cream-dark text-xs mt-1">ROI, рассрочка, сравнение с депозитом</div>
              </button>
              <button
                onClick={() => { setShowBudgetInput(true); setShowLotInput(false) }}
                className="flex-1 bg-rz-green-light border border-rz-gold/30 rounded-xl p-3 text-left hover:border-rz-gold transition"
              >
                <div className="text-rz-gold font-semibold text-sm">Портфель по бюджету</div>
                <div className="text-rz-cream-dark text-xs mt-1">Подбор лотов и стратегий</div>
              </button>
            </div>

            {showLotInput && (
              <div className="ml-10 p-3 bg-rz-green-mid rounded-xl border border-rz-gold/20">
                <label className="text-rz-cream text-sm">Код лота:</label>
                <div className="flex gap-2 mt-2">
                  <input
                    type="text"
                    value={lotCode}
                    onChange={e => setLotCode(e.target.value.toUpperCase())}
                    placeholder="Например В818"
                    className="flex-1 bg-rz-green-dark text-rz-cream rounded-lg px-3 py-2 border border-rz-cream-muted/30 focus:border-rz-gold outline-none text-sm"
                    autoFocus
                    onKeyDown={e => { if (e.key === 'Enter' && lotCode.trim()) sendReport('lot_report', lotCode.trim()) }}
                  />
                  <button
                    onClick={() => lotCode.trim() && sendReport('lot_report', lotCode.trim())}
                    className="bg-rz-gold text-rz-green-dark font-semibold rounded-lg px-4 py-2 text-sm"
                  >
                    Сформировать
                  </button>
                </div>
              </div>
            )}

            {showBudgetInput && (
              <div className="ml-10 p-3 bg-rz-green-mid rounded-xl border border-rz-gold/20">
                <label className="text-rz-cream text-sm">Бюджет клиента:</label>
                <div className="flex gap-2 mt-2">
                  <input
                    type="number"
                    value={budget}
                    onChange={e => setBudget(e.target.value)}
                    placeholder="15000000"
                    className="flex-1 bg-rz-green-dark text-rz-cream rounded-lg px-3 py-2 border border-rz-cream-muted/30 focus:border-rz-gold outline-none text-sm"
                    autoFocus
                    onKeyDown={e => { if (e.key === 'Enter' && budget) sendReport('portfolio', null, budget) }}
                  />
                  <button
                    onClick={() => budget && sendReport('portfolio', null, budget)}
                    className="bg-rz-gold text-rz-green-dark font-semibold rounded-lg px-4 py-2 text-sm"
                  >
                    Подобрать
                  </button>
                </div>
                <div className="flex gap-2 mt-2">
                  {[5, 10, 15, 20, 30, 50].map(m => (
                    <button
                      key={m}
                      onClick={() => setBudget(m * 1000000)}
                      className="text-xs bg-rz-green-dark text-rz-cream-dark rounded px-2 py-1 hover:text-rz-gold transition"
                    >
                      {m} млн
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pl-10">
              {quickActions.map((qa, i) => (
                <button
                  key={i}
                  onClick={() => qa.action ? qa.action() : sendMessage(qa.query)}
                  className="bg-rz-green-mid text-sm px-3 py-1.5 rounded-full hover:bg-rz-green-light transition-colors text-rz-cream-dark border border-rz-green-light"
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </>
        )}

        {/* Typing indicator */}
        {isStreaming && messages[messages.length - 1]?.content === '' && !messages[messages.length - 1]?.reportCard && (
          <div className="flex gap-2">
            <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0">
              R
            </div>
            <div className="bg-rz-green-light rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="ml-10 bg-rz-error/20 text-rz-error rounded-lg px-4 py-2 text-sm">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="fixed bottom-16 left-0 right-0 p-3 bg-rz-green-dark border-t border-rz-green-mid pb-4">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите сообщение..."
            rows={1}
            className="flex-1 bg-rz-green-mid rounded-2xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted resize-none max-h-[120px]"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center hover:bg-rz-gold-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-rz-green-dark font-bold flex-shrink-0"
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  )
}
