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

interface EvaluationItem {
  id: string
  label: string
  properties: {
    planning_grade: number
    planning_critique: string
    research_grade: number
    research_critique: string
    automation_grade: number
    automation_critique: string
    memory_grade: number
    memory_critique: string
    overall_feedback: string
  }
  updated_at: string
}

export const ReflectionViewer: React.FC = () => {
  const [reflections, setReflections] = useState<ReflectionItem[]>([])
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([])
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

    try {
      const res = await fetch('http://localhost:8000/api/executive/evaluations')
      if (!res.ok) throw new Error('API returned error status')
      const data = await res.json()
      setEvaluations(data)
    } catch (err) {
      console.warn('Failed to fetch evaluations, using fallback:', err)
      setEvaluations([
        {
          id: 'eval_1',
          label: 'Evaluation - 2026-06-18',
          updated_at: new Date().toISOString(),
          properties: {
            planning_grade: 9.0,
            planning_critique: 'Task breakdowns follow logical flow, with well-structured dependencies.',
            research_grade: 8.5,
            research_critique: 'Research collector mapped key domains and resolved duplicates correctly.',
            automation_grade: 9.5,
            automation_critique: 'Verified safety classifiers for command execution. No violations.',
            memory_grade: 8.0,
            memory_critique: 'Retrieved preference contexts correctly.',
            overall_feedback: 'Maintain current security and layout heuristics. Continue refining RAG.'
          }
        }
      ])
    }
  }

  const handleTrigger = async () => {
    if (isTriggering) return
    setIsTriggering(true)
    try {
      // Trigger both reflection and evaluation
      await fetch('http://localhost:8000/api/executive/reflect', { method: 'POST' })
      await fetch('http://localhost:8000/api/executive/evaluate', { method: 'POST' })
      await fetchReflections()
      setSelectedIndex(0)
    } catch (err) {
      console.error('Trigger analysis failed:', err)
      alert('Failed to trigger daily reflections and evaluations. Verify backend server is online.')
    } finally {
      setIsTriggering(false)
    }
  }

  const active = reflections[selectedIndex]
  const activeDate = active ? active.label.replace('Reflection - ', '') : ''
  const activeEval = evaluations.find(e => e.label.replace('Evaluation - ', '') === activeDate)

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
              <Loader className="w-3 h-3 animate-spin text-[#00f3ff]" /> ANALYZING...
            </>
          ) : (
            <>
              <Zap className="w-3 h-3 text-[#00f3ff]" /> RUN RETRO
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

      {/* Active Details */}
      {active ? (
        <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs" style={{ flex: 1, overflowY: 'auto' }}>
          
          {/* Agent critic evaluation ratings */}
          {activeEval && (
            <div className="p-2.5 border border-[rgba(0,243,255,0.15)] bg-[rgba(0,243,255,0.02)] space-y-2">
              <span className="text-[10px] text-[#00f3ff] font-bold block mb-1">AGENT CRITIC // METRIC RATINGS</span>
              
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[10px]">
                {/* Planning */}
                <div className="space-y-1">
                  <div className="flex justify-between font-mono text-[#dde3ec]">
                    <span>PLANNING_EFFICACY</span>
                    <span className="text-[#00f3ff]">{activeEval.properties.planning_grade.toFixed(1)}/10</span>
                  </div>
                  <div className="h-1 bg-[rgba(0,243,255,0.15)] relative">
                    <div 
                      className="absolute top-0 left-0 h-full bg-[#00f3ff] shadow-[0_0_4px_#00f3ff]" 
                      style={{ width: `${activeEval.properties.planning_grade * 10}%` }}
                    />
                  </div>
                </div>

                {/* Research */}
                <div className="space-y-1">
                  <div className="flex justify-between font-mono text-[#dde3ec]">
                    <span>RESEARCH_ACCURACY</span>
                    <span className="text-[#00f3ff]">{activeEval.properties.research_grade.toFixed(1)}/10</span>
                  </div>
                  <div className="h-1 bg-[rgba(0,243,255,0.15)] relative">
                    <div 
                      className="absolute top-0 left-0 h-full bg-[#00f3ff] shadow-[0_0_4px_#00f3ff]" 
                      style={{ width: `${activeEval.properties.research_grade * 10}%` }}
                    />
                  </div>
                </div>

                {/* Automation */}
                <div className="space-y-1">
                  <div className="flex justify-between font-mono text-[#dde3ec]">
                    <span>AUTOMATION_SAFETY</span>
                    <span className="text-[#00f3ff]">{activeEval.properties.automation_grade.toFixed(1)}/10</span>
                  </div>
                  <div className="h-1 bg-[rgba(0,243,255,0.15)] relative">
                    <div 
                      className="absolute top-0 left-0 h-full bg-[#00f3ff] shadow-[0_0_4px_#00f3ff]" 
                      style={{ width: `${activeEval.properties.automation_grade * 10}%` }}
                    />
                  </div>
                </div>

                {/* Memory */}
                <div className="space-y-1">
                  <div className="flex justify-between font-mono text-[#dde3ec]">
                    <span>MEMORY_RELEVANCE</span>
                    <span className="text-[#00f3ff]">{activeEval.properties.memory_grade.toFixed(1)}/10</span>
                  </div>
                  <div className="h-1 bg-[rgba(0,243,255,0.15)] relative">
                    <div 
                      className="absolute top-0 left-0 h-full bg-[#00f3ff] shadow-[0_0_4px_#00f3ff]" 
                      style={{ width: `${activeEval.properties.memory_grade * 10}%` }}
                    />
                  </div>
                </div>
              </div>

              {activeEval.properties.overall_feedback && (
                <div className="text-[10px] text-[var(--text-muted)] mt-1 pt-1.5 border-t border-[rgba(0,243,255,0.08)] italic">
                  Feedback: "{activeEval.properties.overall_feedback}"
                </div>
              )}
            </div>
          )}

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
