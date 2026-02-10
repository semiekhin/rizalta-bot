import React from 'react'

const MENU_ITEMS = [
  { id: 'lots', icon: '🏢', label: 'Лоты' },
  { id: 'presentations', icon: '📸', label: 'Презентации' },
  { id: 'chat', icon: '💬', label: 'Чат с AI' },
  { id: 'secretary', icon: '🗓', label: 'Секретарь' },
  { id: 'documents', icon: '📄', label: 'Договоры' },
  { id: 'media', icon: '🎬', label: 'Медиа' },
  { id: 'fixation', icon: '📌', label: 'Фиксация' },
  { id: 'news', icon: '📰', label: 'Новости' },
]

export default function Home({ stats, onNavigate }) {
  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      {/* Hero — compact */}
      <div className="bg-rz-gold px-4 py-6 text-center">
        <img src="/images/logo-green.svg" alt="RIZALTA" className="h-10 mx-auto mb-1" />
        <p className="text-rz-green text-sm">Инвестиционная недвижимость</p>
        <p className="text-rz-green/70 text-xs">Белокуриха, Алтай</p>
      </div>

      {/* Menu grid 2x4 */}
      <div className="p-4 grid grid-cols-2 gap-3">
        {MENU_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className="bg-rz-green-light rounded-xl p-4 flex flex-col items-center gap-2 border border-rz-green-mid hover:border-rz-gold transition-colors"
          >
            <span className="text-2xl">{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </button>
        ))}
      </div>

      {/* Booking button */}
      <div className="px-4 mb-4">
        <button
          onClick={() => onNavigate('booking')}
          className="w-full bg-rz-gold text-rz-green-dark font-bold py-3 rounded-xl hover:bg-rz-gold-light transition-colors text-sm"
        >
          ✅ Записаться на онлайн-показ
        </button>
      </div>

      {/* Mini stats */}
      <div className="px-4">
        <div className="bg-rz-green-light rounded-xl p-3 flex justify-around text-center">
          <div>
            <p className="text-lg font-bold text-rz-success">{stats.available || 0}</p>
            <p className="text-xs text-rz-cream-dark">свободно</p>
          </div>
          <div>
            <p className="text-lg font-bold text-rz-gold">{stats.booked || 0}</p>
            <p className="text-xs text-rz-cream-dark">бронь</p>
          </div>
          <div>
            <p className="text-lg font-bold text-rz-cream-muted">{stats.sold || 0}</p>
            <p className="text-xs text-rz-cream-dark">продано</p>
          </div>
        </div>
      </div>
    </div>
  )
}
