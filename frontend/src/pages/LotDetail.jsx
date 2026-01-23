import React from 'react'

const formatPrice = (p) => new Intl.NumberFormat('ru-RU').format(p)

export default function LotDetail({ lot, onBack, onChat }) {
  if (!lot) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center pb-20">
        <p className="text-slate-400">Лот не выбран</p>
      </div>
    )
  }

  const pricePerM2 = Math.round(lot.price / lot.area)

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-20">
      {/* Header */}
      <div className="bg-slate-800 px-4 py-3 flex items-center gap-4 sticky top-0 z-40">
        <button onClick={onBack} className="text-slate-400 hover:text-white transition-colors">
          ← Назад
        </button>
        <h1 className="font-bold">Апартамент {lot.code}</h1>
      </div>

      {/* Image */}
      <div className="bg-slate-700 h-52 flex items-center justify-center">
        {lot.layout_url ? (
          <img 
            src={lot.layout_url} 
            alt={`Планировка ${lot.code}`} 
            className="h-full w-full object-contain bg-white"
          />
        ) : (
          <div className="text-center text-slate-400">
            <p className="text-5xl mb-2">🏠</p>
            <p className="text-sm">Планировка {lot.area} м²</p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 space-y-4">
        {/* Price & Status */}
        <div className="flex justify-between items-center">
          <div>
            <p className="text-slate-400 text-sm">Стоимость</p>
            <p className="text-2xl font-bold text-amber-400">{formatPrice(lot.price)} ₽</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            lot.status === 'available' 
              ? 'bg-emerald-500 text-white' 
              : lot.status === 'booked'
                ? 'bg-amber-500 text-black'
                : 'bg-gray-500 text-white'
          }`}>
            {lot.status === 'available' ? '✓ Свободен' : lot.status === 'booked' ? '◐ Бронь' : '✕ Продан'}
          </span>
        </div>

        {/* Specs grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Площадь</p>
            <p className="font-bold text-lg">{lot.area} м²</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Этаж</p>
            <p className="font-bold text-lg">{lot.floor}</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Корпус</p>
            <p className="font-bold text-lg">{lot.building} ({lot.buildingName})</p>
          </div>
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-slate-400 text-xs">Цена за м²</p>
            <p className="font-bold text-lg">{formatPrice(pricePerM2)} ₽</p>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2 pt-2">
          <button className="w-full bg-amber-500 text-black font-bold py-3 rounded-xl hover:bg-amber-400 transition-colors">
            📄 Получить КП
          </button>
          <button className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            📊 Расчёт доходности
          </button>
          <button className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors">
            📅 Записаться на показ
          </button>
          <button 
            onClick={onChat}
            className="w-full bg-slate-700 text-white py-3 rounded-xl hover:bg-slate-600 transition-colors"
          >
            💬 Задать вопрос
          </button>
        </div>
      </div>
    </div>
  )
}
