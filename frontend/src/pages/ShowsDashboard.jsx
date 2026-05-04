import React, { useState, useEffect, useMemo } from 'react'

const STATUS_LABEL = {
  planned: 'Запланирован',
  completed: 'Проведён',
  completed_booked: 'Проведён + бронь',
  rescheduled: 'Перенесён',
  cancelled: 'Отменён',
}

const STATUS_PILL = {
  planned: 'bg-blue-600 text-rz-white',
  completed: 'bg-rz-success text-rz-white',
  completed_booked: 'bg-rz-gold text-rz-green',
  rescheduled: 'bg-yellow-700 text-rz-white',
  cancelled: 'bg-rz-cream-muted text-rz-green',
}

const PRESET_LABEL = {
  today: 'Сегодня',
  yesterday: 'Вчера',
  week: 'Эта неделя',
  month: 'Этот месяц',
  custom: 'Произвольный',
}

function pad(n) { return String(n).padStart(2, '0') }
function ymd(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` }

function presetRange(preset) {
  const now = new Date(); now.setHours(0,0,0,0)
  if (preset === 'today') return { from: ymd(now), to: ymd(now) }
  if (preset === 'yesterday') {
    const y = new Date(now); y.setDate(y.getDate() - 1)
    return { from: ymd(y), to: ymd(y) }
  }
  if (preset === 'week') {
    const dow = now.getDay()
    const diff = (dow === 0 ? -6 : 1 - dow)
    const mon = new Date(now); mon.setDate(mon.getDate() + diff)
    const sun = new Date(mon); sun.setDate(sun.getDate() + 6)
    return { from: ymd(mon), to: ymd(sun) }
  }
  if (preset === 'month') {
    const first = new Date(now.getFullYear(), now.getMonth(), 1)
    const last = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    return { from: ymd(first), to: ymd(last) }
  }
  return { from: ymd(now), to: ymd(now) }
}

function dtParts(s) {
  if (!s) return { date: '—', time: '' }
  const norm = s.replace('T', ' ')
  const [d, t] = norm.split(' ')
  return { date: d, time: (t || '').slice(0, 5) }
}

function fmtDate(s) {
  const { date, time } = dtParts(s)
  if (date === '—') return '—'
  const [y, m, dd] = date.split('-')
  return `${dd}.${m}.${y} ${time}`
}

export default function ShowsDashboard({ onBack }) {
  const [preset, setPreset] = useState('month')
  const initial = presetRange('month')
  const [from, setFrom] = useState(initial.from)
  const [to, setTo] = useState(initial.to)

  const [stats, setStats] = useState([])
  const [totals, setTotals] = useState(null)
  const [shows, setShows] = useState([])
  const [filterManager, setFilterManager] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function applyPreset(p) {
    setPreset(p)
    if (p !== 'custom') {
      const r = presetRange(p)
      setFrom(r.from); setTo(r.to)
    }
  }

  function load() {
    setLoading(true); setError('')
    const dateParams = new URLSearchParams({
      date_from: `${from} 00:00:00`,
      date_to: `${to} 23:59:59`,
    })
    const listParams = new URLSearchParams(dateParams)
    if (filterManager) listParams.set('manager', filterManager)
    if (filterStatus) listParams.set('status', filterStatus)
    Promise.all([
      fetch(`/api/shows/dashboard/stats?${dateParams}`).then(r => r.json()),
      fetch(`/api/shows/dashboard/list?${listParams}`).then(r => r.json()),
    ])
      .then(([s, l]) => {
        if (s.ok) { setStats(s.stats); setTotals(s.totals) } else setError(s.error || 'Ошибка stats')
        if (l.ok) setShows(l.shows); else setError(prev => prev || l.error || 'Ошибка списка')
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [from, to, filterManager, filterStatus])

  const flags = useMemo(() => buildFlags(stats), [stats])
  const managerOptions = useMemo(() => stats.map(s => s.manager), [stats])

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-rz-green border-b border-rz-green-light z-30">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={onBack} className="text-rz-cream-dark text-sm">← Главная</button>
          <h1 className="text-lg font-semibold text-rz-gold flex-1">Дашборд показов</h1>
          <button
            onClick={load}
            disabled={loading}
            className="bg-rz-gold hover:bg-rz-gold-light text-rz-green font-semibold rounded-lg px-3 py-1.5 text-sm disabled:opacity-60"
          >
            {loading ? '…' : 'Обновить'}
          </button>
        </div>
        <div className="max-w-6xl mx-auto px-4 pb-3 flex items-center gap-2 flex-wrap">
          {Object.keys(PRESET_LABEL).map(p => (
            <button
              key={p}
              onClick={() => applyPreset(p)}
              className={`px-3 py-1.5 text-sm rounded ${preset===p ? 'bg-rz-gold text-rz-green' : 'bg-rz-green-mid text-rz-cream-dark hover:text-rz-gold'}`}
            >
              {PRESET_LABEL[p]}
            </button>
          ))}
          {preset === 'custom' && (
            <div className="flex items-center gap-2 w-full sm:w-auto mt-1 sm:mt-0">
              <input type="date" value={from} onChange={e => setFrom(e.target.value)} className={dateInputCls} />
              <span className="text-rz-cream-dark text-sm">—</span>
              <input type="date" value={to} onChange={e => setTo(e.target.value)} className={dateInputCls} />
            </div>
          )}
          <div className="text-xs text-rz-cream-muted ml-auto">
            {from === to ? from : `${from} — ${to}`}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 mt-4">
        {error && <div className="text-rz-error text-sm mb-3">{error}</div>}

        {/* Red flags */}
        {flags.length > 0 && (
          <section className="mb-6">
            <h2 className="text-sm uppercase tracking-wide text-rz-cream-dark mb-2">🚩 Красные флаги</h2>
            <div className="grid sm:grid-cols-2 gap-2">
              {flags.map((f, i) => (
                <div key={i} className="bg-rz-error/15 border border-rz-error/40 rounded-lg p-3">
                  <div className="text-rz-error font-semibold text-sm">{f.manager}</div>
                  <div className="text-rz-cream text-sm mt-0.5">{f.message}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Manager stats */}
        <section className="mb-6">
          <h2 className="text-sm uppercase tracking-wide text-rz-cream-dark mb-2">Сводка по менеджерам</h2>

          {/* Desktop table */}
          <div className="hidden md:block overflow-hidden rounded-lg border border-rz-green-light">
            <table className="w-full text-sm">
              <thead className="bg-rz-green-mid text-rz-cream-dark">
                <tr>
                  <th className="text-left px-3 py-2">Менеджер</th>
                  <th className="text-right px-3 py-2">Всего</th>
                  <th className="text-right px-3 py-2">Запланир.</th>
                  <th className="text-right px-3 py-2">Проведено</th>
                  <th className="text-right px-3 py-2">из них с бронью</th>
                  <th className="text-right px-3 py-2">Перенесено</th>
                  <th className="text-right px-3 py-2">Отменено</th>
                  <th className="text-right px-3 py-2">% броней</th>
                </tr>
              </thead>
              <tbody>
                {stats.map(s => (
                  <tr key={s.manager} className="border-t border-rz-green-light">
                    <td className="px-3 py-2 text-rz-cream">{s.manager}</td>
                    <td className="px-3 py-2 text-right">{s.total}</td>
                    <td className="px-3 py-2 text-right">{s.planned}</td>
                    <td className="px-3 py-2 text-right">{s.completed + s.completed_booked}</td>
                    <td className="px-3 py-2 text-right text-rz-gold font-semibold">{s.completed_booked}</td>
                    <td className="px-3 py-2 text-right">{s.rescheduled}</td>
                    <td className="px-3 py-2 text-right">{s.cancelled}</td>
                    <td className="px-3 py-2 text-right">{s.booking_rate == null ? '—' : `${s.booking_rate}%`}</td>
                  </tr>
                ))}
                {totals && (
                  <tr className="border-t-2 border-rz-gold/40 bg-rz-green-mid font-semibold">
                    <td className="px-3 py-2 text-rz-gold">Итого</td>
                    <td className="px-3 py-2 text-right">{totals.total}</td>
                    <td className="px-3 py-2 text-right">{totals.planned}</td>
                    <td className="px-3 py-2 text-right">{totals.completed + totals.completed_booked}</td>
                    <td className="px-3 py-2 text-right text-rz-gold">{totals.completed_booked}</td>
                    <td className="px-3 py-2 text-right">{totals.rescheduled}</td>
                    <td className="px-3 py-2 text-right">{totals.cancelled}</td>
                    <td className="px-3 py-2 text-right">{totals.booking_rate == null ? '—' : `${totals.booking_rate}%`}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {stats.map(s => <ManagerCard key={s.manager} s={s} />)}
            {totals && <ManagerCard s={{ manager: 'Итого', ...totals }} highlight />}
          </div>
        </section>

        {/* Shows list */}
        <section>
          <h2 className="text-sm uppercase tracking-wide text-rz-cream-dark mb-2">Все показы</h2>
          <div className="flex gap-2 mb-3 flex-wrap">
            <select value={filterManager} onChange={e => setFilterManager(e.target.value)} className={selectCls}>
              <option value="">Все менеджеры</option>
              {managerOptions.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className={selectCls}>
              <option value="">Все статусы</option>
              {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <div className="text-xs text-rz-cream-muted ml-auto self-center">{shows.length} {pluralShow(shows.length)}</div>
          </div>

          {shows.length === 0 ? (
            <div className="text-rz-cream-muted text-sm py-6 text-center">Нет показов за выбранный период</div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block overflow-hidden rounded-lg border border-rz-green-light">
                <table className="w-full text-sm">
                  <thead className="bg-rz-green-mid text-rz-cream-dark">
                    <tr>
                      <th className="text-left px-3 py-2">Дата+время</th>
                      <th className="text-left px-3 py-2">Менеджер</th>
                      <th className="text-left px-3 py-2">Агентство</th>
                      <th className="text-left px-3 py-2">Риэлтор</th>
                      <th className="text-left px-3 py-2">Статус</th>
                      <th className="text-left px-3 py-2">Комментарий</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shows.map(s => (
                      <tr key={s.id} className="border-t border-rz-green-light">
                        <td className="px-3 py-2 text-rz-cream whitespace-nowrap">{fmtDate(s.show_datetime)}</td>
                        <td className="px-3 py-2">{s.manager}</td>
                        <td className="px-3 py-2">{s.realtor_agency || '—'}</td>
                        <td className="px-3 py-2">{s.realtor_name}</td>
                        <td className="px-3 py-2">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs ${STATUS_PILL[s.status] || 'bg-rz-green-light'}`}>
                            {STATUS_LABEL[s.status] || s.status}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-rz-cream-dark">{s.comment || ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3">
                {shows.map(s => <ShowCard key={s.id} s={s} />)}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

function buildFlags(stats) {
  const flags = []
  for (const s of stats) {
    const conducted = s.completed + s.completed_booked
    if (conducted >= 5 && s.booking_rate != null && s.booking_rate < 20) {
      flags.push({
        manager: s.manager,
        message: `Высокая активность (${conducted} проведённых), низкая конверсия в бронь — ${s.booking_rate}%`,
      })
    }
    if (s.total < 3) {
      flags.push({
        manager: s.manager,
        message: `Низкая активность — всего ${s.total} ${pluralShow(s.total)} за период`,
      })
    }
  }
  return flags
}

function ManagerCard({ s, highlight }) {
  const cells = [
    { label: 'Всего', value: s.total },
    { label: 'Запланировано', value: s.planned },
    { label: 'Проведено', value: s.completed + s.completed_booked },
    { label: 'из них с бронью', value: s.completed_booked, gold: true },
    { label: 'Перенесено', value: s.rescheduled },
    { label: 'Отменено', value: s.cancelled },
    { label: '% броней', value: s.booking_rate == null ? '—' : `${s.booking_rate}%`, span: 2 },
  ]
  return (
    <div className={`rounded-lg p-3 ${highlight ? 'bg-rz-green-mid border-2 border-rz-gold/40' : 'bg-rz-green-mid border border-rz-green-light'}`}>
      <div className={`font-semibold mb-2 ${highlight ? 'text-rz-gold' : 'text-rz-cream'}`}>{s.manager}</div>
      <div className="grid grid-cols-2 gap-2">
        {cells.map((c, i) => (
          <div key={i} className={`bg-rz-green rounded px-2 py-1.5 ${c.span === 2 ? 'col-span-2' : ''}`}>
            <div className="text-[10px] text-rz-cream-muted uppercase">{c.label}</div>
            <div className={`text-base font-semibold ${c.gold ? 'text-rz-gold' : 'text-rz-cream'}`}>{c.value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ShowCard({ s }) {
  return (
    <div className="bg-rz-green-mid border border-rz-green-light rounded-lg p-3">
      <div className="text-rz-gold font-semibold text-base">{fmtDate(s.show_datetime)}</div>
      <div className="mt-2 text-sm space-y-1">
        <div><span className="text-rz-cream-muted">Менеджер:</span> {s.manager}</div>
        <div><span className="text-rz-cream-muted">Агентство:</span> {s.realtor_agency || '—'}</div>
        <div><span className="text-rz-cream-muted">Риэлтор:</span> {s.realtor_name}</div>
        <div className="pt-1">
          <span className={`inline-block px-2 py-0.5 rounded text-xs ${STATUS_PILL[s.status] || 'bg-rz-green-light'}`}>
            {STATUS_LABEL[s.status] || s.status}
          </span>
        </div>
        {s.comment && <div className="text-rz-cream-dark italic pt-1">{s.comment}</div>}
      </div>
    </div>
  )
}

function pluralShow(n) {
  const m10 = n % 10, m100 = n % 100
  if (m10 === 1 && m100 !== 11) return 'показ'
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return 'показа'
  return 'показов'
}

const dateInputCls = "bg-rz-green-mid border border-rz-green-light rounded px-2 py-1 text-rz-cream text-sm"
const selectCls = "bg-rz-green-mid border border-rz-green-light rounded px-3 py-1.5 text-rz-cream text-sm"
