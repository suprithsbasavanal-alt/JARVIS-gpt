import { useState, useEffect } from 'react'
import { ChatHUD } from './components/ChatHUD'
import { VoiceIndicator } from './components/VoiceIndicator'
import { AgentStatus } from './components/AgentStatus'
import { MemoryViewer } from './components/MemoryViewer'
import { AlertsViewer } from './components/AlertsViewer'
import { ReflectionViewer } from './components/ReflectionViewer'
import { Settings } from './components/Settings'
import { Cpu, Terminal, Plus, MessageSquare, Monitor, X, Minus } from 'lucide-react'

interface ConversationSession {
  id: string
  title: string
  created_at: string
}

function App() {
  const [activePlan, setActivePlan] = useState<{ goal: string; tasks: any[] } | null>(null)
  const [conversations, setConversations] = useState<ConversationSession[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'agents' | 'memory' | 'alerts' | 'reflections' | 'settings'>('agents')

  useEffect(() => {
    fetchConversations()
  }, [activeConversationId])

  const fetchConversations = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/chat/history')
      const data = await res.json()
      setConversations(data)
      if (data.length > 0 && !activeConversationId) {
        setActiveConversationId(data[0].id)
      }
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  const handleNewSession = () => {
    setActiveConversationId(null)
    setActivePlan(null)
  }

  const handleMinimize = () => {
    if ((window as any).electronAPI) {
      (window as any).electronAPI.minimizeWindow()
    }
  }

  const handleClose = () => {
    if ((window as any).electronAPI) {
      (window as any).electronAPI.closeWindow()
    }
  }

  const triggerScreenAnalysis = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/vision/capture', { method: 'POST' })
      const data = await res.json()
      alert(`Screen Analysis:\n\n${data.explanation}`)
    } catch (err) {
      console.error('Screen capture request failed:', err)
      alert('Failed to request screen capture. Check if backend server is online.')
    }
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[rgba(5,10,16,0.85)] scanline-animation relative" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Title Bar / Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[rgba(0,243,255,0.2)] bg-[rgba(14,20,26,0.8)] drag-region select-none" style={{ WebkitAppRegion: 'drag' } as any}>
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-[#00f3ff] blink" />
          <span className="font-bold text-sm tracking-[0.2em] text-[#00f3ff] font-title" style={{ fontFamily: 'var(--font-title)' }}>
            JARVIS // ARTIFICIAL INTELLIGENCE OS
          </span>
        </div>

        {/* Window controls */}
        <div className="flex items-center gap-3 no-drag-region" style={{ WebkitAppRegion: 'no-drag' } as any}>
          <button 
            onClick={triggerScreenAnalysis}
            className="hud-button flex items-center gap-1 py-1 px-2.5 text-[10px]"
          >
            <Monitor className="w-3 h-3" /> CAPTURE SCREEN
          </button>
          
          <div className="flex items-center gap-1.5 border-l border-[rgba(0,243,255,0.15)] pl-3">
            <button 
              onClick={handleMinimize}
              className="p-1 hover:bg-[rgba(0,243,255,0.15)] text-[#849495] hover:text-[#00f3ff] transition-colors"
            >
              <Minus className="w-4 h-4" />
            </button>
            <button 
              onClick={handleClose}
              className="p-1 hover:bg-[rgba(255,0,60,0.15)] text-[#849495] hover:text-[#ff003c] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Dashboard */}
      <div className="flex flex-1 overflow-hidden" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        
        {/* Left Toolbar: Conversation List */}
        <div className="w-64 border-r border-[rgba(0,243,255,0.15)] bg-[rgba(0,0,0,0.4)] flex flex-col p-3 space-y-3" style={{ width: '256px', display: 'flex', flexDirection: 'column' }}>
          <button 
            onClick={handleNewSession}
            className="hud-button w-full flex items-center justify-center gap-2 py-2"
          >
            <Plus className="w-4 h-4" /> NEW COMMS CHANNEL
          </button>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1" style={{ flex: 1, overflowY: 'auto' }}>
            <span className="text-[10px] text-[var(--text-muted)] font-bold tracking-widest block uppercase mb-1">Active Channels</span>
            {conversations.length === 0 ? (
              <div className="text-[10px] text-[var(--text-muted)] text-center py-4 uppercase font-semibold">No active sessions</div>
            ) : (
              conversations.map(session => (
                <button
                  key={session.id}
                  onClick={() => setActiveConversationId(session.id)}
                  className={`w-full text-left p-2.5 border transition-all flex items-center gap-2 text-xs ${
                    activeConversationId === session.id 
                      ? 'border-[#00f3ff] bg-[rgba(0,243,255,0.1)] text-[#00f3ff]' 
                      : 'border-[rgba(0,243,255,0.1)] hover:border-[rgba(0,243,255,0.3)] text-[var(--text-muted)] bg-[rgba(0,0,0,0.2)]'
                  }`}
                  style={{ borderRadius: '0px' }}
                >
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{session.title}</span>
                </button>
              ))
            )}
          </div>

          <div className="p-2 border border-[rgba(0,243,255,0.1)] bg-[rgba(0,0,0,0.3)] text-[10px] text-[var(--text-muted)] space-y-1">
            <div>SECURE DECRYPT // AES-256</div>
            <div>STATUS: ENCRYPTED</div>
          </div>
        </div>

        {/* Center Panel: Primary Chat Terminal */}
        <div className="flex-1 p-3 flex flex-col overflow-hidden" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <ChatHUD 
            onPlanChange={setActivePlan} 
            activeConversationId={activeConversationId}
            setActiveConversationId={setActiveConversationId}
          />
        </div>

        {/* Right Panel: Side telemetry & audio controller */}
        <div className="w-80 border-l border-[rgba(0,243,255,0.15)] bg-[rgba(0,0,0,0.3)] flex flex-col p-3 space-y-3 overflow-y-auto" style={{ width: '320px', display: 'flex', flexDirection: 'column' }}>
          
          {/* Audio Link */}
          <VoiceIndicator />

          {/* Telemetry Tabs */}
          <div className="flex border-b border-[rgba(0,243,255,0.15)]">
            <button
              onClick={() => setActiveTab('agents')}
              className={`flex-1 pb-2 text-[9px] font-bold uppercase transition-all ${
                activeTab === 'agents' ? 'text-[#00f3ff] border-b-2 border-[#00f3ff]' : 'text-[var(--text-muted)]'
              }`}
            >
              AGENTS
            </button>
            <button
              onClick={() => setActiveTab('memory')}
              className={`flex-1 pb-2 text-[9px] font-bold uppercase transition-all ${
                activeTab === 'memory' ? 'text-[#00f3ff] border-b-2 border-[#00f3ff]' : 'text-[var(--text-muted)]'
              }`}
            >
              MEMORY
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`flex-1 pb-2 text-[9px] font-bold uppercase transition-all ${
                activeTab === 'alerts' ? 'text-[#00f3ff] border-b-2 border-[#00f3ff]' : 'text-[var(--text-muted)]'
              }`}
            >
              ALERTS
            </button>
            <button
              onClick={() => setActiveTab('reflections')}
              className={`flex-1 pb-2 text-[9px] font-bold uppercase transition-all ${
                activeTab === 'reflections' ? 'text-[#00f3ff] border-b-2 border-[#00f3ff]' : 'text-[var(--text-muted)]'
              }`}
            >
              REFLECT
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 pb-2 text-[9px] font-bold uppercase transition-all ${
                activeTab === 'settings' ? 'text-[#00f3ff] border-b-2 border-[#00f3ff]' : 'text-[var(--text-muted)]'
              }`}
            >
              SETTINGS
            </button>
          </div>

          <div className="flex-1" style={{ flex: 1 }}>
            {activeTab === 'agents' && <AgentStatus plan={activePlan} />}
            {activeTab === 'memory' && <MemoryViewer />}
            {activeTab === 'alerts' && <AlertsViewer />}
            {activeTab === 'reflections' && <ReflectionViewer />}
            {activeTab === 'settings' && <Settings />}
          </div>
        </div>

      </div>

      {/* Footer bar */}
      <div className="px-4 py-1.5 border-t border-[rgba(0,243,255,0.15)] bg-[rgba(5,10,16,0.95)] flex justify-between items-center text-[10px] text-[var(--text-muted)] font-mono z-10">
        <div>ENVIRONMENT: LOCAL DEVELOPMENT</div>
        <div className="flex items-center gap-1.5">
          <Terminal className="w-3 h-3 text-[#00f3ff]" />
          <span>PORT: 8000 // STABLE CONNECTION</span>
        </div>
      </div>
    </div>
  )
}

export default App
