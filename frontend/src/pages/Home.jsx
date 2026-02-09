import React from 'react'

export default function Home({ stats, onNavigate }) {
  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      {/* Hero */}
      <div className="bg-rz-green px-4 py-8 text-center border-b border-rz-green-light">
        <img src="/images/logo.png" alt="RIZALTA" className="h-12 mx-auto mb-3" />
        <p className="text-rz-cream">Инвестиционная недвижимость</p>
        <p className="text-rz-cream-dark text-sm">Белокуриха, Алтай</p>
        <div className="mt-6 bg-rz-green-light/50 rounded-xl p-4 inline-block">
          <p className="text-4xl font-semibold text-rz-cream">{stats.total || 356}</p>
          <p className="text-sm text-rz-cream-dark">апартаментов</p>
        </div>
      </div>

      {/* Quick actions */}
      <div className="p-4 space-y-3">
        <p className="text-rz-cream-dark text-sm font-medium">Быстрые действия</p>

        <button
          onClick={() => onNavigate('catalog')}
          className="w-full bg-rz-green-light rounded-xl p-4 flex items-center gap-4 border border-rz-green-mid hover:border-rz-gold transition-colors"
        >
          <span className="text-2xl">🏢</span>
          <div className="text-left flex-1">
            <p className="font-medium">Выбрать апартамент</p>
            <p className="text-xs text-rz-cream-dark">Интерактивная шахматка</p>
          </div>
          <span className="text-rz-cream-muted">→</span>
        </button>

        <button
          onClick={() => onNavigate('chat')}
          className="w-full bg-rz-green-light rounded-xl p-4 flex items-center gap-4 border border-rz-green-mid hover:border-rz-gold transition-colors"
        >
          <span className="text-2xl">💬</span>
          <div className="text-left flex-1">
            <p className="font-medium">AI Консультант</p>
            <p className="text-xs text-rz-cream-dark">Ответим на любые вопросы</p>
          </div>
          <span className="text-rz-cream-muted">→</span>
        </button>

        <button
          onClick={() => onNavigate('catalog')}
          className="w-full bg-rz-green-light rounded-xl p-4 flex items-center gap-4 border border-rz-green-mid hover:border-rz-gold transition-colors"
        >
          <span className="text-2xl">📊</span>
          <div className="text-left flex-1">
            <p className="font-medium">Расчёт доходности</p>
            <p className="text-xs text-rz-cream-dark">ROI vs банковский депозит</p>
          </div>
          <span className="text-rz-cream-muted">→</span>
        </button>
      </div>

      {/* Stats */}
      <div className="px-4">
        <div className="bg-rz-green-light rounded-xl p-4">
          <p className="text-rz-cream-dark text-sm mb-3">Сейчас доступно</p>
          <div className="flex justify-between text-center">
            <div>
              <p className="text-2xl font-bold text-rz-success">{stats.available || 0}</p>
              <p className="text-xs text-rz-cream-dark">свободно</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-rz-gold">{stats.booked || 0}</p>
              <p className="text-xs text-rz-cream-dark">бронь</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-rz-cream-muted">{stats.sold || 0}</p>
              <p className="text-xs text-rz-cream-dark">продано</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
