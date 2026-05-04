import React, { useState, useEffect, useMemo } from 'react'

const STATUS_LABEL = {
  planned: 'Запланирован',
  rescheduled: 'Перенесён',
  completed: 'Проведён',
  cancelled: 'Отменён',
  no_show: 'Не пришли',
}

const STATUS_BG = {
  planned: 'bg-blue-600',
  rescheduled: 'bg-yellow-500',
  completed: 'bg-rz-success',
  cancelled: 'bg-rz-cream-muted',
  no_show: 'bg-rz-error',
}

const RESULT_LABEL = {
  interested: 'Заинтересован',
  booked: 'Забронировал',
  not_interested: 'Не интересно',
  contact_saved: 'Сохранён контакт',
}

const DAYS_RU_FULL = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
const DAYS_RU_SHORT = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
const MONTHS_RU = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

const HOURS = Array.from({ length: 11 }, (_, i) => 10 + i) // 10..20

const LS_KEY = 'shows_manager'

function pad(n) { return String(n).padStart(2, '0') }

function dateToYMD(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function ymdhmToISO(date, time) {
  // date: YYYY-MM-DD, time: HH:MM -> "YYYY-MM-DD HH:MM:00" (sortable text)
  return `${date} ${time}:00`
}

function parseShowDT(s) {
  // "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DDTHH:MM:SS"
  if (!s) return null
  const norm = s.replace('T', ' ')
  const [d, t] = norm.split(' ')
  return { date: d, time: (t || '00:00:00').slice(0, 5) }
}

function startOfWeek(d) {
  const date = new Date(d)
  const dow = date.getDay()
  const diff = (dow === 0 ? -6 : 1 - dow) // Mon-start
  date.setDate(date.getDate() + diff)
  date.setHours(0, 0, 0, 0)
  return date
}

function addDays(d, n) {
  const x = new Date(d); x.setDate(x.getDate() + n); return x
}

function startOfMonth(d) {
  const x = new Date(d.getFullYear(), d.getMonth(), 1)
  return x
}

export default function Shows({ onBack }) {
  const [manager, setManager] = useState(null)
  const [managers, setManagers] = useState([])
  const [view, setView] = useState('week') // day | week | month
  const [anchor, setAnchor] = useState(() => { const d = new Date(); d.setHours(0,0,0,0); return d })
  const [shows, setShows] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [editing, setEditing] = useState(null) // show object
  const [error, setError] = useState('')

  // Init manager from localStorage + load managers list
  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY)
    if (saved) setManager(saved)
    fetch('/api/shows/managers')
      .then(r => r.json())
      .then(d => { if (d.ok) setManagers(d.managers) })
      .catch(() => {})
  }, [])

  const range = useMemo(() => {
    if (view === 'day') {
      return { from: dateToYMD(anchor), to: dateToYMD(anchor), days: [new Date(anchor)] }
    }
    if (view === 'week') {
      const start = startOfWeek(anchor)
      const days = Array.from({ length: 7 }, (_, i) => addDays(start, i))
      return { from: dateToYMD(days[0]), to: dateToYMD(days[6]), days }
    }
    // month
    const first = startOfMonth(anchor)
    const last = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0)
    const days = []
    for (let i = 0; i < last.getDate(); i++) days.push(addDays(first, i))
    return { from: dateToYMD(first), to: dateToYMD(last), days }
  }, [view, anchor])

  // Fetch shows when range changes
  useEffect(() => {
    if (!manager) return
    setLoading(true)
    setError('')
    const params = new URLSearchParams({
      date_from: `${range.from} 00:00:00`,
      date_to: `${range.to} 23:59:59`,
    })
    fetch(`/api/shows?${params}`)
      .then(r => r.json())
      .then(d => {
        if (d.ok) setShows(d.shows || [])
        else setError(d.error || 'Ошибка загрузки')
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [manager, range.from, range.to])

  function refresh() {
    if (!manager) return
    const params = new URLSearchParams({
      date_from: `${range.from} 00:00:00`,
      date_to: `${range.to} 23:59:59`,
    })
    fetch(`/api/shows?${params}`)
      .then(r => r.json())
      .then(d => { if (d.ok) setShows(d.shows || []) })
  }

  function pickManager(name) {
    localStorage.setItem(LS_KEY, name)
    setManager(name)
  }

  function changeUser() {
    localStorage.removeItem(LS_KEY)
    setManager(null)
  }

  function navigate(delta) {
    const d = new Date(anchor)
    if (view === 'day') d.setDate(d.getDate() + delta)
    else if (view === 'week') d.setDate(d.getDate() + 7 * delta)
    else d.setMonth(d.getMonth() + delta)
    setAnchor(d)
  }

  // ===== Manager picker =====
  if (!manager) {
    return (
      <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
        <div className="max-w-md mx-auto px-4 pt-10">
          <button onClick={onBack} className="text-rz-cream-dark text-sm mb-6">← На главную</button>
          <h1 className="text-2xl font-semibold text-rz-gold mb-2">Кто вы?</h1>
          <p className="text-rz-cream-dark text-sm mb-6">Выберите своё имя — оно сохранится для следующих визитов.</p>
          <div className="flex flex-col gap-3">
            {(managers.length ? managers : ['Дегтярева Марина','Шумова Дарья','Хватик Светлана','Панченко Инна']).map(n => (
              <button
                key={n}
                onClick={() => pickManager(n)}
                className="bg-rz-green-light hover:bg-rz-green-dark border border-rz-gold/40 text-rz-cream rounded-xl py-4 px-5 text-left text-base"
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ===== Calendar =====
  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-rz-green border-b border-rz-green-light z-30">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={onBack} className="text-rz-cream-dark text-sm">← Главная</button>
          <h1 className="text-lg font-semibold text-rz-gold flex-1">Календарь показов</h1>
          <div className="text-xs text-rz-cream-dark hidden sm:block">{manager}</div>
          <button onClick={changeUser} className="text-xs text-rz-cream-dark underline">Сменить</button>
        </div>
        <div className="max-w-6xl mx-auto px-4 pb-3 flex items-center gap-2 flex-wrap">
          <div className="flex bg-rz-green-mid rounded-lg overflow-hidden">
            {['day','week','month'].map(v => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1.5 text-sm ${view===v ? 'bg-rz-gold text-rz-green' : 'text-rz-cream-dark'}`}
              >
                {v==='day'?'День':v==='week'?'Неделя':'Месяц'}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => navigate(-1)} className="px-2 py-1 text-rz-cream-dark hover:text-rz-gold">‹</button>
            <button
              onClick={() => { const d = new Date(); d.setHours(0,0,0,0); setAnchor(d) }}
              className="px-3 py-1 text-sm border border-rz-gold/40 rounded text-rz-cream"
            >Сегодня</button>
            <button onClick={() => navigate(1)} className="px-2 py-1 text-rz-cream-dark hover:text-rz-gold">›</button>
          </div>
          <div className="text-sm text-rz-cream-dark ml-auto">
            {view==='month' ? `${MONTHS_RU[anchor.getMonth()]} ${anchor.getFullYear()}`
              : `${range.days[0].getDate()} ${MONTHS_RU[range.days[0].getMonth()].toLowerCase()} — ${range.days[range.days.length-1].getDate()} ${MONTHS_RU[range.days[range.days.length-1].getMonth()].toLowerCase()}`}
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="w-full sm:w-auto bg-rz-gold hover:bg-rz-gold-light text-rz-green font-semibold rounded-lg px-4 py-2.5 text-sm flex items-center justify-center gap-1.5 shadow"
          >
            <span className="text-lg leading-none">+</span>
            <span>Создать показ</span>
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="max-w-6xl mx-auto px-2 sm:px-4 mt-4">
        {error && <div className="text-rz-error text-sm mb-3">{error}</div>}
        {loading && <div className="text-rz-cream-dark text-sm mb-3">Загрузка…</div>}

        {view === 'month' ? (
          <MonthView days={range.days} shows={shows} manager={manager} onClickShow={setEditing} />
        ) : (
          <TimeGrid days={range.days} shows={shows} manager={manager} onClickShow={setEditing} />
        )}
      </div>

      {showCreate && (
        <CreateModal
          manager={manager}
          managers={managers}
          defaultDate={dateToYMD(view==='month' ? anchor : (range.days[0] || anchor))}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); refresh() }}
        />
      )}

      {editing && (
        <EditModal
          show={editing}
          managers={managers}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); refresh() }}
          onDeleted={() => { setEditing(null); refresh() }}
        />
      )}
    </div>
  )
}

// ============ Time grid (day/week) ============

function TimeGrid({ days, shows, manager, onClickShow }) {
  const showsByDay = useMemo(() => {
    const map = {}
    for (const d of days) map[dateToYMD(d)] = []
    for (const s of shows) {
      const dt = parseShowDT(s.show_datetime)
      if (dt && map[dt.date] !== undefined) map[dt.date].push(s)
    }
    return map
  }, [days, shows])

  return (
    <div className="overflow-x-auto">
      <div className="grid" style={{ gridTemplateColumns: `60px repeat(${days.length}, minmax(140px, 1fr))` }}>
        {/* Header row */}
        <div></div>
        {days.map(d => {
          const isToday = dateToYMD(d) === dateToYMD(new Date())
          return (
            <div key={dateToYMD(d)} className={`text-center py-2 border-b border-rz-green-light ${isToday ? 'text-rz-gold' : 'text-rz-cream-dark'}`}>
              <div className="text-xs">{DAYS_RU_SHORT[d.getDay()]}</div>
              <div className="text-base font-semibold">{d.getDate()} {MONTHS_RU[d.getMonth()].slice(0,3).toLowerCase()}</div>
            </div>
          )
        })}

        {/* Hours */}
        {HOURS.map(h => (
          <React.Fragment key={h}>
            <div className="text-xs text-rz-cream-muted text-right pr-2 py-2 border-t border-rz-green-light">{pad(h)}:00</div>
            {days.map(d => {
              const ymd = dateToYMD(d)
              const inSlot = (showsByDay[ymd] || []).filter(s => {
                const dt = parseShowDT(s.show_datetime)
                if (!dt) return false
                const hh = parseInt(dt.time.slice(0, 2), 10)
                return hh === h
              })
              return (
                <div key={ymd + h} className="border-t border-l border-rz-green-light min-h-[60px] p-1 relative">
                  {inSlot.map(s => <ShowCard key={s.id} show={s} mine={s.manager === manager} onClick={() => onClickShow(s)} />)}
                </div>
              )
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}

function ShowCard({ show, mine, onClick }) {
  const dt = parseShowDT(show.show_datetime)
  return (
    <button
      onClick={onClick}
      className={`w-full text-left text-xs ${STATUS_BG[show.status] || 'bg-rz-green-light'} text-rz-white rounded px-1.5 py-1 mb-1 ${mine ? 'ring-2 ring-rz-gold' : ''}`}
      title={`${STATUS_LABEL[show.status]} · ${show.manager}`}
    >
      <div className="font-semibold">{dt?.time || '—'} · {show.planned_lot}</div>
      <div className="truncate opacity-90">{show.realtor_name}</div>
    </button>
  )
}

// ============ Month view ============

function MonthView({ days, shows, manager, onClickShow }) {
  // Pad to start on Monday
  const first = days[0]
  const lead = (first.getDay() + 6) % 7 // Mon=0
  const cells = []
  for (let i = 0; i < lead; i++) cells.push(null)
  for (const d of days) cells.push(d)
  while (cells.length % 7 !== 0) cells.push(null)

  const showsByDay = useMemo(() => {
    const map = {}
    for (const s of shows) {
      const dt = parseShowDT(s.show_datetime)
      if (!dt) continue
      if (!map[dt.date]) map[dt.date] = []
      map[dt.date].push(s)
    }
    return map
  }, [shows])

  return (
    <div className="grid grid-cols-7 gap-px bg-rz-green-light rounded overflow-hidden">
      {DAYS_RU_SHORT.slice(1).concat(DAYS_RU_SHORT[0]).map(d => (
        <div key={d} className="bg-rz-green text-center text-xs text-rz-cream-dark py-2">{d}</div>
      ))}
      {cells.map((d, i) => (
        <div key={i} className="bg-rz-green min-h-[100px] p-1.5">
          {d && (
            <>
              <div className={`text-xs ${dateToYMD(d) === dateToYMD(new Date()) ? 'text-rz-gold font-bold' : 'text-rz-cream-dark'}`}>
                {d.getDate()}
              </div>
              <div className="space-y-0.5 mt-1">
                {(showsByDay[dateToYMD(d)] || []).slice(0, 3).map(s => (
                  <ShowCard key={s.id} show={s} mine={s.manager === manager} onClick={() => onClickShow(s)} />
                ))}
                {(showsByDay[dateToYMD(d)] || []).length > 3 && (
                  <div className="text-[10px] text-rz-cream-muted">+{(showsByDay[dateToYMD(d)] || []).length - 3} ещё</div>
                )}
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  )
}

// ============ Create modal ============

function CreateModal({ manager, managers, defaultDate, onClose, onCreated }) {
  const [form, setForm] = useState({
    date: defaultDate,
    time: '12:00',
    realtor_name: '',
    realtor_phone: '',
    realtor_agency: '',
    client_name: '',
    planned_lot: '',
  })
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')
  const [lotInfo, setLotInfo] = useState(null)

  function update(k, v) { setForm(f => ({ ...f, [k]: v })) }

  // Lot autocomplete via /api/lots/search
  useEffect(() => {
    const code = form.planned_lot.trim()
    if (code.length < 3) { setLotInfo(null); return }
    const t = setTimeout(() => {
      fetch(`/api/lots/search?code=${encodeURIComponent(code)}`)
        .then(r => r.json())
        .then(d => {
          if (d.ok && d.lot) setLotInfo({ ok: true, label: `${d.lot.code} · ${d.lot.buildingName} · ${d.lot.area} м²` })
          else if (d.ok && d.multiple) setLotInfo({ ok: true, label: `Найдено: ${d.lots.length}` })
          else setLotInfo({ ok: false, label: 'Лот не найден' })
        })
        .catch(() => setLotInfo(null))
    }, 350)
    return () => clearTimeout(t)
  }, [form.planned_lot])

  async function submit(e) {
    e.preventDefault()
    setErr('')
    if (!form.realtor_name.trim() || !form.planned_lot.trim()) {
      setErr('Заполните риэлтора и лот')
      return
    }
    setSaving(true)
    try {
      const res = await fetch('/api/shows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          show_datetime: ymdhmToISO(form.date, form.time),
          manager,
          realtor_name: form.realtor_name.trim(),
          realtor_phone: form.realtor_phone.trim() || null,
          realtor_agency: form.realtor_agency.trim() || null,
          client_name: form.client_name.trim() || null,
          planned_lot: form.planned_lot.trim(),
        }),
      })
      const data = await res.json()
      if (data.ok) onCreated()
      else setErr(data.error || data.detail || 'Ошибка сохранения')
    } catch (e) {
      setErr(String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal onClose={onClose} title="Новый показ">
      <form onSubmit={submit} className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <Field label="Дата">
            <input type="date" value={form.date} onChange={e => update('date', e.target.value)} className={inputCls} required />
          </Field>
          <Field label="Время">
            <input type="time" value={form.time} onChange={e => update('time', e.target.value)} className={inputCls} required />
          </Field>
        </div>
        <Field label="Менеджер">
          <input value={manager} disabled className={inputCls + ' opacity-70'} />
        </Field>
        <Field label="Риэлтор (ФИО)*">
          <input value={form.realtor_name} onChange={e => update('realtor_name', e.target.value)} className={inputCls} required />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Телефон">
            <input value={form.realtor_phone} onChange={e => update('realtor_phone', e.target.value)} className={inputCls} />
          </Field>
          <Field label="Агентство">
            <input value={form.realtor_agency} onChange={e => update('realtor_agency', e.target.value)} className={inputCls} />
          </Field>
        </div>
        <Field label="Клиент (опционально)">
          <input value={form.client_name} onChange={e => update('client_name', e.target.value)} className={inputCls} />
        </Field>
        <Field label="Планируемый лот* (код)">
          <input value={form.planned_lot} onChange={e => update('planned_lot', e.target.value)} className={inputCls} required placeholder="например, А-12-3" />
          {lotInfo && (
            <div className={`text-xs mt-1 ${lotInfo.ok ? 'text-rz-success' : 'text-rz-cream-muted'}`}>{lotInfo.label}</div>
          )}
        </Field>

        {err && <div className="text-rz-error text-sm">{err}</div>}
        <div className="flex gap-2 pt-2">
          <button type="button" onClick={onClose} className="flex-1 py-2 rounded border border-rz-green-light text-rz-cream-dark">Отмена</button>
          <button type="submit" disabled={saving} className="flex-1 py-2 rounded bg-rz-gold text-rz-green font-semibold disabled:opacity-60">
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ============ Edit modal ============

function EditModal({ show, managers, onClose, onSaved, onDeleted }) {
  const dt = parseShowDT(show.show_datetime) || { date: '', time: '' }
  const [form, setForm] = useState({
    date: dt.date,
    time: dt.time,
    manager: show.manager,
    realtor_name: show.realtor_name || '',
    realtor_phone: show.realtor_phone || '',
    realtor_agency: show.realtor_agency || '',
    client_name: show.client_name || '',
    planned_lot: show.planned_lot || '',
    status: show.status || 'planned',
    actual_lot: show.actual_lot || '',
    result: show.result || '',
    comment: show.comment || '',
    reschedule_to: show.reschedule_to || '',
    reschedule_reason: show.reschedule_reason || '',
  })
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')
  const [confirmDel, setConfirmDel] = useState(false)

  function update(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function submit(e) {
    e.preventDefault()
    setErr('')
    setSaving(true)
    try {
      const body = {
        show_datetime: ymdhmToISO(form.date, form.time),
        manager: form.manager,
        realtor_name: form.realtor_name.trim(),
        realtor_phone: form.realtor_phone.trim() || null,
        realtor_agency: form.realtor_agency.trim() || null,
        client_name: form.client_name.trim() || null,
        planned_lot: form.planned_lot.trim(),
        status: form.status,
        actual_lot: form.status === 'completed' ? (form.actual_lot.trim() || null) : null,
        result: form.status === 'completed' ? (form.result || null) : null,
        comment: form.comment.trim() || null,
        reschedule_to: form.status === 'rescheduled' ? (form.reschedule_to || null) : null,
        reschedule_reason: form.status === 'rescheduled' ? (form.reschedule_reason.trim() || null) : null,
      }
      const res = await fetch(`/api/shows/${show.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (data.ok) onSaved()
      else setErr(data.error || data.detail || 'Ошибка сохранения')
    } catch (e) {
      setErr(String(e))
    } finally {
      setSaving(false)
    }
  }

  async function doDelete() {
    setSaving(true)
    try {
      const res = await fetch(`/api/shows/${show.id}`, { method: 'DELETE' })
      const data = await res.json()
      if (data.ok) onDeleted()
      else setErr(data.detail || 'Ошибка удаления')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal onClose={onClose} title={`Показ #${show.id}`}>
      <form onSubmit={submit} className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <Field label="Дата"><input type="date" value={form.date} onChange={e => update('date', e.target.value)} className={inputCls} required /></Field>
          <Field label="Время"><input type="time" value={form.time} onChange={e => update('time', e.target.value)} className={inputCls} required /></Field>
        </div>
        <Field label="Менеджер">
          <select value={form.manager} onChange={e => update('manager', e.target.value)} className={inputCls}>
            {managers.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </Field>
        <Field label="Статус">
          <select value={form.status} onChange={e => update('status', e.target.value)} className={inputCls}>
            {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>

        {form.status === 'rescheduled' && (
          <div className="space-y-2 p-3 bg-rz-green-mid rounded border border-yellow-500/30">
            <Field label="Перенесено на (дата+время)">
              <input type="datetime-local" value={form.reschedule_to ? form.reschedule_to.replace(' ', 'T').slice(0,16) : ''}
                onChange={e => update('reschedule_to', e.target.value.replace('T', ' ') + ':00')}
                className={inputCls} />
            </Field>
            <Field label="Причина переноса">
              <input value={form.reschedule_reason} onChange={e => update('reschedule_reason', e.target.value)} className={inputCls} />
            </Field>
          </div>
        )}

        {form.status === 'completed' && (
          <div className="space-y-2 p-3 bg-rz-green-mid rounded border border-rz-success/30">
            <Field label="Реально показанный лот">
              <input value={form.actual_lot} onChange={e => update('actual_lot', e.target.value)} className={inputCls} placeholder="код лота" />
            </Field>
            <Field label="Результат">
              <select value={form.result} onChange={e => update('result', e.target.value)} className={inputCls}>
                <option value="">— не указан —</option>
                {Object.entries(RESULT_LABEL).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </Field>
          </div>
        )}

        <Field label="Риэлтор"><input value={form.realtor_name} onChange={e => update('realtor_name', e.target.value)} className={inputCls} /></Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Телефон"><input value={form.realtor_phone} onChange={e => update('realtor_phone', e.target.value)} className={inputCls} /></Field>
          <Field label="Агентство"><input value={form.realtor_agency} onChange={e => update('realtor_agency', e.target.value)} className={inputCls} /></Field>
        </div>
        <Field label="Клиент"><input value={form.client_name} onChange={e => update('client_name', e.target.value)} className={inputCls} /></Field>
        <Field label="Планируемый лот"><input value={form.planned_lot} onChange={e => update('planned_lot', e.target.value)} className={inputCls} /></Field>
        <Field label="Комментарий">
          <textarea value={form.comment} onChange={e => update('comment', e.target.value)} className={inputCls + ' min-h-[60px]'} />
        </Field>

        {err && <div className="text-rz-error text-sm">{err}</div>}

        <div className="flex gap-2 pt-2">
          {!confirmDel ? (
            <button type="button" onClick={() => setConfirmDel(true)} className="px-3 py-2 rounded border border-rz-error text-rz-error text-sm">Удалить</button>
          ) : (
            <>
              <button type="button" onClick={doDelete} className="px-3 py-2 rounded bg-rz-error text-rz-white text-sm">Подтвердить</button>
              <button type="button" onClick={() => setConfirmDel(false)} className="px-3 py-2 rounded border border-rz-cream-dark text-rz-cream-dark text-sm">Нет</button>
            </>
          )}
          <div className="flex-1" />
          <button type="button" onClick={onClose} className="px-3 py-2 rounded border border-rz-green-light text-rz-cream-dark">Отмена</button>
          <button type="submit" disabled={saving} className="px-4 py-2 rounded bg-rz-gold text-rz-green font-semibold disabled:opacity-60">
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ============ Helpers ============

const inputCls = "w-full bg-rz-green-mid border border-rz-green-light rounded px-3 py-2 text-rz-cream text-sm focus:outline-none focus:border-rz-gold"

function Field({ label, children }) {
  return (
    <label className="block">
      <div className="text-xs text-rz-cream-dark mb-1">{label}</div>
      {children}
    </label>
  )
}

function Modal({ title, onClose, children }) {
  useEffect(() => {
    const onEsc = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [onClose])

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={onClose}>
      <div
        className="bg-rz-green border border-rz-green-light rounded-t-2xl sm:rounded-xl w-full sm:max-w-lg max-h-[92vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-rz-green border-b border-rz-green-light px-4 py-3 flex items-center justify-between">
          <h2 className="text-rz-gold font-semibold">{title}</h2>
          <button onClick={onClose} className="text-rz-cream-dark text-xl leading-none">×</button>
        </div>
        <div className="px-4 py-4">{children}</div>
      </div>
    </div>
  )
}
