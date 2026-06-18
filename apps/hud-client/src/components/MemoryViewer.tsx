import React, { useState, useEffect } from 'react'
import { Database, RefreshCw, Layers } from 'lucide-react'

interface MemoryItem {
  id: string
  entity_key: string
  entity_value: string
  category: string
}

export const MemoryViewer: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [activeCategory, setActiveCategory] = useState<string>('all')

  useEffect(() => {
    fetchMemories()
  }, [activeCategory])

  const fetchMemories = async () => {
    try {
      const url = activeCategory === 'all' 
        ? 'http://localhost:8000/api/memory' 
        : `http://localhost:8000/api/memory?category=${activeCategory}`
      const res = await fetch(url)
      if (!res.ok) throw new Error('API returned non-200 status')
      const data = await res.json()
      setMemories(data)
    } catch (err) {
      console.warn('Failed to fetch memories from backend, using fallback:', err)
      setMemories([
        { id: '1', entity_key: 'user_name', entity_value: 'Suprith', category: 'preference' },
        { id: '2', entity_key: 'active_editor', entity_value: 'VS Code', category: 'preference' },
        { id: '3', entity_key: 'current_project', entity_value: 'JARVIS-gpt Assistant', category: 'project' },
        { id: '4', entity_key: 'demo_date', entity_value: 'June 19, 2026', category: 'tasks' }
      ])
    }
  }

  const filteredMemories = activeCategory === 'all' 
    ? memories 
    : memories.filter(m => m.category === activeCategory)

  return (
    <div className="hud-panel p-4 flex flex-col space-y-3">
      <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-[#00f3ff]" /> LONG-TERM KNOWLEDGE BASE
        </span>
        <button onClick={fetchMemories} className="p-1 text-[#00f3ff] hover:text-white transition-colors">
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      {/* Category selector */}
      <div className="flex gap-2">
        {['all', 'preference', 'project', 'tasks'].map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`text-[9px] px-2 py-0.5 border ${
              activeCategory === cat 
                ? 'border-[#00f3ff] text-white bg-[rgba(0,243,255,0.15)]' 
                : 'border-[rgba(0,243,255,0.15)] text-[var(--text-muted)]'
            } uppercase font-bold`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Memories List */}
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
        {filteredMemories.length === 0 ? (
          <div className="text-[10px] text-[var(--text-muted)] text-center py-4 uppercase font-semibold">
            No memories committed yet.
          </div>
        ) : (
          filteredMemories.map(item => (
            <div 
              key={item.id}
              className="p-2 bg-[rgba(0,0,0,0.2)] border border-[rgba(0,243,255,0.1)] flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-3 h-3 text-[rgba(0,243,255,0.5)]" />
                <span className="text-[#00f3ff] font-bold">{item.entity_key}:</span>
              </div>
              <span className="text-[var(--text-muted)] text-right">{item.entity_value}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
