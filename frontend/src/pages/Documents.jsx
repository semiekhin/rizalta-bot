import React from 'react'

const DOCUMENTS = [
  { key: 'ddu', icon: '📋', label: 'Договор ДДУ' },
  { key: 'arenda', icon: '📋', label: 'Договор с отельным оператором' },
]

export default function Documents({ onBack }) {
  const handleDownload = (key) => {
    const url = `/api/files/documents/${key}`
    window.open(url, '_blank')
  }

  const handleDownloadAll = () => {
    DOCUMENTS.forEach(d => handleDownload(d.key))
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream pb-20">
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-rz-cream-dark hover:text-rz-cream transition-colors">← Назад</button>
        <h1 className="font-bold">📄 Договоры</h1>
      </div>

      <div className="p-4 space-y-3">
        {DOCUMENTS.map(d => (
          <div key={d.key} className="bg-rz-green-light rounded-xl p-4 flex items-center justify-between border border-rz-green-mid">
            <div className="flex items-center gap-3">
              <span className="text-xl">{d.icon}</span>
              <span className="text-sm font-medium">{d.label}</span>
            </div>
            <button
              onClick={() => handleDownload(d.key)}
              className="bg-rz-gold text-rz-green-dark text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-rz-gold-light transition-colors"
            >
              Скачать
            </button>
          </div>
        ))}

        <button
          onClick={handleDownloadAll}
          className="w-full bg-rz-green-light rounded-xl p-4 flex items-center justify-between border border-rz-green-mid"
        >
          <div className="flex items-center gap-3">
            <span className="text-xl">📚</span>
            <span className="text-sm font-medium">Скачать оба</span>
          </div>
          <span className="bg-rz-gold text-rz-green-dark text-xs font-medium px-3 py-1.5 rounded-lg">Скачать</span>
        </button>
      </div>
    </div>
  )
}
