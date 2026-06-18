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
      <div className="flex items-center justify-between px-4 py-2 border-b border-[rgba(0,243,255,0.2)] bg-[rgba(14,20,26,0.85)] drag-region select-none" style={{ WebkitAppRegion: 'drag', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', borderBottom: '1px solid rgba(0,243,255,0.2)' } as any}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu className="w-5 h-5 text-[#00f3ff] blink" />
          <span className="font-bold text-xs tracking-[0.2em] text-[#00f3ff] font-title" style={{ fontFamily: 'var(--font-title)', letterSpacing: '0.2em' }}>
            JARVIS // TACTICAL COMMAND CENTER // VOICE FIRST OS
          </span>
        </div>

        {/* Window controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', backgroundColor: 'rgba(0,243,255,0.05)', border: '1px solid rgba(0,243,255,0.1)', padding: '2px 8px' }}>
            L-TIME: {systemUptime}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', borderLeft: '1px solid rgba(0,243,255,0.15)', paddingLeft: '12px' }}>
            <button 
              onClick={handleMinimize}
              className="p-1 hover:bg-[rgba(0,243,255,0.15)] text-[#849495] hover:text-[#00f3ff] transition-colors"
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <Minus className="w-4 h-4" />
            </button>
            <button 
              onClick={handleClose}
              className="p-1 hover:bg-[rgba(255,0,60,0.15)] text-[#849495] hover:text-[#ff003c] transition-colors"
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid Workspace */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '12px', padding: '12px', overflow: 'hidden', flex: 1, minHeight: 0 }}>
        
        {/* ================= COLUMN 1: INTEL & BRIEFINGS (Left) ================= */}
        <div style={{ gridColumn: 'span 3', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '4px', minHeight: 0 }}>
          
          {/* System Status Panel */}
          <div className="hud-panel" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '8px' }}>
              <span className="hud-title" style={{ fontSize: '10px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Layers className="w-3.5 h-3.5" /> SYSTEM MATRIX STATUS
              </span>
              <span style={{ fontSize: '9px', color: '#00f3ff', fontWeight: 'bold' }}>NOMINAL</span>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
              <div style={{ padding: '6px', border: '1px solid rgba(0,243,255,0.08)', backgroundColor: 'rgba(0,0,0,0.25)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontSize: '8px', marginBottom: '2px' }}>CORE FREQ</span>
                <span style={{ color: 'white', fontWeight: 'bold' }}>4.2 GHz</span>
              </div>
              <div style={{ padding: '6px', border: '1px solid rgba(0,243,255,0.08)', backgroundColor: 'rgba(0,0,0,0.25)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontSize: '8px', marginBottom: '2px' }}>RAM HEAP</span>
                <span style={{ color: '#00f3ff', fontWeight: 'bold' }}>142 MB</span>
              </div>
              <div style={{ padding: '6px', border: '1px solid rgba(0,243,255,0.08)', backgroundColor: 'rgba(0,0,0,0.25)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontSize: '8px', marginBottom: '2px' }}>AUDIO FEED</span>
                <span style={{ color: 'white', fontWeight: 'bold' }}>48 kHz PCM</span>
              </div>
              <div style={{ padding: '6px', border: '1px solid rgba(0,243,255,0.08)', backgroundColor: 'rgba(0,0,0,0.25)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', fontSize: '8px', marginBottom: '2px' }}>VAD CORE</span>
                <span style={{ color: '#00f3ff', fontWeight: 'bold' }}>RMS ONNX</span>
              </div>
            </div>
          </div>

          {/* Current Focus Panel */}
          <div className="hud-panel" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '8px' }}>
              <span className="hud-title" style={{ fontSize: '10px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu className="w-3.5 h-3.5" /> COGNITIVE FOCUS TELEMETRY
              </span>
              {focusState?.attention_drift_alert && (
                <span style={{ fontSize: '8px', backgroundColor: 'rgba(255,0,60,0.2)', color: '#ff003c', border: '1px solid #ff003c', padding: '1px 4px', fontWeight: 'bold' }} className="blink">DRIFT</span>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>ACTIVE PROJECT:</span>
                <span style={{ color: 'white', fontWeight: 'bold', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '150px' }}>{focusState?.active_project || 'None'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>ACTIVE APP:</span>
                <span style={{ color: 'white', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '150px' }}>{focusState?.active_application || 'None'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>WINDOW LOAD:</span>
                <span style={{ color: '#00f3ff', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '150px' }}>{focusState?.active_window_title || 'None'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(0,243,255,0.08)', paddingTop: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>COGNITIVE LOAD:</span>
                <span style={{ fontWeight: 'bold', textTransform: 'uppercase', color: focusState?.cognitive_load === 'high' ? '#ff003c' : '#00f3ff' }}>
                  {focusState?.cognitive_load || 'low'}
                </span>
              </div>
            </div>
          </div>

          {/* Daily Briefing Panel */}
          <div className="hud-panel" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', flex: 1, minHeight: '180px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '8px' }}>
              <span className="hud-title" style={{ fontSize: '10px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Compass className="w-3.5 h-3.5" /> DAILY STRATEGIC INTEL
              </span>
              <button 
                onClick={fetchDailyBriefing} 
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#00f3ff' }}
                className="hover:text-white transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', fontSize: '11px', fontFamily: 'var(--font-mono)', lineHeight: '1.6', color: '#dde3ec', whiteSpace: 'pre-wrap', paddingRight: '4px' }} className="select-text">
              {dailyBriefing}
            </div>
          </div>

        </div>

        {/* ================= COLUMN 2: VOICE OS HUB & TRANSCRIPTS (Center) ================= */}
        <div style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '12px', minHeight: 0 }}>
          
          {/* Top Panel: Core Voice Orb */}
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1, minHeight: 0 }}>
            <VoiceIndicator />
          </div>

          {/* Bottom Panel: Collapsible Session Log */}
          <div className="hud-panel" style={{ height: '192px', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '8px', marginBottom: '8px' }}>
              <span className="hud-title" style={{ fontSize: '10px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Terminal className="w-3.5 h-3.5" /> CONSOLE SESSION LOG
              </span>
              <button 
                onClick={handleNewSession}
                style={{ fontSize: '9px', border: '1px solid rgba(0,243,255,0.3)', backgroundColor: 'transparent', padding: '2px 8px', color: '#00f3ff', cursor: 'pointer' }}
                className="hover:bg-[rgba(0,243,255,0.1)] transition-colors"
              >
                CLEAR SESSION
              </button>
            </div>

            <div style={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '4px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              {conversations.length === 0 ? (
                <div style={{ textTransform: 'uppercase', color: 'var(--text-muted)', textAlign: 'center', padding: '24px 0' }}>
                  CONSOLE STANDBY. SECURE COMMS LINK ACTIVE.
                </div>
              ) : (
                conversations.slice(0, 5).map((session, idx) => (
                  <div key={session.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px', border: '1px solid rgba(0,243,255,0.06)', backgroundColor: 'rgba(0,0,0,0.15)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <MessageSquare className="w-3.5 h-3.5 text-[#00f3ff]" />
                      <span style={{ color: '#dde3ec', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '280px' }}>{session.title}</span>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '9px', alignSelf: 'center' }}>CHANNEL {idx + 1}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* ================= COLUMN 3: GOALS & ALERTS (Right) ================= */}
        <div style={{ gridColumn: 'span 4', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '4px', minHeight: 0 }}>
          
          {/* Active Goals Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1, minHeight: '180px' }}>
            <AgentStatus plan={activePlan} />
          </div>

          {/* Alerts & Reflections Tabs */}
          <div className="hud-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1, minHeight: '220px', padding: '14px' }}>
            
            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '6px', marginBottom: '10px' }}>
              <button
                onClick={() => setActiveRightTab('alerts')}
                style={{ display: 'flex', flex: 1, paddingBottom: '4px', fontSize: '10px', fontWeight: 'bold', textTransform: 'uppercase', alignItems: 'center', justifyContent: 'center', gap: '6px', background: 'none', border: 'none', borderBottom: activeRightTab === 'alerts' ? '2px solid #00f3ff' : 'none', color: activeRightTab === 'alerts' ? '#00f3ff' : 'var(--text-muted)', cursor: 'pointer' }}
              >
                <ShieldAlert className="w-3.5 h-3.5" /> ALERTS
              </button>
              <button
                onClick={() => setActiveRightTab('reflections')}
                style={{ display: 'flex', flex: 1, paddingBottom: '4px', fontSize: '10px', fontWeight: 'bold', textTransform: 'uppercase', alignItems: 'center', justifyContent: 'center', gap: '6px', background: 'none', border: 'none', borderBottom: activeRightTab === 'reflections' ? '2px solid #00f3ff' : 'none', color: activeRightTab === 'reflections' ? '#00f3ff' : 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Compass className="w-3.5 h-3.5" /> REFLECTIONS
              </button>
            </div>

            {/* Tab Body */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
              {activeRightTab === 'alerts' && <AlertsViewer />}
              {activeRightTab === 'reflections' && <ReflectionViewer />}
            </div>
          </div>

        </div>

      </div>

      {/* Footer Status Bar */}
      <div className="px-4 py-1.5 border-t border-[rgba(0,243,255,0.15)] bg-[rgba(5,10,16,0.95)] flex justify-between items-center text-[9px] text-[var(--text-muted)] font-mono z-10" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '9px', padding: '6px 16px', borderTop: '1px solid rgba(0,243,255,0.15)', backgroundColor: 'rgba(5,10,16,0.95)', fontFamily: 'var(--font-mono)' }}>
        <div>ENVIRONMENT: LOCAL // COMPONENT LOAD: WIDESCREEN HUD CENTER</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span>PORT: 8000 // STABLE</span>
          <span>SECURE LINK ENCRYPTED</span>
        </div>
      </div>
    </div>
  )
}

export default App
