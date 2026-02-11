import React, { useState, useEffect, useRef } from 'react'

const DAYS_RU = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
const MONTHS_RU = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
const PRIORITY_COLORS = { high: 'bg-rz-error', normal: 'bg-rz-gold', low: 'bg-rz-cream-muted' }

function formatDate(d) {
  return d.toISOString().split('T')[0]
}

function humanDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return `${d.getDate()} ${MONTHS_RU[d.getMonth()]}`
}

function getDaysArray(centerDate, range = 14) {
  const days = []
  const center = new Date(centerDate + 'T00:00:00')
  for (let i = -3; i <= range; i++) {
    const d = new Date(center)
    d.setDate(d.getDate() + i)
    days.push(formatDate(d))
  }
  return days
}

export default function Secretary({ onBack }) {
  const today = formatDate(new Date())
  const [selectedDate, setSelectedDate] = useState(today)
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [parseMode, setParseMode] = useState(false)
  const [freeText, setFreeText] = useState('')
  const [parsing, setParsing] = useState(false)
  const [form, setForm] = useState({ task: '', date: today, time: '', client_name: '', priority: 'normal' })
  const [saving, setSaving] = useState(false)
  const daysRef = useRef(null)
  const days = getDaysArray(today)

  // Scroll to today on mount
  useEffect(() => {
    const el = daysRef.current
    if (el) {
      const todayBtn = el.querySelector('[data-today]')
      if (todayBtn) {
        todayBtn.scrollIntoView({ inline: 'center', behavior: 'instant' })
      }
    }
  }, [])

  // Fetch tasks when date changes
  useEffect(() => {
    loadTasks(selectedDate)
  }, [selectedDate])

  async function loadTasks(date) {
    setLoading(true)
    try {
      const res = await fetch(`/api/secretary/tasks?date=${date}`)
      const data = await res.json()
      if (data.ok) setTasks(data.tasks)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  async function toggleDone(task) {
    const endpoint = task.done ? 'undone' : 'done'
    try {
      await fetch(`/api/secretary/tasks/${task.id}/${endpoint}`, { method: 'PUT' })
      loadTasks(selectedDate)
    } catch {
      // ignore
    }
  }

  async function handleDelete(taskId) {
    try {
      await fetch(`/api/secretary/tasks/${taskId}`, { method: 'DELETE' })
      loadTasks(selectedDate)
    } catch {
      // ignore
    }
  }

  async function handleParse() {
    if (!freeText.trim()) return
    setParsing(true)
    try {
      const res = await fetch('/api/secretary/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: freeText }),
      })
      const data = await res.json()
      if (data.ok) {
        setForm({
          task: data.task || freeText,
          date: data.date || today,
          time: data.time || '',
          client_name: data.client_name || '',
          priority: data.priority || 'normal',
        })
        setParseMode(false)
      }
    } catch {
      // fallback: just use text as-is
      setForm({ ...form, task: freeText })
      setParseMode(false)
    } finally {
      setParsing(false)
    }
  }

  async function handleSave() {
    if (!form.task.trim()) return
    setSaving(true)
    try {
      await fetch('/api/secretary/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: form.task,
          date: form.date,
          time: form.time || null,
          client_name: form.client_name || null,
          priority: form.priority,
        }),
      })
      setShowCreate(false)
      setForm({ task: '', date: selectedDate, time: '', client_name: '', priority: 'normal' })
      setFreeText('')
      loadTasks(selectedDate)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  const isToday = selectedDate === today

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-24">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
          <h1 className="font-bold">Секретарь</h1>
        </div>
        <button
          onClick={() => { setShowCreate(true); setParseMode(true); setForm({ ...form, date: selectedDate }) }}
          className="w-9 h-9 bg-rz-gold rounded-full flex items-center justify-center text-rz-green-dark font-bold text-xl hover:bg-rz-gold-light transition-colors"
        >
          +
        </button>
      </div>

      {/* Calendar strip */}
      <div ref={daysRef} className="flex gap-1 px-3 py-3 overflow-x-auto scrollbar-hide">
        {days.map(day => {
          const d = new Date(day + 'T00:00:00')
          const isSelected = day === selectedDate
          const isDayToday = day === today
          return (
            <button
              key={day}
              data-today={isDayToday ? '' : undefined}
              onClick={() => setSelectedDate(day)}
              className={`flex flex-col items-center min-w-[48px] py-2 px-1 rounded-xl transition-colors flex-shrink-0 ${
                isSelected
                  ? 'bg-rz-gold text-rz-green-dark'
                  : isDayToday
                    ? 'bg-rz-green-light text-rz-gold border border-rz-gold'
                    : 'text-rz-cream-dark'
              }`}
            >
              <span className="text-[10px] uppercase">{DAYS_RU[d.getDay()]}</span>
              <span className="text-lg font-bold">{d.getDate()}</span>
            </button>
          )
        })}
      </div>

      {/* Date label */}
      <div className="px-4 pb-2">
        <p className="text-sm text-rz-cream-dark">
          {isToday ? 'Сегодня' : humanDate(selectedDate)}
          {tasks.length > 0 && ` — ${tasks.length} задач`}
        </p>
      </div>

      {/* Tasks list */}
      <div className="px-4 space-y-2">
        {loading ? (
          <div className="text-center py-8 text-rz-cream-muted">Загрузка...</div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-3xl mb-3">📋</p>
            <p className="text-rz-cream-muted text-sm">Нет задач на этот день</p>
            <button
              onClick={() => { setShowCreate(true); setParseMode(true); setForm({ ...form, date: selectedDate }) }}
              className="mt-4 text-rz-gold text-sm hover:underline"
            >
              + Добавить задачу
            </button>
          </div>
        ) : (
          tasks.map(task => (
            <div
              key={task.id}
              className={`bg-rz-green-light rounded-xl p-3 flex items-start gap-3 ${task.done ? 'opacity-60' : ''}`}
            >
              {/* Checkbox */}
              <button
                onClick={() => toggleDone(task)}
                className={`w-6 h-6 rounded-md border-2 flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors ${
                  task.done
                    ? 'bg-rz-success border-rz-success text-white'
                    : 'border-rz-cream-muted hover:border-rz-gold'
                }`}
              >
                {task.done && '✓'}
              </button>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${task.done ? 'line-through text-rz-cream-muted' : ''}`}>
                  {task.task}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {task.time && (
                    <span className="text-xs text-rz-cream-muted">{task.time}</span>
                  )}
                  {task.client_name && (
                    <span className="text-xs text-rz-gold">{task.client_name}</span>
                  )}
                  <span className={`w-2 h-2 rounded-full ${PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.normal}`}></span>
                </div>
              </div>

              {/* Delete */}
              <button
                onClick={() => handleDelete(task.id)}
                className="text-rz-cream-muted hover:text-rz-error text-sm flex-shrink-0 px-1"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      {/* Create task modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-end">
          <div className="w-full bg-rz-green-dark rounded-t-2xl p-4 pb-24 max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-lg">Новая задача</h2>
              <button
                onClick={() => { setShowCreate(false); setParseMode(false); setFreeText('') }}
                className="text-rz-cream-muted hover:text-rz-cream text-xl"
              >
                ✕
              </button>
            </div>

            {parseMode ? (
              <>
                <p className="text-sm text-rz-cream-dark mb-2">Опишите задачу своими словами:</p>
                <textarea
                  value={freeText}
                  onChange={e => setFreeText(e.target.value)}
                  placeholder="Завтра в 10 позвонить Иванову по поводу просмотра..."
                  rows={3}
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-3 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted resize-none mb-3"
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleParse}
                    disabled={!freeText.trim() || parsing}
                    className="flex-1 bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl disabled:opacity-50 transition-colors hover:bg-rz-gold-light"
                  >
                    {parsing ? 'Анализирую...' : 'Распознать'}
                  </button>
                  <button
                    onClick={() => { setParseMode(false); setForm({ ...form, task: freeText || '' }) }}
                    className="px-4 py-3 text-rz-cream-dark text-sm rounded-xl border border-rz-green-mid hover:border-rz-cream-muted transition-colors"
                  >
                    Вручную
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">Задача</label>
                    <input
                      value={form.task}
                      onChange={e => setForm({ ...form, task: e.target.value })}
                      placeholder="Описание задачи..."
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                      autoFocus
                    />
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="text-xs text-rz-cream-dark mb-1 block">Дата</label>
                      <input
                        type="date"
                        value={form.date}
                        onChange={e => setForm({ ...form, date: e.target.value })}
                        className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold"
                      />
                    </div>
                    <div className="w-28">
                      <label className="text-xs text-rz-cream-dark mb-1 block">Время</label>
                      <input
                        type="time"
                        value={form.time}
                        onChange={e => setForm({ ...form, time: e.target.value })}
                        className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">Клиент</label>
                    <input
                      value={form.client_name}
                      onChange={e => setForm({ ...form, client_name: e.target.value })}
                      placeholder="Имя клиента (опционально)"
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">Приоритет</label>
                    <div className="flex gap-2">
                      {[['low', 'Низкий'], ['normal', 'Обычный'], ['high', 'Важный']].map(([val, label]) => (
                        <button
                          key={val}
                          onClick={() => setForm({ ...form, priority: val })}
                          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-colors ${
                            form.priority === val
                              ? val === 'high' ? 'bg-rz-error text-white' : val === 'low' ? 'bg-rz-cream-muted text-rz-green-dark' : 'bg-rz-gold text-rz-green-dark'
                              : 'bg-rz-green-mid text-rz-cream-dark'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleSave}
                  disabled={!form.task.trim() || saving}
                  className="w-full mt-4 bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl disabled:opacity-50 transition-colors hover:bg-rz-gold-light"
                >
                  {saving ? 'Сохраняю...' : 'Создать задачу'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
