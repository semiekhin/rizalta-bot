import React from 'react'

export default function Home({ stats, onNavigate }) {
  return (
    <div className="min-h-screen bg-slate-900 text-white pb-20">
      {/* Hero */}
      <div className="bg-gradient-to-b from-amber-500 to-amber-600 px-4 py-8 text-center">
        <h1 className="text-3xl font-bold mb-2">RIZALTA</h1>
        <p className="text-amber-100">Инвестиционная недвижимость</p>
        <p className="text-amber-100 text-sm">Белокуриха, Алтай</p>
        <div className="mt-6 bg-white/20 rounded-xl p-4 inline-block">
          <p className="text-4xl font-bold">{stats.total || 356}</p>
          <p className="text-sm text-amber-100">апартаментов</p>
        </div>
      </div>

      {/* Quick actions */}
      <div className="p-4 space-y-3">
        <p className="text-slate-400 text-sm font-medium">Быстрые действия</p>
        
        <button 
          onClick={() => onNavigate('catalog')}
          className="w-full bg-slate-800 rounded-xl p-4 flex items-center gap-4 border border-slate-700 hover:border-amber-500 transition-colors"
        >
          <span className="text-2xl">🏢</span>
          <div className="text-left flex-1">
            <p className="font-medium">Выбрать апартамент</p>
            <p className="text-xs text-slate-400">Интерактивная шахматка</p>
          </div>
          <span className="text-slate-500">→</span>
        </button>

        <button 
          onClick={() => onNavigate('chat')}
          className="w-full bg-slate-800 rounded-xl p-4 flex items-center gap-4 border border-slate-700 hover:border-amber-500 transition-colors"
        >
          <span className="text-2xl">💬</span>
          <div className="text-left flex-1">
            <p className="font-medium">AI Консультант</p>
            <p className="text-xs text-slate-400">Ответим на любые вопросы</p>
          </div>
          <span className="text-slate-500">→</span>
        </button>

        <button 
          onClick={() => onNavigate('catalog')}
          className="w-full bg-slate-800 rounded-xl p-4 flex items-center gap-4 border border-slate-700 hover:border-amber-500 transition-colors"
        >
          <span className="text-2xl">📊</span>
          <div className="text-left flex-1">
            <p className="font-medium">Расчёт доходности</p>
            <p className="text-xs text-slate-400">ROI vs банковский депозит</p>
          </div>
          <span className="text-slate-500">→</span>
        </button>
      </div>

      {/* Stats */}
      <div className="px-4">
        <div className="bg-slate-800 rounded-xl p-4">
          <p className="text-slate-400 text-sm mb-3">Сейчас доступно</p>
          <div className="flex justify-between text-center">
            <div>
              <p className="text-2xl font-bold text-emerald-400">{stats.available || 0}</p>
              <p className="text-xs text-slate-400">свободно</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-400">{stats.booked || 0}</p>
              <p className="text-xs text-slate-400">бронь</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-500">{stats.sold || 0}</p>
              <p className="text-xs text-slate-400">продано</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
