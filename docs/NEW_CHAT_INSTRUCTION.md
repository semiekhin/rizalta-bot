# Инструкция для нового чата

Привет! Изучи инструкцию, согласуй задачи и продолжим работу.

⚠️ PROD/DEV НЕ ТРОГАТЬ! РАБОТАЕМ ТОЛЬКО В /opt/webapp/ ⚠️

# RIZALTA Web App v0.2.0

Standalone веб-приложение — fallback если Telegram упадёт в РФ.

## Сервер
```
ssh -p 2222 root@72.56.64.91
```

## Документация (ЧИТАТЬ СНАЧАЛА)
```
cat /opt/webapp/docs/PROJECT_PLAN.md      # План и прогресс
cat /opt/webapp/docs/WEBAPP_CONTEXT.md    # Техконтекст
```

## Прогресс: 60%

✅ Инфраструктура — готово
✅ Frontend UI — 4 страницы готовы  
✅ Деплой — РЕШЕНО (напрямую на сервер, без Cloudflare)
⬜ GPT в чат
⬜ Кнопки (КП, ROI, показы)

## Что работает

**https://webapp.rizaltaservice.ru/** — работает БЕЗ VPN из РФ ✅

## Архитектура (простая, без Cloudflare)
```
Браузер (РФ) → webapp.rizaltaservice.ru → Сервер NL (72.56.64.91)
                                              ↓
                                         Nginx (443)
                                         ├── /assets/* → статика
                                         └── /api/* → localhost:8000 (PROD API)
```

- SSL: Let's Encrypt (автопродление)
- Фреймворк: Preact (19KB вместо React 180KB)
- Cloudflare НЕ используется для webapp

## Ключевые файлы
```
/opt/webapp/frontend/dist/     — Production build
/opt/webapp/frontend/src/      — Исходники React/Preact
/etc/nginx/sites-available/webapp — Конфиг nginx
```

## Запуск/перезапуск
```bash
# Пересборка фронтенда
cd /opt/webapp/frontend && npm run build

# Перезагрузка nginx
nginx -t && nginx -s reload
```

## Следующие задачи

1. GPT в чат — интеграция с OpenAI
2. Кнопка "Получить КП" — генерация PDF
3. Кнопка "Расчёт ROI" — калькулятор доходности
4. Кнопка "Записаться на показ" — форма заявки

## Полезные файлы из бота (для копирования логики)
```
/opt/bot/services/ai_chat.py          — GPT чат
/opt/bot/services/kp_pdf_generator.py — генерация КП
/opt/bot/services/calc_universal.py   — расчёты рассрочки
/opt/bot/handlers/calc_dynamic.py     — ROI расчёты
```

Работаем по командам: ты мне команду, я тебе вывод.
