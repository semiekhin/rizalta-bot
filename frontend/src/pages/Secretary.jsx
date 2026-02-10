import React from 'react'

export default function Secretary({ onBack }) {
  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">🗓 Секретарь</h1>
      </div>

      <div className="p-4">
        <div className="bg-rz-green-light rounded-xl p-6 text-center border border-rz-green-mid">
          <p className="text-4xl mb-4">🗓</p>
          <h2 className="text-lg font-bold mb-2">AI-Секретарь</h2>
          <p className="text-rz-cream-dark text-sm mb-6">
            Персональный ежедневник с голосовым вводом.
            Полный функционал доступен в Telegram-боте.
          </p>
          <a
            href="https://t.me/rizalta_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block bg-rz-gold text-rz-green-dark font-bold px-6 py-3 rounded-xl hover:bg-rz-gold-light transition-colors"
          >
            Открыть бот →
          </a>
        </div>
      </div>
    </div>
  )
}
