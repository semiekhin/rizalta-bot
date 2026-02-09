import React, { useState, useRef, useEffect } from 'react'

export default function Chat({ lots, onNavigate }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Здравствуйте! Я AI-консультант RIZALTA. Помогу подобрать апартамент, рассчитать доходность или ответить на вопросы. Что вас интересует?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const quickActions = [
    { label: 'Подобрать апартамент', action: () => onNavigate('catalog') },
    { label: 'Условия рассрочки', query: 'Расскажи про условия рассрочки' },
    { label: 'Доходность', query: 'Какая доходность у апартаментов?' },
  ]

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return

    const userMessage = { role: 'user', content: text }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Пока заглушка — потом подключим GPT
    setTimeout(() => {
      const botResponse = {
        role: 'assistant',
        content: `Спасибо за вопрос! Сейчас чат работает в демо-режиме. В полной версии я смогу:\n\n• Подобрать апартаменты по вашим критериям\n• Рассчитать доходность и сравнить с депозитом\n• Рассказать про условия рассрочки\n• Записать на онлайн-показ\n\nПока можете посмотреть каталог — там ${lots.filter(l => l.status === 'available').length} свободных апартаментов.`
      }
      setMessages(prev => [...prev, botResponse])
      setLoading(false)
    }, 1000)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream flex flex-col">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-3 sticky top-0 z-40">
        <div className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center text-rz-green-dark font-bold">
          R
        </div>
        <div>
          <p className="font-bold">RIZALTA AI</p>
          <p className="text-xs text-rz-success">● Онлайн</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 space-y-4 overflow-auto pb-32">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'gap-2'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0">
                R
              </div>
            )}
            <div className={`max-w-xs rounded-2xl px-4 py-2 ${
              msg.role === 'user'
                ? 'bg-rz-gold text-rz-green-dark rounded-tr-none'
                : 'bg-rz-green-light rounded-tl-none'
            }`}>
              <p className="text-sm whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        ))}

        {/* Quick actions после первого сообщения */}
        {messages.length === 1 && (
          <div className="flex flex-wrap gap-2 pl-10">
            {quickActions.map((qa, i) => (
              <button
                key={i}
                onClick={() => qa.action ? qa.action() : sendMessage(qa.query)}
                className="bg-rz-green-mid text-sm px-3 py-1.5 rounded-full hover:bg-rz-green-light transition-colors text-rz-cream-dark"
              >
                {qa.label}
              </button>
            ))}
          </div>
        )}

        {loading && (
          <div className="flex gap-2">
            <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0">
              R
            </div>
            <div className="bg-rz-green-light rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="fixed bottom-16 left-0 right-0 p-3 bg-rz-green-dark border-t border-rz-green-mid">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Введите сообщение..."
            className="flex-1 bg-rz-green-mid rounded-full px-4 py-2 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center hover:bg-rz-gold-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-rz-green-dark font-bold"
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  )
}
