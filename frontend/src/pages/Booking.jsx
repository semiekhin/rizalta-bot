import React, { useState } from 'react'

export default function Booking({ onBack }) {
  const [form, setForm] = useState({ name: '', phone: '', comment: '' })
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()

    const phoneClean = form.phone.replace(/[\s\-\(\)]/g, '')
    if (phoneClean.length < 10) {
      setError('Пожалуйста, введите корректный номер телефона')
      return
    }

    setSending(true)
    setError('')
    try {
      const resp = await fetch('/api/book-showing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      const data = await resp.json()
      if (data.ok) {
        setSent(true)
      } else {
        setError('Ошибка отправки. Попробуйте ещё раз.')
      }
    } catch (err) {
      console.error(err)
      setError('Ошибка соединения. Попробуйте ещё раз.')
    }
    setSending(false)
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">✅ Запись на показ</h1>
      </div>

      <div className="p-4">
        {sent ? (
          <div className="text-center py-12">
            <p className="text-5xl mb-4">✅</p>
            <p className="text-xl font-bold text-rz-success">Заявка отправлена!</p>
            <p className="text-rz-cream-dark mt-2">Мы свяжемся с вами в ближайшее время</p>
            <button
              onClick={onBack}
              className="mt-6 bg-rz-green-light text-rz-cream px-6 py-2 rounded-xl hover:bg-rz-green-mid transition-colors"
            >
              На главную
            </button>
          </div>
        ) : (
          <>
            <p className="text-rz-cream-dark text-sm mb-6">
              Оставьте заявку и мы проведём для вас онлайн-показ апартаментов RIZALTA в Белокурихе
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-rz-cream-dark text-sm">Ваше имя</label>
                <input type="text" required value={form.name}
                  onChange={(e) => setForm({...form, name: e.target.value})}
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold"
                  placeholder="Иван"/>
              </div>
              <div>
                <label className="text-rz-cream-dark text-sm">Телефон</label>
                <input type="tel" required value={form.phone}
                  onChange={(e) => setForm({...form, phone: e.target.value})}
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold"
                  placeholder="+7 999 123-45-67"/>
              </div>
              <div>
                <label className="text-rz-cream-dark text-sm">Комментарий (необязательно)</label>
                <textarea value={form.comment}
                  onChange={(e) => setForm({...form, comment: e.target.value})}
                  className="w-full bg-rz-green-mid rounded-xl px-4 py-3 mt-1 text-rz-cream resize-none outline-none focus:ring-2 focus:ring-rz-gold"
                  rows={3} placeholder="Удобное время для звонка"/>
              </div>
              {error && (
                <p className="text-rz-error text-sm text-center">{error}</p>
              )}
              <button
                type="submit"
                disabled={sending}
                className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors disabled:opacity-50"
              >
                {sending ? 'Отправка...' : 'Отправить заявку'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
