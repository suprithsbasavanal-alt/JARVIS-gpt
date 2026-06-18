import React, { useState, useEffect, useRef } from 'react'
import { Send, Cpu, MessageSquare, Terminal } from 'lucide-react'

interface Message {
  id: string
  sender: 'user' | 'jarvis' | 'agent_system'
  content: string
  thought_trace?: string
  created_at: string
}


interface ChatHUDProps {
  onPlanChange: (plan: { goal: string; tasks: any[] } | null) => void
  activeConversationId: string | null
  setActiveConversationId: (id: string | null) => void
}

export const ChatHUD: React.FC<ChatHUDProps> = ({ onPlanChange, activeConversationId, setActiveConversationId }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const pollIntervalRef = useRef<any>(null)

  useEffect(() => {
    fetchHistory()
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [activeConversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const startPolling = (convId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/chat/history/${convId}`)
        const historyData: Message[] = await res.json()
        
        // Find if there is a completed response
        const lastMsg = historyData[historyData.length - 1]
        let isProcessing = false
        if (lastMsg && lastMsg.sender === 'jarvis' && lastMsg.thought_trace) {
          try {
            const trace = JSON.parse(lastMsg.thought_trace)
            if (trace && trace.status === 'processing') {
              isProcessing = true
            }
          } catch (e) {
            // Not JSON or doesn't have status: processing
          }
        }

        setMessages(historyData)

        if (!isProcessing) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }
          setIsLoading(false)
          
          if (lastMsg && lastMsg.sender === 'jarvis' && lastMsg.thought_trace) {
            try {
              const trace = JSON.parse(lastMsg.thought_trace)
              if (trace && (trace.goal || trace.tasks)) {
                onPlanChange(trace)
              }
            } catch (e) {
              // Ignore
            }
          }
        }
      } catch (err) {
        console.error('Error polling chat history:', err)
      }
    }, 2000)
  }

  const fetchHistory = async () => {
    if (!activeConversationId) return
    try {
      const res = await fetch(`http://localhost:8000/api/chat/history/${activeConversationId}`)
      const data = await res.json()
      setMessages(data)

      // Check if last message is processing, if so resume polling
      const lastMsg = data[data.length - 1]
      let isProcessing = false
      if (lastMsg && lastMsg.sender === 'jarvis' && lastMsg.thought_trace) {
        try {
          const trace = JSON.parse(lastMsg.thought_trace)
          if (trace && trace.status === 'processing') {
            isProcessing = true
          }
        } catch (e) {
          // Ignore
        }
      }

      if (isProcessing) {
        setIsLoading(true)
        startPolling(activeConversationId)
      } else {
        setIsLoading(false)
      }
    } catch (err) {
      console.error('Failed to fetch chat logs:', err)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const userText = inputValue
    setInputValue('')
    setIsLoading(true)

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: Math.random().toString(),
      sender: 'user',
      content: userText,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const res = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          conversation_id: activeConversationId
        })
      })

      const data = await res.json()
      let currentConvId = activeConversationId
      if (!activeConversationId && data.conversation_id) {
        setActiveConversationId(data.conversation_id)
        currentConvId = data.conversation_id
      }

      const tempJarvisMsg: Message = {
        id: Math.random().toString(),
        sender: 'jarvis',
        content: data.reply,
        thought_trace: data.plan ? JSON.stringify(data.plan, null, 2) : undefined,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, tempJarvisMsg])

      if (data.plan) {
        onPlanChange(data.plan)
      }

      if (data.status === 'processing' && currentConvId) {
        startPolling(currentConvId)
      } else {
        setIsLoading(false)
      }
    } catch (err) {
      console.error('Failed to communicate with Jarvis backend:', err)
      const errorMsg: Message = {
        id: Math.random().toString(),
        sender: 'agent_system',
        content: 'System communication error. Check if backend server is online.',
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
      setIsLoading(false)
    }
  }

  return (
    <div className="hud-panel flex flex-col h-full rounded-none overflow-hidden" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-[rgba(0,243,255,0.15)] bg-[rgba(0,0,0,0.2)]">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-[#00f3ff]" />
          <span className="hud-title text-sm tracking-wider">COMMS LINK // DIRECT INTERACTION</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#00f3ff] blink"></span>
          <span className="text-[10px] text-[#00f3ff] font-bold">ONLINE</span>
        </div>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {messages.length === 0 && (
          <div className="text-center py-10 text-[var(--text-muted)] text-xs">
            <Cpu className="w-8 h-8 text-[rgba(0,243,255,0.2)] mx-auto mb-2 blink" />
            SECURE QUANTUM TELEMETRY STANDBY. INITIATE INPUT COMMS.
          </div>
        )}
        
        {messages.map(msg => (
          <div 
            key={msg.id} 
            className={`flex flex-col max-w-[85%] ${
              msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
            }`}
          >
            {/* Sender Label */}
            <div className="text-[10px] text-[var(--text-muted)] mb-1 flex items-center gap-1">
              {msg.sender === 'user' ? (
                <>USER // LOGGED_IN</>
              ) : msg.sender === 'jarvis' ? (
                <><span className="text-[#00f3ff]">JARVIS // RESPONDING</span></>
              ) : (
                <><span className="text-[#ff003c]">SYSTEM_AGENT // WARNING</span></>
              )}
            </div>

            {/* Bubble */}
            <div className={`p-3 text-sm ${
              msg.sender === 'user'
                ? 'bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.3)] text-white'
                : msg.sender === 'jarvis'
                ? 'bg-[rgba(0,243,255,0.08)] border border-[rgba(0,243,255,0.25)] text-[#dde3ec]'
                : 'bg-[rgba(255,0,60,0.1)] border border-[rgba(255,0,60,0.3)] text-[#ffb4ab]'
            }`} style={{ borderRadius: '0px', wordBreak: 'break-word' }}>
              {msg.content}
            </div>

            {/* Thought trace toggle if available */}
            {msg.thought_trace && (
              <details className="w-full mt-2 border border-[rgba(0,243,255,0.15)] bg-[rgba(0,0,0,0.3)]">
                <summary className="text-[10px] text-[#00f3ff] p-1.5 cursor-pointer flex items-center gap-1 select-none font-bold">
                  <Terminal className="w-3 h-3" /> REASONING_TRACE.EXE
                </summary>
                <pre className="text-[11px] p-2 text-[var(--text-muted)] overflow-x-auto whitespace-pre-wrap max-h-48 border-t border-[rgba(0,243,255,0.1)] bg-[rgba(0,0,0,0.4)]">
                  {msg.thought_trace}
                </pre>
              </details>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-[rgba(0,243,255,0.15)] bg-[rgba(0,0,0,0.3)] flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="SEND COMMAND OR CHAT..."
          className="hud-input flex-1"
          style={{ flex: 1 }}
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className="hud-button flex items-center justify-center p-2"
          disabled={isLoading}
          style={{ width: '45px', height: '38px' }}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
