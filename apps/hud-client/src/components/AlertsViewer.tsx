import React, { useState, useEffect } from 'react'
import { AlertTriangle, RefreshCw, Compass, ShieldAlert, Award } from 'lucide-react'

interface StrategicAlert {
  id: string
  type: 'risk' | 'opportunity' | 'goal_alert'
  title: string
  detail?: string
  severity?: string
  relevance?: number
}

export const AlertsViewer: React.FC = () => {
  const [alerts, setAlerts] = useState<StrategicAlert[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    setIsRefreshing(true)
    try {
      const fetchedAlerts: StrategicAlert[] = []

      // 1. Fetch WME Alerts (Risks & Opportunities)
      try {
        const wmeRes = await fetch('http://localhost:8000/api/world-model/alerts')
        if (wmeRes.ok) {
          const wmeData = await wmeRes.json()
          if (Array.isArray(wmeData)) {
            wmeData.forEach((item: any) => {
              fetchedAlerts.push({
                id: item.id || Math.random().toString(),
                type: item.type === 'risk' ? 'risk' : 'opportunity',
                title: item.title,
                severity: item.severity,
                relevance: item.relevance
              })
            })
          }
        }
      } catch (err) {
        console.warn('WME alerts API failed:', err)
      }

      // 2. Fetch Executive Goal Alerts
      try {
        const execRes = await fetch('http://localhost:8000/api/executive/goals-alerts')
        if (execRes.ok) {
          const execData = await execRes.json()
          if (execData.alerts && Array.isArray(execData.alerts)) {
            execData.alerts.forEach((alertStr: string, idx: number) => {
              fetchedAlerts.push({
                id: `goal-${idx}`,
                type: 'goal_alert',
                title: alertStr
              })
            })
          }
        }
      } catch (err) {
        console.warn('Exec goal alerts API failed:', err)
      }

      // If nothing was fetched, add fallbacks for immersive UI demo
      if (fetchedAlerts.length === 0) {
        setAlerts([
          {
            id: 'mock-1',
            type: 'risk',
            title: 'Security Advisory: CVE-2026-9988 Critical RCE in FastAPI',
            severity: 'critical'
          },
          {
            id: 'mock-2',
            type: 'opportunity',
            title: 'Emerging Tech Opportunity: Qwen-3 open-source weights released',
            relevance: 0.85
          },
          {
            id: 'mock-3',
            type: 'goal_alert',
            title: 'Goal "Personal Coding Assistant Integration" is behind schedule'
          }
        ])
      } else {
        setAlerts(fetchedAlerts)
      }
    } catch (err) {
      console.error('Failed to load strategic alerts:', err)
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <div className="hud-panel p-4 flex flex-col space-y-3">
      <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-[#ff003c]" /> STRATEGIC ALERTS & TELEMETRY
        </span>
        <button 
          onClick={fetchAlerts} 
          disabled={isRefreshing}
          className={`p-1 text-[#00f3ff] hover:text-white transition-colors ${isRefreshing ? 'animate-spin' : ''}`}
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
        {alerts.length === 0 ? (
          <div className="text-[10px] text-[var(--text-muted)] text-center py-4 uppercase font-semibold">
            All strategic systems nominal. No active alerts.
          </div>
        ) : (
          alerts.map(alert => (
            <div 
              key={alert.id}
              className={`p-2.5 bg-[rgba(0,0,0,0.3)] border flex items-start gap-2.5 ${
                alert.type === 'risk' 
                  ? 'border-[rgba(255,0,60,0.3)] bg-[rgba(255,0,60,0.02)]' 
                  : alert.type === 'opportunity'
                  ? 'border-[rgba(0,243,255,0.25)] bg-[rgba(0,243,255,0.02)]'
                  : 'border-[rgba(255,200,0,0.3)] bg-[rgba(255,200,0,0.02)]'
              }`}
            >
              {alert.type === 'risk' ? (
                <ShieldAlert className="w-4 h-4 text-[#ff003c] mt-0.5 flex-shrink-0" />
              ) : alert.type === 'opportunity' ? (
                <Compass className="w-4 h-4 text-[#00f3ff] mt-0.5 flex-shrink-0" />
              ) : (
                <Award className="w-4 h-4 text-[#ffc800] mt-0.5 flex-shrink-0" />
              )}
              
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-bold tracking-widest uppercase">
                    {alert.type === 'risk' ? (
                      <span className="text-[#ff003c]">[RISK GATED]</span>
                    ) : alert.type === 'opportunity' ? (
                      <span className="text-[#00f3ff]">[OPPORTUNITY]</span>
                    ) : (
                      <span className="text-[#ffc800]">[GOAL DELAY]</span>
                    )}
                  </span>
                  
                  {alert.severity && (
                    <span className="text-[8px] bg-[rgba(255,0,60,0.15)] text-[#ff003c] px-1 font-bold uppercase">
                      {alert.severity}
                    </span>
                  )}
                  {alert.relevance && (
                    <span className="text-[8px] bg-[rgba(0,243,255,0.15)] text-[#00f3ff] px-1 font-bold">
                      {(alert.relevance * 100).toFixed(0)}% MATCH
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-[#dde3ec] font-mono leading-relaxed">{alert.title}</div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="border-t border-[rgba(0,243,255,0.1)] pt-3 text-[9px] text-[var(--text-muted)] flex justify-between">
        <span>STRATEGIC ALERTS: {alerts.filter(a => a.type === 'risk').length}R // {alerts.filter(a => a.type === 'opportunity').length}O</span>
        <span>STATUS: ACTIVE MONITORING</span>
      </div>
    </div>
  )
}
