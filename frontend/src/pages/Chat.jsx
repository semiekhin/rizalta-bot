import React, { useState, useRef, useEffect, useCallback } from 'react'

const WELCOME_MSG = {
  role: 'assistant',
  content: 'Здравствуйте! Я AI-консультант RIZALTA. Помогу подобрать апартамент, рассчитать доходность или ответить на вопросы об инвестициях. Что вас интересует?'
}

// Map navigate "to" paths to internal screen names
function resolveNavigation(to, onNavigate) {
  // Parse path like /catalog/А209?modal=roi or /lots or /booking
  const [path, query] = to.split('?')
  const segments = path.split('/').filter(Boolean)

  const screen = segments[0]
  const screenMap = {
    lots: 'lots',
    catalog: 'lots',
    booking: 'booking',
    presentations: 'presentations',
    documents: 'documents',
    media: 'media',
    news: 'news',
    secretary: 'secretary',
    fixation: 'fixation',
  }

  const targetScreen = screenMap[screen]
  if (targetScreen) {
    onNavigate(targetScreen)
  }
}

export default function Chat({ lots, onNavigate }) {
  const [messages, setMessages] = useState([WELCOME_MSG])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const abortRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }
  }, [input])

  const sendMessage = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || isStreaming) return

    setError(null)
    setInput('')

    // Add user message
    const userMsg = { role: 'user', content: trimmed }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setIsStreaming(true)

    // Prepare history
    const history = newMessages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({ role: m.role, content: m.content }))
      .slice(0, -1)

    // Add placeholder assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
        signal: controller.signal,
      })

      if (response.status === 429) {
        setError('Слишком много запросов. Подождите минуту.')
        setMessages(prev => prev.slice(0, -1))
        setIsStreaming(false)
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const contentType = response.headers.get('content-type') || ''

      // Action response (JSON)
      if (contentType.includes('application/json')) {
        const data = await response.json()
        if (data.type === 'action') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: 'assistant',
              content: data.message,
              actions: data.actions,
            }
            return updated
          })
          setIsStreaming(false)
          return
        }
      }

      // SSE streaming response
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6)
          if (!jsonStr) continue

          try {
            const event = JSON.parse(jsonStr)
            if (event.type === 'token') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    content: last.content + event.content,
                  }
                }
                return updated
              })
            } else if (event.type === 'actions') {
              // Action buttons appended after AI streaming
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    actions: event.actions,
                  }
                }
                return updated
              })
            } else if (event.type === 'error') {
              setError(event.content)
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError('Не удалось связаться с AI. Попробуйте позже.')
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant' && !last.content) {
            return prev.slice(0, -1)
          }
          return prev
        })
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const quickActions = [
    { label: 'Подобрать апартамент', action: () => onNavigate('lots') },
    { label: 'Доходность', query: 'Какая доходность у апартаментов RIZALTA?' },
    { label: 'Условия рассрочки', query: 'Расскажи про условия рассрочки' },
  ]

  return (
    <div className="min-h-screen bg-rz-green text-rz-cream flex flex-col">
      {/* Header */}
      <div className="bg-rz-green-light px-4 py-3 flex items-center gap-3 sticky top-0 z-40">
        <div className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center text-rz-green-dark font-bold">
          R
        </div>
        <div>
          <p className="font-semibold">AI Консультант</p>
          <p className="text-xs text-rz-success">● Онлайн</p>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 p-4 space-y-4 overflow-auto pb-36">
        {messages.map((msg, i) => (
          <div key={i}>
            <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'gap-2'}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0 mt-1">
                  R
                </div>
              )}
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                msg.role === 'user'
                  ? 'bg-rz-gold text-rz-green-dark rounded-tr-none'
                  : 'bg-rz-green-light rounded-tl-none'
              }`}>
                <p className="text-sm whitespace-pre-line leading-relaxed">{msg.content}</p>
              </div>
            </div>

            {/* Action buttons */}
            {msg.actions && msg.actions.length > 0 && (
              <div className="flex flex-wrap gap-2 pl-10 mt-2">
                {msg.actions.map((action, j) => (
                  <button
                    key={j}
                    onClick={() => {
                      if (action.type === 'navigate') {
                        resolveNavigation(action.to, onNavigate)
                      }
                    }}
                    className="bg-transparent border border-rz-gold text-rz-gold text-sm px-4 py-2 rounded-xl hover:bg-rz-gold hover:text-rz-green-dark transition-colors font-medium"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Quick actions after welcome */}
        {messages.length === 1 && !isStreaming && (
          <div className="flex flex-wrap gap-2 pl-10">
            {quickActions.map((qa, i) => (
              <button
                key={i}
                onClick={() => qa.action ? qa.action() : sendMessage(qa.query)}
                className="bg-rz-green-mid text-sm px-3 py-1.5 rounded-full hover:bg-rz-green-light transition-colors text-rz-cream-dark border border-rz-green-light"
              >
                {qa.label}
              </button>
            ))}
          </div>
        )}

        {/* Typing indicator */}
        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="flex gap-2">
            <div className="w-8 h-8 bg-rz-gold rounded-full flex items-center justify-center text-sm text-rz-green-dark font-bold flex-shrink-0">
              R
            </div>
            <div className="bg-rz-green-light rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-rz-cream-muted rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="ml-10 bg-rz-error/20 text-rz-error rounded-lg px-4 py-2 text-sm">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="fixed bottom-16 left-0 right-0 p-3 bg-rz-green-dark border-t border-rz-green-mid pb-4">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите сообщение..."
            rows={1}
            className="flex-1 bg-rz-green-mid rounded-2xl px-4 py-2.5 text-sm text-rz-cream outline-none focus:ring-2 focus:ring-rz-gold placeholder:text-rz-cream-muted resize-none max-h-[120px]"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="w-10 h-10 bg-rz-gold rounded-full flex items-center justify-center hover:bg-rz-gold-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-rz-green-dark font-bold flex-shrink-0"
          >
            ↑
          </button>
        </form>
      </div>
    </div>
  )
}
