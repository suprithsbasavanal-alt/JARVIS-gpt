import { useState, useEffect } from 'react'
import { VoiceIndicator } from './components/VoiceIndicator'
import { AgentStatus } from './components/AgentStatus'
import { AlertsViewer } from './components/AlertsViewer'
import { ReflectionViewer } from './components/ReflectionViewer'
import { Cpu, Terminal, MessageSquare, X, Minus, ShieldAlert, Compass, RefreshCw, Layers } from 'lucide-react'

interface ConversationSession {
  id: string
  title: string
  created_at: string
}

interface CognitiveState {
  active_project: string
  active_application: string
  active_window_title: string
  cognitive_load: string
  attention_drift_alert: boolean
}

function App() {
  const [activePlan, setActivePlan] = useState<{ goal: string; tasks: any[] } | null>(null)
  const [conversations, setConversations] = useState<ConversationSession[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [dailyBriefing, setDailyBriefing] = useState<string>('Initializing daily brief...')
  const [focusState, setFocusState] = useState<CognitiveState | null>(null)
  const [systemUptime, setSystemUptime] = useState('00:00:00')
  const [activeRightTab, setActiveRightTab] = useState<'alerts' | 'reflections'>('alerts')

  useEffect(() => {
    fetchConversations()
    fetchDailyBriefing()
    fetchCognitiveState()

    const focusTimer = setInterval(() => {
      fetchCognitiveState()
    }, 5000)

    const uptimeTimer = setInterval(() => {
      const start = new Date()
      // Simulate uptime calculation
      const hours = String(start.getHours()).padStart(2, '0')
      const minutes = String(start.getMinutes()).padStart(2, '0')
      const seconds = String(start.getSeconds()).padStart(2, '0')
      setSystemUptime(`${hours}:${minutes}:${seconds}`)
    }, 1000)

    return () => {
      clearInterval(focusTimer)
      clearInterval(uptimeTimer)
    }
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

  const fetchDailyBriefing = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/executive/briefing/daily')
      if (res.ok) {
        const data = await res.json()
        setDailyBriefing(data.briefing || 'No briefing available.')
      }
    } catch (err) {
      console.warn('Failed to load daily briefing:', err)
      setDailyBriefing('Executive mind offline. Unable to retrieve daily strategic brief.')
    }
  }

  const fetchCognitiveState = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/pcc/cognitive-state')
      if (res.ok) {
        const data = await res.json()
        setFocusState(data)
      }
    } catch (err) {
      console.warn('Failed to fetch cognitive state:', err)
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

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[rgba(5,10,16,0.92)] scanline-animation relative" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Title Bar / Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[rgba(0,243,255,0.2)] bg-[rgba(14,20,26,0.85)] drag-region select-none" style={{ WebkitAppRegion: 'drag' } as any}>
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-[#00f3ff] blink" />
          <span className="font-bold text-xs tracking-[0.2em] text-[#00f3ff] font-title" style={{ fontFamily: 'var(--font-title)' }}>
            JARVIS // TACTICAL COMMAND CENTER // VOICE FIRST OS
          </span>
        </div>

        {/* Window controls */}
        <div className="flex items-center gap-3 no-drag-region" style={{ WebkitAppRegion: 'no-drag' } as any}>
          <div className="text-[10px] text-[var(--text-muted)] font-mono uppercase bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.1)] px-2 py-0.5">
            L-TIME: {systemUptime}
          </div>
          
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

      {/* Main Grid Workspace */}
      <div className="flex-1 grid grid-cols-12 gap-3 p-3 overflow-hidden" style={{ minHeight: 0 }}>
        
        {/* ================= COLUMN 1: INTEL & BRIEFINGS (Left) ================= */}
        <div className="col-span-3 flex flex-col space-y-3 overflow-y-auto pr-1" style={{ minHeight: 0 }}>
          
          {/* System Status Panel */}
          <div className="hud-panel p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2">
              <span className="hud-title text-[10px] tracking-widest flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> SYSTEM MATRIX STATUS
              </span>
              <span className="text-[9px] text-[#00f3ff] font-bold">NOMINAL</span>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
              <div className="p-1.5 border border-[rgba(0,243,255,0.08)] bg-[rgba(0,0,0,0.25)]">
                <span className="text-[var(--text-muted)] block uppercase text-[8px]">CORE FREQ</span>
                <span className="text-white font-bold">4.2 GHz</span>
              </div>
              <div className="p-1.5 border border-[rgba(0,243,255,0.08)] bg-[rgba(0,0,0,0.25)]">
                <span className="text-[var(--text-muted)] block uppercase text-[8px]">RAM HEAP</span>
                <span className="text-[#00f3ff] font-bold">142 MB</span>
              </div>
              <div className="p-1.5 border border-[rgba(0,243,255,0.08)] bg-[rgba(0,0,0,0.25)]">
                <span className="text-[var(--text-muted)] block uppercase text-[8px]">AUDIO FEED</span>
                <span className="text-white font-bold">48 kHz PCM</span>
              </div>
              <div className="p-1.5 border border-[rgba(0,243,255,0.08)] bg-[rgba(0,0,0,0.25)]">
                <span className="text-[var(--text-muted)] block uppercase text-[8px]">VAD CORE</span>
                <span className="text-[#00f3ff] font-bold">RMS ONNX</span>
              </div>
            </div>
          </div>

          {/* Current Focus Panel */}
          <div className="hud-panel p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2">
              <span className="hud-title text-[10px] tracking-widest flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> COGNITIVE FOCUS TELEMETRY
              </span>
              {focusState?.attention_drift_alert && (
                <span className="text-[8px] bg-[rgba(255,0,60,0.2)] text-[#ff003c] border border-[#ff003c] px-1 font-bold animate-pulse">DRIFT</span>
              )}
            </div>

            <div className="space-y-2 text-[11px] font-mono">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">ACTIVE PROJECT:</span>
                <span className="text-white font-bold truncate max-w-[150px]">{focusState?.active_project || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">ACTIVE APP:</span>
                <span className="text-white truncate max-w-[150px]">{focusState?.active_application || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">WINDOW LOAD:</span>
                <span className="text-[#00f3ff] truncate max-w-[150px]">{focusState?.active_window_title || 'None'}</span>
              </div>
              <div className="flex justify-between border-t border-[rgba(0,243,255,0.08)] pt-1.5">
                <span className="text-[var(--text-muted)]">COGNITIVE LOAD:</span>
                <span className={`font-bold uppercase ${focusState?.cognitive_load === 'high' ? 'text-[#ff003c]' : 'text-[#00f3ff]'}`}>
                  {focusState?.cognitive_load || 'low'}
                </span>
              </div>
            </div>
          </div>

          {/* Daily Briefing Panel */}
          <div className="hud-panel p-3.5 flex-1 flex flex-col space-y-2 overflow-hidden" style={{ minHeight: '180px' }}>
            <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2">
              <span className="hud-title text-[10px] tracking-widest flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5" /> DAILY STRATEGIC INTEL
              </span>
              <button onClick={fetchDailyBriefing} className="text-[#00f3ff] hover:text-white transition-colors">
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto text-[11px] font-mono leading-relaxed text-[#dde3ec] pr-1 whitespace-pre-wrap select-text">
              {dailyBriefing}
            </div>
          </div>

        </div>

        {/* ================= COLUMN 2: VOICE OS HUB & TRANSCRIPTS (Center) ================= */}
        <div className="col-span-5 flex flex-col space-y-3" style={{ minHeight: 0 }}>
          
          {/* Top Panel: Core Voice Orb */}
          <div className="flex-1 flex flex-col overflow-hidden" style={{ minHeight: 0 }}>
            <VoiceIndicator />
          </div>

          {/* Bottom Panel: Collapsible Session Log */}
          <div className="hud-panel p-3.5 h-48 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
              <span className="hud-title text-[10px] tracking-widest flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> CONSOLE SESSION LOG
              </span>
              <button 
                onClick={handleNewSession}
                className="text-[9px] border border-[rgba(0,243,255,0.3)] px-2 py-0.5 hover:bg-[rgba(0,243,255,0.1)] text-[#00f3ff]"
              >
                CLEAR SESSION
              </button>
            </div>

            <div className="flex-grow overflow-y-auto space-y-2.5 pr-1 font-mono text-[11px]">
              {conversations.length === 0 ? (
                <div className="text-center text-[var(--text-muted)] uppercase py-6">
                  CONSOLE STANDBY. SECURE COMMS LINK ACTIVE.
                </div>
              ) : (
                conversations.slice(0, 5).map((session, idx) => (
                  <div key={session.id} className="flex justify-between p-1.5 border border-[rgba(0,243,255,0.06)] bg-[rgba(0,0,0,0.15)]">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-3.5 h-3.5 text-[#00f3ff]" />
                      <span className="text-[#dde3ec] truncate max-w-[280px]">{session.title}</span>
                    </div>
                    <span className="text-[var(--text-muted)] text-[9px] self-center">CHANNEL {idx + 1}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* ================= COLUMN 3: GOALS & ALERTS (Right) ================= */}
        <div className="col-span-4 flex flex-col space-y-3 overflow-y-auto pr-1" style={{ minHeight: 0 }}>
          
          {/* Active Goals Panel */}
          <div className="flex-grow flex flex-col overflow-hidden" style={{ minHeight: '180px' }}>
            <AgentStatus plan={activePlan} />
          </div>

          {/* Alerts & Reflections Tabs */}
          <div className="hud-panel p-3.5 flex-grow flex flex-col overflow-hidden" style={{ minHeight: '220px' }}>
            
            {/* Tabs */}
            <div className="flex border-b border-[rgba(0,243,255,0.15)] pb-1.5 mb-2.5">
              <button
                onClick={() => setActiveRightTab('alerts')}
                className={`flex-1 pb-1 text-[10px] font-bold uppercase transition-all tracking-wider flex items-center justify-center gap-1.5 ${
                  activeRightTab === 'alerts' ? 'text-[#00f3ff]' : 'text-[var(--text-muted)] hover:text-white'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" /> ALERTS ({activeRightTab === 'alerts' ? 'ACTIVE' : 'MONITOR'})
              </button>
              <button
                onClick={() => setActiveRightTab('reflections')}
                className={`flex-1 pb-1 text-[10px] font-bold uppercase transition-all tracking-wider flex items-center justify-center gap-1.5 ${
                  activeRightTab === 'reflections' ? 'text-[#00f3ff]' : 'text-[var(--text-muted)] hover:text-white'
                }`}
              >
                <Compass className="w-3.5 h-3.5" /> REFLECTIONS
              </button>
            </div>

            {/* Tab Body */}
            <div className="flex-1 overflow-y-auto pr-1">
              {activeRightTab === 'alerts' && <AlertsViewer />}
              {activeRightTab === 'reflections' && <ReflectionViewer />}
            </div>
          </div>

        </div>

      </div>

      {/* Footer Status Bar */}
      <div className="px-4 py-1.5 border-t border-[rgba(0,243,255,0.15)] bg-[rgba(5,10,16,0.95)] flex justify-between items-center text-[9px] text-[var(--text-muted)] font-mono z-10">
        <div>ENVIRONMENT: LOCAL // COMPONENT LOAD: VOICE CENTER GRID</div>
        <div className="flex items-center gap-3">
          <span>PORT: 8000 // STABLE</span>
          <span>SECURE LINK ENCRYPTED</span>
        </div>
      </div>
    </div>
  )
}

export default App
