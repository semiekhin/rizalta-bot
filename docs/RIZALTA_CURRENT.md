# Текущий статус RIZALTA

📅 **Последняя сессия:** 05.02.2026
🏷️ **Версия:** 2.5.9

## ✅ Что сделано (05.02.2026)

### Фикс аренды в "Сравнить с депозитом"
- **Баг:** аренда считалась на захардкоженных 26.8 м² вместо реальной площади лота
- **Решение:** `area_m2` передаётся через callback chain как `area10 = int(area*10)`
- **Обратная совместимость:** старые кнопки без area используют дефолт 26.8

**Изменённые файлы (6):**
- `handlers/compare.py` — добавлен area_m2 во все функции + area10 в callbacks
- `handlers/kp.py` — кнопка "Сравнить с депозитом" передаёт area лота (К1/К2)
- `handlers/corp3.py` — кнопка "Сравнить с депозитом" передаёт area лота (К3)
- `app.py` — парсинг area10 из callback_data с обратной совместимостью
- `services/compare_pdf_generator.py` — area_m2 в generate_compare_pdf + calculate_rizalta
- `services/investment_compare.py` — area_m2 в format_comparison_table

**Callback chain (новый формат):**
```
compare_lot_{code}_{building}_{price_k}_{area10}
  → compare_period_{years}_{amount}_{area10}
    → compare_full_{years}_{amount}_{area10}
      → compare_pdf_{years}_{amount}_{area10}
```

## 🔄 Текущее состояние

- **PROD:** работает ✅ v2.5.9
- **DEV:** работает ✅ v2.5.9
- **Корпус 1 «Family»:** 253 лота (properties.db)
- **Корпус 2 «Business»:** скрыт (ценовая пауза, нет в БД)
- **Корпус 3 «Digital»:** 282 лота (corp3_units.json, whitelist)
- **Mini App Vercel:** работает ✅
- **Watchdog:** работает ✅

## 🔜 Следующие задачи

1. 🟡 **ARCHITECTURE.md + CALLBACKS.md** — карта проекта для LLM-ассистента
2. 🟡 **Деплой ипотечного калькулятора** — готов в DEV
3. 🟡 **Вопрос "11 лет / полный цикл"** — уточнить формулировку (2035 vs 2036)
4. 🟡 **Админ-панель** — типовые операции
5. 🟡 Миграция на российский сервер

## Как вернуть Корпус 2

Когда новые цены будут готовы:
1. Отредактировать `/opt/bot/data/hidden_buildings.json`: `{"hidden": []}`
2. `sudo systemctl restart rizalta-bot`
3. Корпус 2 появится в боте и Mini App автоматически
