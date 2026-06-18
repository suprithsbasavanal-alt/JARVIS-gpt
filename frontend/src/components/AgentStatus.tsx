import React, { useState, useEffect } from 'react'
import { CheckCircle2, Circle, AlertCircle, RefreshCw, Cpu } from 'lucide-react'

interface Task {
  id: string
  title: string
  description: string
  status: string
  agent: string
}

interface AgentStatusProps {
  plan: { goal: string; tasks: Task[] } | null
}

export const AgentStatus: React.FC<AgentStatusProps> = ({ plan }) => {
  const [tasks, setTasks] = useState<Task[]>([])

  useEffect(() => {
    if (plan && plan.tasks) {
      setTasks(plan.tasks)
    } else {
      fetchTasks()
    }
  }, [plan])

  const fetchTasks = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/tasks')
      const data = await res.json()
      setTasks(data)
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-[#00f3ff]" />
      case 'in_progress':
        return <RefreshCw className="w-4 h-4 text-[#00f3ff] blink" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-[#ff003c]" />
      default:
        return <Circle className="w-4 h-4 text-[var(--text-muted)]" />
    }
  }

  return (
    <div className="hud-panel p-4 flex flex-col space-y-4">
      <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-[#00f3ff]" /> MULTI-AGENT STATE & TELEMETRY
        </span>
        <button onClick={fetchTasks} className="p-1 text-[#00f3ff] hover:text-white transition-colors">
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      {/* Goal header */}
      {plan?.goal && (
        <div className="p-2 bg-[rgba(0,243,255,0.05)] border border-[rgba(0,243,255,0.15)] text-xs mb-2">
          <span className="text-[#00f3ff] font-bold">ACTIVE GOAL:</span> {plan.goal}
        </div>
      )}

      {/* Tasks Telemetry List */}
      <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
        {tasks.length === 0 ? (
          <div className="text-[10px] text-[var(--text-muted)] text-center py-4 uppercase font-semibold">
            No active agent tasks.
          </div>
        ) : (
          tasks.map(task => (
            <div 
              key={task.id} 
              className="p-2.5 bg-[rgba(0,0,0,0.3)] border border-[rgba(0,243,255,0.1)] flex items-start justify-between gap-3"
            >
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#dde3ec]">{task.title}</span>
                  <span className="hud-tag text-[8px] px-1 py-0.5">{task.agent}</span>
                </div>
                {task.description && (
                  <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{task.description}</p>
                )}
              </div>
              <div className="flex items-center self-center">
                {getStatusIcon(task.status)}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Agent Heartbeats */}
      <div className="border-t border-[rgba(0,243,255,0.1)] pt-3">
        <span className="text-[10px] text-[var(--text-muted)] font-bold tracking-wider uppercase block mb-2">Agent Status Grid</span>
        <div className="grid grid-cols-3 gap-2">
          {['PLANNER', 'RESEARCHER', 'CODER', 'WRITER', 'VISION', 'AUTOMATION'].map(agent => (
            <div key={agent} className="p-1.5 border border-[rgba(0,243,255,0.1)] bg-[rgba(0,0,0,0.2)] text-center">
              <span className="text-[9px] text-[#849495] block">{agent}</span>
              <span className="text-[8px] text-[#00f3ff] font-bold blink">STANDBY</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
