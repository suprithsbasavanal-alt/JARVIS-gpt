import React, { useState } from 'react'
import { Settings as SettingsIcon, Key, Sliders } from 'lucide-react'

export const Settings: React.FC = () => {
  const [geminiKey, setGeminiKey] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    // In a real app we would send the keys to the backend/store them in local storage.
    // Let's set a saved banner.
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="hud-panel p-4 flex flex-col space-y-4">
      <div className="flex items-center justify-between border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <SettingsIcon className="w-3.5 h-3.5 text-[#00f3ff]" /> SYSTEM PARAMETERS & KEYS
        </span>
      </div>

      <form onSubmit={handleSave} className="space-y-3">
        {/* Gemini Key */}
        <div className="space-y-1">
          <label className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
            <Key className="w-3 h-3 text-[#00f3ff]" /> GEMINI_API_KEY
          </label>
          <input
            type="password"
            value={geminiKey}
            onChange={e => setGeminiKey(e.target.value)}
            placeholder="ENTER GEMINI API KEY..."
            className="hud-input py-1.5 text-xs"
          />
        </div>

        {/* OpenAI Key */}
        <div className="space-y-1">
          <label className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
            <Key className="w-3 h-3 text-[#00f3ff]" /> OPENAI_API_KEY
          </label>
          <input
            type="password"
            value={openaiKey}
            onChange={e => setOpenaiKey(e.target.value)}
            placeholder="ENTER OPENAI API KEY..."
            className="hud-input py-1.5 text-xs"
          />
        </div>

        {/* Anthropic Key */}
        <div className="space-y-1">
          <label className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
            <Key className="w-3 h-3 text-[#00f3ff]" /> ANTHROPIC_API_KEY
          </label>
          <input
            type="password"
            value={anthropicKey}
            onChange={e => setAnthropicKey(e.target.value)}
            placeholder="ENTER ANTHROPIC API KEY..."
            className="hud-input py-1.5 text-xs"
          />
        </div>

        <button type="submit" className="hud-button w-full py-2 mt-2">
          COMMIT PARAMETERS
        </button>

        {saved && (
          <div className="text-[10px] text-center text-[#00f3ff] font-bold blink uppercase">
            SYSTEM KEYS COMMITTED SUCCESSFULLY.
          </div>
        )}
      </form>

      {/* OS details */}
      <div className="border-t border-[rgba(0,243,255,0.1)] pt-3 text-[10px] space-y-1 text-[var(--text-muted)]">
        <div className="flex items-center gap-1.5">
          <Sliders className="w-3.5 h-3.5" />
          <span className="font-bold uppercase">System Environment</span>
        </div>
        <div>OS: macOS (Darwin ARM64)</div>
        <div>Target Server: localhost:8000</div>
        <div>Vibrancy: HUD (Activated)</div>
      </div>
    </div>
  )
}
