import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, Wifi } from 'lucide-react'

// Downsamples float32 audio data to 16kHz 16-bit PCM
function downsampleBuffer(buffer: Float32Array, inputSampleRate: number, outputSampleRate: number): Int16Array {
  if (inputSampleRate === outputSampleRate) {
    const result = new Int16Array(buffer.length)
    for (let i = 0; i < buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]))
      result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return result
  }
  
  const sampleRateRatio = inputSampleRate / outputSampleRate
  const newLength = Math.round(buffer.length / sampleRateRatio)
  const result = new Int16Array(newLength)
  
  let offsetResult = 0
  let offsetBuffer = 0
  
  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
    let accum = 0
    let count = 0
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i]
      count++
    }
    const s = count > 0 ? accum / count : 0
    result[offsetResult] = Math.max(-32768, Math.min(32767, s < 0 ? s * 32768 : s * 32767))
    offsetResult++
    offsetBuffer = nextOffsetBuffer
  }
  
  return result
}

interface VoiceIndicatorProps {
  onTranscription?: (text: string) => void
  onResponse?: (text: string) => void
}

export const VoiceIndicator: React.FC<VoiceIndicatorProps> = ({ onTranscription, onResponse }) => {
  const [isActive, setIsActive] = useState(true) // Autostart by default
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle')
  const [statusText, setStatusText] = useState('Initializing...')
  const [liveTranscript, setLiveTranscript] = useState('')
  const [jarvisReply, setJarvisReply] = useState('')
  const [latency, setLatency] = useState('0ms')
  
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    if (isActive) {
      connectVoicePipeline()
    } else {
      disconnectVoicePipeline()
    }
    return () => {
      disconnectVoicePipeline()
    }
  }, [isActive])

  // Canvas visualizer rendering loop
  useEffect(() => {
    let active = true
    const draw = () => {
      if (!active) return
      renderOrb()
      animationFrameRef.current = requestAnimationFrame(draw)
    }
    animationFrameRef.current = requestAnimationFrame(draw)
    return () => {
      active = false
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
    }
  }, [voiceState])

  const connectVoicePipeline = async () => {
    setStatusText('Requesting hardware link...')
    try {
      // 1. Get mic access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // 2. Setup audio context (prefer 16000Hz standard, but browser might fallback)
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      })
      audioContextRef.current = audioCtx
      
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      // 3. Setup WebSocket client to the full voice session endpoint
      setStatusText('Establishing secure uplink...')
      const ws = new WebSocket('ws://localhost:8000/api/voice/stream')
      wsRef.current = ws

      ws.onopen = () => {
        setStatusText('Secure uplink active.')
        
        // 4. Create raw audio processor to stream PCM chunks
        const processor = audioCtx.createScriptProcessor(4096, 1, 1)
        source.connect(processor)
        processor.connect(audioCtx.destination)

        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const startTime = performance.now()
            const inputData = e.inputBuffer.getChannelData(0)
            
            // Downsample and convert float32 to int16 PCM bytes
            const downsampled = downsampleBuffer(inputData, audioCtx.sampleRate, 16000)
            const buffer = new ArrayBuffer(downsampled.length * 2)
            const view = new DataView(buffer)
            for (let i = 0; i < downsampled.length; i++) {
              view.setInt16(i * 2, downsampled[i], true)
            }
            
            ws.send(buffer)
            const ms = Math.round(performance.now() - startTime)
            setLatency(`${ms}ms`)
          }
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.voice_state) {
            setVoiceState(data.voice_state)
          }

          switch (data.event) {
            case 'status':
              setStatusText(data.text || 'Online.')
              break
            case 'wake_word_detected':
              setVoiceState('listening')
              setStatusText('Listening...')
              setLiveTranscript('')
              setJarvisReply('Yes?')
              if (onResponse) onResponse('Yes?')
              break
            case 'interrupted':
              setVoiceState('listening')
              setStatusText('Listening (Interrupted)...')
              setJarvisReply('Listening...')
              break
            case 'session_timeout':
              setVoiceState('idle')
              setStatusText('Standby.')
              break
            case 'thinking':
              setVoiceState('thinking')
              setStatusText('Thinking...')
              break
            case 'transcription':
              setLiveTranscript(data.text)
              if (onTranscription) onTranscription(data.text)
              break
            case 'response':
              setVoiceState('speaking')
              setJarvisReply(data.text)
              setStatusText('Speaking...')
              if (onResponse) onResponse(data.text)
              break
            case 'empty_transcription':
              setVoiceState('listening')
              setStatusText('Listening...')
              break
          }
        } catch (e) {
          console.error('Failed to parse websocket package:', e)
        }
      }

      ws.onerror = (err) => {
        console.error('Voice stream websocket error:', err)
        setStatusText('Uplink failed. Retrying...')
      }

      ws.onclose = () => {
        console.log('Voice stream connection closed.')
        if (isActive) {
          // Auto reconnect after 3 seconds
          setTimeout(() => {
            if (isActive) connectVoicePipeline()
          }, 3000)
        }
      }

    } catch (err) {
      console.error('Mic access refused:', err)
      setStatusText('Mic access denied.')
      setIsActive(false)
    }
  }

  const disconnectVoicePipeline = () => {
    setStatusText('Offline.')
    setVoiceState('idle')
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    analyserRef.current = null
  }

  const renderOrb = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    ctx.clearRect(0, 0, width, height)

    const centerX = width / 2
    const centerY = height / 2
    const baseRadius = Math.min(width, height) / 3.8
    const time = Date.now() / 1000

    // Drawing context setup
    ctx.lineCap = 'round'
    
    // Draw outer technical brackets/ring
    ctx.strokeStyle = 'rgba(0, 243, 255, 0.1)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.arc(centerX, centerY, baseRadius * 1.5, 0, Math.PI * 2)
    ctx.stroke()

    // Draw ticks on the outer ring
    for (let i = 0; i < 360; i += 30) {
      const angle = (i * Math.PI) / 180
      const x1 = centerX + Math.cos(angle) * (baseRadius * 1.45)
      const y1 = centerY + Math.sin(angle) * (baseRadius * 1.45)
      const x2 = centerX + Math.cos(angle) * (baseRadius * 1.52)
      const y2 = centerY + Math.sin(angle) * (baseRadius * 1.52)
      ctx.strokeStyle = i % 90 === 0 ? 'rgba(0, 243, 255, 0.4)' : 'rgba(0, 243, 255, 0.15)'
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
    }

    if (voiceState === 'idle') {
      // 1. Idle state: breathing pulse concentric rings
      const pulse = 1 + 0.08 * Math.sin(time * 2.5)
      const radius = baseRadius * pulse

      // Glowing radial gradient
      const gradient = ctx.createRadialGradient(centerX, centerY, radius * 0.1, centerX, centerY, radius * 1.1)
      gradient.addColorStop(0, 'rgba(0, 102, 255, 0.4)')
      gradient.addColorStop(0.5, 'rgba(0, 243, 255, 0.15)')
      gradient.addColorStop(1, 'rgba(5, 10, 16, 0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius * 1.1, 0, Math.PI * 2)
      ctx.fill()

      // Concentric sharp rings
      ctx.lineWidth = 1.5
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.6)'
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
      ctx.stroke()

      ctx.strokeStyle = 'rgba(0, 102, 255, 0.3)'
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius * 0.7, 0, Math.PI * 2)
      ctx.stroke()

    } else if (voiceState === 'listening') {
      // 2. Listening state: circular responsive waveform
      const analyser = analyserRef.current
      const bufferLength = analyser ? analyser.frequencyBinCount : 128
      const dataArray = new Uint8Array(bufferLength)
      if (analyser) {
        analyser.getByteFrequencyData(dataArray)
      }

      // Base glow
      const gradient = ctx.createRadialGradient(centerX, centerY, baseRadius * 0.2, centerX, centerY, baseRadius * 1.3)
      gradient.addColorStop(0, 'rgba(0, 243, 255, 0.35)')
      gradient.addColorStop(0.5, 'rgba(0, 102, 255, 0.15)')
      gradient.addColorStop(1, 'rgba(5, 10, 16, 0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 1.3, 0, Math.PI * 2)
      ctx.fill()

      // Render audio waveform along the circle perimeter
      ctx.lineWidth = 2
      ctx.strokeStyle = '#00f3ff'
      ctx.beginPath()
      
      const numPoints = 120
      for (let i = 0; i <= numPoints; i++) {
        const index = Math.floor((i % numPoints) / numPoints * bufferLength)
        const magnitude = dataArray[index] / 255.0
        const offset = magnitude * 40 * (0.8 + 0.2 * Math.sin(time * 10 + i))
        const angle = (i / numPoints) * Math.PI * 2
        const radius = baseRadius + offset
        
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius
        
        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.closePath()
      ctx.stroke()

      // Inner pulsating core
      ctx.fillStyle = 'rgba(0, 243, 255, 0.8)'
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 0.15 * (1 + 0.1 * Math.sin(time * 20)), 0, Math.PI * 2)
      ctx.fill()

    } else if (voiceState === 'thinking') {
      // 3. Thinking state: rotating holographic dashboard gears
      ctx.lineWidth = 1.5
      
      // Outer ring rotating clockwise
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.8)'
      ctx.save()
      ctx.translate(centerX, centerY)
      ctx.rotate(time * 1.5)
      ctx.beginPath()
      ctx.arc(0, 0, baseRadius * 1.1, 0, Math.PI * 1.6) // Dented arc
      ctx.stroke()
      ctx.restore()

      // Inner ring rotating counter-clockwise
      ctx.strokeStyle = 'rgba(0, 102, 255, 0.6)'
      ctx.save()
      ctx.translate(centerX, centerY)
      ctx.rotate(-time * 2.2)
      // Dashed circle
      ctx.setLineDash([8, 12])
      ctx.beginPath()
      ctx.arc(0, 0, baseRadius * 0.8, 0, Math.PI * 2)
      ctx.stroke()
      ctx.restore()

      // Inner core gear ticks
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.save()
      ctx.translate(centerX, centerY)
      ctx.rotate(time * 0.8)
      for (let i = 0; i < 8; i++) {
        ctx.beginPath()
        ctx.moveTo(0, -baseRadius * 0.4)
        ctx.lineTo(0, -baseRadius * 0.5)
        ctx.stroke()
        ctx.rotate(Math.PI / 4)
      }
      ctx.restore()

      // Core glow
      const pulse = 1 + 0.12 * Math.sin(time * 12)
      const gradient = ctx.createRadialGradient(centerX, centerY, 5, centerX, centerY, baseRadius * 0.4 * pulse)
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0.7)')
      gradient.addColorStop(0.5, 'rgba(0, 243, 255, 0.3)')
      gradient.addColorStop(1, 'rgba(5, 10, 16, 0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, baseRadius * 0.4 * pulse, 0, Math.PI * 2)
      ctx.fill()

    } else if (voiceState === 'speaking') {
      // 4. Speaking state: energetic overlapping sine waves (simulated audio voice)
      const numWaves = 4
      const radius = baseRadius

      // Outer glow
      const gradient = ctx.createRadialGradient(centerX, centerY, radius * 0.2, centerX, centerY, radius * 1.3)
      gradient.addColorStop(0, 'rgba(0, 102, 255, 0.4)')
      gradient.addColorStop(0.6, 'rgba(0, 243, 255, 0.15)')
      gradient.addColorStop(1, 'rgba(5, 10, 16, 0)')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius * 1.3, 0, Math.PI * 2)
      ctx.fill()

      for (let w = 0; w < numWaves; w++) {
        ctx.beginPath()
        ctx.strokeStyle = w === 0 ? '#00f3ff' : w === 1 ? 'rgba(0, 102, 255, 0.7)' : w === 2 ? 'rgba(0, 243, 255, 0.4)' : 'rgba(255, 255, 255, 0.6)'
        ctx.lineWidth = w === 0 ? 2 : 1
        
        const speed = (w + 1.2) * 4.5
        const amplitude = 25 * Math.sin(time * 1.5) * (1 - w * 0.22)
        const frequency = (w + 1) * 0.03

        const numPoints = 80
        for (let i = -numPoints/2; i <= numPoints/2; i++) {
          const pct = i / (numPoints/2)
          // Apply Gaussian envelope to keep wave peaks in the center of the orb
          const envelope = Math.exp(-pct * pct * 3.5)
          const waveVal = Math.sin(i * frequency + time * speed) * amplitude * envelope
          
          const x = centerX + pct * radius * 0.95
          const y = centerY + waveVal

          if (i === -numPoints/2) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }
        ctx.stroke()
      }
    }
  }

  const getStatusColor = () => {
    switch (voiceState) {
      case 'listening': return '#00f3ff'
      case 'thinking': return '#0066ff'
      case 'speaking': return '#ffffff'
      default: return 'var(--text-muted)'
    }
  }

  return (
    <div className="hud-panel" style={{ height: '100%', minHeight: '280px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-between', padding: '12px' }}>
      
      {/* Header telemetry link */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', borderBottom: '1px solid rgba(0,243,255,0.15)', paddingBottom: '8px', marginBottom: '4px' }}>
        <span className="hud-title" style={{ fontSize: '11px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Volume2 className="w-3.5 h-3.5" style={{ color: '#00f3ff' }} /> JARVIS CORE PRESENCE
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Wifi className="w-3 h-3" style={{ color: '#00f3ff' }} />
            <span style={{ fontSize: '9px', color: '#00f3ff', fontFamily: 'var(--font-mono)' }}>{latency}</span>
          </div>
          <span 
            style={{ 
              fontSize: '9px', 
              textTransform: 'uppercase', 
              fontWeight: 'bold', 
              letterSpacing: '0.05em', 
              color: getStatusColor() 
            }}
            className={voiceState === 'thinking' ? 'blink' : ''}
          >
            {voiceState}
          </span>
        </div>
      </div>

      {/* Voice Orb Area */}
      <div style={{ position: 'relative', width: '100%', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px 0' }}>
        <canvas 
          ref={canvasRef} 
          width={300} 
          height={140} 
          style={{ maxWidth: '100%', maxHeight: '130px', filter: 'drop-shadow(0 0 15px rgba(0,243,255,0.15))' }}
        />
        
        {/* Floating Core Status Text overlay */}
        <div style={{ position: 'absolute', bottom: '2px', textAlign: 'center' }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', letterSpacing: '0.15em', textTransform: 'uppercase' }}>
            {statusText}
          </span>
        </div>
      </div>

      {/* Output Panel: Realtime Transcripts display */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(0,243,255,0.12)' }}>
        
        {/* User live speech */}
        <div style={{ padding: '8px 10px', backgroundColor: 'rgba(0,0,0,0.4)', border: '1px solid rgba(0,243,255,0.08)', minHeight: '38px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <span style={{ fontSize: '8px', color: '#00f3ff', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', display: 'block', fontWeight: 'bold', marginBottom: '1px' }}>SPEECH INPUT</span>
          <p style={{ fontSize: '11px', color: '#dde3ec', fontFamily: 'var(--font-mono)', lineHeight: '1.5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {liveTranscript ? liveTranscript : <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Awaiting voice command...</span>}
          </p>
        </div>

        {/* Jarvis reply readout */}
        <div style={{ padding: '8px 10px', backgroundColor: 'rgba(0,243,255,0.04)', border: '1px solid rgba(0,243,255,0.15)', minHeight: '48px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <span style={{ fontSize: '8px', color: '#ffffff', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em', display: 'block', fontWeight: 'bold', marginBottom: '1px' }}>JARVIS OUTPUT</span>
          <p style={{ fontSize: '11px', color: '#00f3ff', fontFamily: 'var(--font-mono)', lineHeight: '1.5', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {jarvisReply ? jarvisReply : <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Standby...</span>}
          </p>
        </div>

        {/* Mic Control toggle */}
        <button
          onClick={() => setIsActive(prev => !prev)}
          className="hud-button"
          style={{ 
            width: '100%', 
            padding: '8px 0', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            gap: '8px', 
            cursor: 'pointer',
            ...(isActive ? { backgroundColor: 'rgba(0,243,255,0.06)', borderColor: '#00f3ff' } : { borderColor: 'rgba(0,243,255,0.2)', color: 'var(--text-muted)' })
          }}
        >
          {isActive ? (
            <>
              <Mic className="w-4 h-4" style={{ color: '#00f3ff' }} />
              <span style={{ fontSize: '12px' }}>UPLINK ACTIVE // PRESS TO MUTE</span>
            </>
          ) : (
            <>
              <MicOff className="w-4 h-4 blink" style={{ color: '#ff003c' }} />
              <span style={{ fontSize: '12px', color: '#ff003c' }}>UPLINK MUTED // CLICK TO CONNECT</span>
            </>
          )}
        </button>
      </div>

    </div>
  )
}

