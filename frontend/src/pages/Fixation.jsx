import React, { useState, useEffect } from 'react'

export default function Fixation({ onBack }) {
  const [authState, setAuthState] = useState('loading') // loading | login | authenticated
  const [agentName, setAgentName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  // Fixation form
  const [clientName, setClientName] = useState('')
  const [clientPhone, setClientPhone] = useState('')
  const [comment, setComment] = useState('')
  const [fixLoading, setFixLoading] = useState(false)
  const [fixResult, setFixResult] = useState(null) // {ok, message}
  const [phoneError, setPhoneError] = useState(null)

  // Check auth status on mount
  useEffect(() => {
    checkStatus()
  }, [])

  async function checkStatus() {
    try {
      const res = await fetch('/api/fixation/status')
      const data = await res.json()
      if (data.authenticated) {
        setAgentName(data.agent_name || '')
        setAuthState('authenticated')
      } else {
        setAuthState('login')
      }
    } catch {
      setAuthState('login')
    }
  }

  async function handleLogin(e) {
    e.preventDefault()
    if (!phone.trim() || !password.trim()) return
    setAuthLoading(true)
    setAuthError(null)

    try {
      const res = await fetch('/api/fixation/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      })
      const data = await res.json()
      if (data.ok) {
        setAgentName(data.agent_name || phone)
        setAuthState('authenticated')
        setPassword('')
      } else {
        setAuthError(data.message || 'Ошибка авторизации')
      }
    } catch {
      setAuthError('Сервис недоступен')
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleLogout() {
    try {
      await fetch('/api/fixation/logout', { method: 'POST' })
    } catch {
      // ignore
    }
    setAuthState('login')
    setAgentName('')
    setPhone('')
    setFixResult(null)
  }

  function validatePhone() {
    const clean = clientPhone.replace(/\D/g, '')
    if (clean.length < 10) {
      setPhoneError('Минимум 10 цифр')
      return false
    }
    setPhoneError(null)
    return true
  }

  async function handleFixation(e) {
    e.preventDefault()
    if (!clientName.trim() || !clientPhone.trim()) return
    if (!validatePhone()) return

    setFixLoading(true)
    setFixResult(null)

    try {
      const res = await fetch('/api/fixation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_name: clientName,
          client_phone: clientPhone,
          comment,
        }),
      })
      const data = await res.json()
      setFixResult(data)
      if (data.ok) {
        setClientName('')
        setClientPhone('')
        setComment('')
      }
    } catch {
      setFixResult({ ok: false, message: 'Ошибка связи с сервером' })
    } finally {
      setFixLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-24">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">Фиксация клиента</h1>
      </div>

      <div className="p-4">
        {/* Loading state */}
        {authState === 'loading' && (
          <div className="text-center py-12 text-rz-cream-muted">Проверка авторизации...</div>
        )}

        {/* Login form */}
        {authState === 'login' && (
          <div className="bg-rz-green-light rounded-xl p-5 border border-rz-green-mid">
            <h2 className="font-bold text-lg mb-1">Вход в ri.rclick.ru</h2>
            <p className="text-rz-cream-dark text-sm mb-4">
              Для фиксации клиентов необходимо авторизоваться
            </p>

            <form onSubmit={handleLogin} className="space-y-3">
              <div>
                <label className="text-xs text-rz-cream-dark mb-1 block">Телефон</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="+7 (999) 123-45-67"
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs text-rz-cream-dark mb-1 block">Пароль</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Пароль"
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                />
              </div>

              {authError && (
                <div className="bg-rz-error/20 text-rz-error rounded-lg px-4 py-2 text-sm">
                  {authError}
                </div>
              )}

              <button
                type="submit"
                disabled={authLoading || !phone.trim() || !password.trim()}
                className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl disabled:opacity-50 transition-colors hover:bg-rz-gold-light"
              >
                {authLoading ? 'Вхожу...' : 'Войти'}
              </button>
            </form>
          </div>
        )}

        {/* Authenticated — fixation form */}
        {authState === 'authenticated' && (
          <>
            {/* Status bar */}
            <div className="bg-rz-green-light rounded-xl p-4 mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-rz-cream-dark">Авторизован как</p>
                <p className="font-bold text-rz-gold">{agentName}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-rz-cream-muted text-sm hover:text-rz-error transition-colors"
              >
                Выйти
              </button>
            </div>

            {/* Success state */}
            {fixResult?.ok ? (
              <div className="bg-rz-green-light rounded-xl p-6 text-center border border-rz-success">
                <p className="text-3xl mb-3">✅</p>
                <h3 className="font-bold text-lg mb-2">Фиксация создана</h3>
                <p className="text-rz-cream-dark text-sm mb-4">{fixResult.message}</p>
                {fixResult.fixation_id && (
                  <p className="text-xs text-rz-cream-muted mb-4">ID: {fixResult.fixation_id}</p>
                )}
                <button
                  onClick={() => setFixResult(null)}
                  className="bg-rz-gold text-rz-green-dark font-bold px-6 py-3 rounded-xl hover:bg-rz-gold-light transition-colors"
                >
                  Ещё фиксация
                </button>
              </div>
            ) : (
              /* Fixation form */
              <div className="bg-rz-green-light rounded-xl p-5 border border-rz-green-mid">
                <h2 className="font-bold text-lg mb-4">Новая фиксация</h2>

                <form onSubmit={handleFixation} className="space-y-3">
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">ФИО клиента *</label>
                    <input
                      value={clientName}
                      onChange={e => setClientName(e.target.value)}
                      placeholder="Иванов Иван Иванович"
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">Телефон клиента *</label>
                    <input
                      type="tel"
                      value={clientPhone}
                      onChange={e => { setClientPhone(e.target.value); setPhoneError(null) }}
                      placeholder="+7 (999) 123-45-67"
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
                    />
                    {phoneError && (
                      <p className="text-rz-error text-xs mt-1">{phoneError}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-xs text-rz-cream-dark mb-1 block">Комментарий</label>
                    <textarea
                      value={comment}
                      onChange={e => setComment(e.target.value)}
                      placeholder="Дополнительная информация..."
                      rows={2}
                      className="w-full bg-rz-green-mid rounded-xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted resize-none"
                    />
                  </div>

                  {fixResult && !fixResult.ok && (
                    <div className="bg-rz-error/20 text-rz-error rounded-lg px-4 py-2 text-sm">
                      {fixResult.message}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={fixLoading || !clientName.trim() || !clientPhone.trim()}
                    className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl disabled:opacity-50 transition-colors hover:bg-rz-gold-light"
                  >
                    {fixLoading ? 'Отправляю...' : 'Отправить фиксацию'}
                  </button>
                </form>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
