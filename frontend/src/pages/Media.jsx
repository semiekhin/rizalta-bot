import React, { useState } from 'react'

const VIDEOS = [
  { key: 'nerealno', label: 'Нереально' },
  { key: 'vesti_kurort', label: 'Вести Курорт' },
  { key: 'bolshoy_altai', label: 'Большой Алтай' },
  { key: 'pravilo_30x30', label: 'Правило 30×30' },
  { key: 'vesti_turpotok', label: 'Вести тур поток' },
  { key: 'mihalkova', label: 'Михалкова — Алтай' },
]

export default function Media({ onBack, onNavigate }) {
  const [playing, setPlaying] = useState(null)

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">🎬 Медиа</h1>
      </div>

      <div className="p-4 space-y-4">
        {/* Link to presentations */}
        <button
          onClick={() => onNavigate('presentations')}
          className="w-full bg-rz-green-light rounded-xl p-4 flex items-center gap-3 border border-rz-green-mid hover:border-rz-gold transition-colors"
        >
          <span className="text-xl">📸</span>
          <span className="text-sm font-medium flex-1 text-left">Презентации (PDF)</span>
          <span className="text-rz-cream-muted">→</span>
        </button>

        {/* Videos */}
        <p className="text-rz-cream-dark text-sm font-medium">🎬 Видеоматериалы RIZALTA</p>

        <div className="space-y-3">
          {VIDEOS.map(v => (
            <div key={v.key} className="bg-rz-green-light rounded-xl overflow-hidden border border-rz-green-mid">
              {playing === v.key ? (
                <div className="relative">
                  <video
                    src={`/api/files/videos/${v.key}`}
                    controls
                    autoPlay
                    className="w-full"
                    onEnded={() => setPlaying(null)}
                  />
                  <button
                    onClick={() => setPlaying(null)}
                    className="absolute top-2 right-2 bg-black/50 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setPlaying(v.key)}
                  className="w-full p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">▶️</span>
                    <span className="text-sm font-medium">{v.label}</span>
                  </div>
                  <span className="bg-rz-gold text-rz-green-dark text-xs font-medium px-3 py-1.5 rounded-lg">
                    Смотреть
                  </span>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
