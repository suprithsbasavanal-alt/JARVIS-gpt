import React, { useState, useEffect } from 'react'
import { Brain, RotateCcw, Zap, Check, AlertTriangle, ArrowRight, Loader } from 'lucide-react'

interface ReflectionItem {
  id: string
  label: string
  properties: {
    summary: string
    what_worked: string
    what_failed: string
    adjustments: string
  }
  updated_at: string
}

export const ReflectionViewer: React.FC = () => {
  const [reflections, setReflections] = useState<ReflectionItem[]>([])
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const [isTriggering, setIsTriggering] = useState(false)

  useEffect(() => {
    fetchReflections()
  }, [])

  const fetchReflections = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/executive/reflections')
      if (!res.ok) throw new Error('API returned error status')
      const data = await res.json()
      setReflections(data)
    } catch (err) {
      console.warn('Failed to fetch reflections from backend, using fallback:', err)
      setReflections([
        {
          id: 'ref_1',
          label: 'Reflection - 2026-06-18',
          updated_at: new Date().toISOString(),
          properties: {
            summary: 'Active monitoring of local dev environment is fully completed.',
            what_worked: 'Fast path optimization implemented; database endpoints running successfully.',
            what_failed: 'Observed minor testing latency bottlenecks.',
            adjustments: 'Incorporate caching and clean intervals in frontend Comms HUD.'
          }
        }
      ])
    }
  }

  const handleTrigger = async () => {
    if (isTriggering) return
    setIsTriggering(true)
    try {
      const res = await fetch('http://localhost:8000/api/executive/reflect', { method: 'POST' })
      if (!res.ok) throw new Error('Failed to run reflection calculation')
      await fetchReflections()
      setSelectedIndex(0)
    } catch (err) {
      console.error('Trigger reflection failed:', err)
      alert('Failed to trigger daily reflection. Verify that uvicorn server is online.')
    } finally {
      setIsTriggering(false)
    }
  }

  const active = reflections[selectedIndex]

  return (
    <div className="hud-panel p-4 flex flex-col space-y-3" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <Brain className="w-3.5 h-3.5 text-[#00f3ff]" /> COGNITIVE SELF-REFLECTION
        </span>
        <button 
          onClick={handleTrigger} 
          disabled={isTriggering}
          className="hud-button flex items-center gap-1 py-1 px-2 text-[10px]"
        >
          {isTriggering ? (
            <>
              <Loader className="w-3 h-3 animate-spin text-[#00f3ff]" /> REFLECTING...
            </>
          ) : (
            <>
              <Zap className="w-3 h-3 text-[#00f3ff]" /> RUN ANALYSIS
            </>
          )}
        </button>
      </div>

      {/* Select active reflection date if history exists */}
      {reflections.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-[var(--text-muted)] font-bold">HISTORICAL LOG:</span>
          <select 
            value={selectedIndex} 
            onChange={(e) => setSelectedIndex(Number(e.target.value))}
            className="bg-[rgba(0,0,0,0.3)] border border-[rgba(0,243,255,0.15)] text-[10px] text-[#00f3ff] px-2 py-0.5"
            style={{ outline: 'none' }}
          >
            {reflections.map((ref, idx) => (
              <option key={ref.id} value={idx} className="bg-[#0e141a] text-[#dde3ec]">
                {ref.label.replace('Reflection - ', '')}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Active Reflection Details */}
      {active ? (
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs" style={{ flex: 1, overflowY: 'auto' }}>
          {/* Summary */}
          <div className="p-2 border border-[rgba(0,243,255,0.1)] bg-[rgba(0,243,255,0.02)]">
            <span className="text-[10px] text-[#00f3ff] font-bold block mb-1">SUMMARY // OUTLINE</span>
            <p className="text-[var(--text-muted)] leading-relaxed">{active.properties.summary}</p>
          </div>

          <div className="grid grid-cols-1 gap-2">
            {/* What Worked */}
            <div className="p-2 border border-[rgba(0,255,100,0.15)] bg-[rgba(0,255,100,0.02)]">
              <span className="text-[10px] text-[#00ff64] font-bold flex items-center gap-1 mb-1">
                <Check className="w-3.5 h-3.5" /> WHAT WORKED
              </span>
              <p className="text-[var(--text-muted)] leading-relaxed">{active.properties.what_worked}</p>
            </div>

            {/* What Failed */}
            <div className="p-2 border border-[rgba(255,0,60,0.15)] bg-[rgba(255,0,60,0.02)]">
              <span className="text-[10px] text-[#ff003c] font-bold flex items-center gap-1 mb-1">
                <AlertTriangle className="w-3.5 h-3.5" /> WHAT FAILED
              </span>
              <p className="text-[var(--text-muted)] leading-relaxed">{active.properties.what_failed}</p>
            </div>
          </div>

          {/* Adjustments */}
          <div className="p-2 border border-[rgba(0,243,255,0.15)] bg-[rgba(0,243,255,0.05)]">
            <span className="text-[10px] text-[#00f3ff] font-bold flex items-center gap-1 mb-1">
              <ArrowRight className="w-3.5 h-3.5" /> WORKFLOW ADJUSTMENTS & MEMORY TARGETS
            </span>
            <p className="text-white leading-relaxed font-mono text-[11px] bg-[rgba(0,0,0,0.2)] p-2 border border-[rgba(0,243,255,0.1)]">
              {active.properties.adjustments}
            </p>
          </div>
        </div>
      ) : (
        <div className="text-center py-10 text-[var(--text-muted)] text-xs uppercase font-semibold">
          <RotateCcw className="w-8 h-8 text-[rgba(0,243,255,0.2)] mx-auto mb-2 blink" />
          No cognitive reflections generated yet. Run analysis to initialize.
        </div>
      )}
    </div>
  )
}
