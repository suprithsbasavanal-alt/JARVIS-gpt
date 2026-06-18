import React, { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2 } from 'lucide-react'

export const VoiceIndicator: React.FC = () => {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    if (isListening) {
      startRecording()
    } else {
      stopRecording()
    }
    return () => {
      stopRecording()
    }
  }, [isListening])

  const startRecording = async () => {
    try {
      // 1. Get User Media Stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      // 2. Set up Web Audio API Analyser for Waveform
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
      audioContextRef.current = audioCtx
      
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      // 3. Set up WebSocket Connection
      const ws = new WebSocket('ws://localhost:8000/api/audio/stream')
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.text) {
            setTranscript(data.text)
          }
        } catch (e) {
          console.error('Failed to parse websocket message:', e)
        }
      }

      ws.onopen = () => {
        console.log('Voice stream connection opened.')
        // Basic Audio Stream Node to feed WebSocket (mock/simplified PCM push)
        const processor = audioCtx.createScriptProcessor(4096, 1, 1)
        source.connect(processor)
        processor.connect(audioCtx.destination)

        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0)
            // Convert Float32Array to 16-bit PCM bytes
            const buffer = new ArrayBuffer(inputData.length * 2)
            const view = new DataView(buffer)
            for (let i = 0; i < inputData.length; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]))
              view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
            }
            ws.send(buffer)
          }
        }
      }

      // Start rendering waveform canvas
      drawWaveform()
    } catch (err) {
      console.error('Microphone access refused:', err)
      setIsListening(false)
    }
  }

  const stopRecording = () => {
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
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
    analyserRef.current = null
  }

  const drawWaveform = () => {
    const canvas = canvasRef.current
    const analyser = analyserRef.current
    if (!canvas || !analyser) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const draw = () => {
      if (!isListening) return
      animationFrameRef.current = requestAnimationFrame(draw)

      analyser.getByteTimeDomainData(dataArray)

      ctx.fillStyle = 'rgba(5, 10, 16, 0.4)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.lineWidth = 2
      ctx.strokeStyle = '#00f3ff'
      ctx.beginPath()

      const sliceWidth = canvas.width / bufferLength
      let x = 0

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * canvas.height) / 2

        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }

        x += sliceWidth
      }

      ctx.lineTo(canvas.width, canvas.height / 2)
      ctx.stroke()
    }

    draw()
  }

  return (
    <div className="hud-panel p-4 flex flex-col items-center justify-center space-y-4">
      <div className="flex items-center justify-between w-full border-b border-[rgba(0,243,255,0.15)] pb-2 mb-2">
        <span className="hud-title text-xs tracking-widest flex items-center gap-1.5">
          <Volume2 className="w-3.5 h-3.5 text-[#00f3ff]" /> AUDIO TELEMETRY LINK
        </span>
        <span className="text-[10px] text-[#00f3ff] font-bold">MODE: {isListening ? 'STREAMING' : 'STANDBY'}</span>
      </div>

      {/* Waveform / Visualizer */}
      <div className="relative w-full h-24 bg-[rgba(0,0,0,0.4)] border border-[rgba(0,243,255,0.1)] flex items-center justify-center overflow-hidden">
        {isListening ? (
          <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" width={400} height={100} />
        ) : (
          <span className="text-[10px] text-[var(--text-muted)] tracking-widest uppercase font-semibold">Voice Input Offline</span>
        )}
      </div>

      {/* Controls */}
      <div className="flex flex-col items-center w-full space-y-2">
        <button
          onClick={() => setIsListening(prev => !prev)}
          className={`hud-button w-full py-3 flex items-center justify-center gap-2 ${
            isListening ? 'bg-[rgba(0,243,255,0.15)] border-white text-white' : ''
          }`}
        >
          {isListening ? (
            <>
              <MicOff className="w-4 h-4 text-[#ff003c] blink" />
              <span>TERMINATE AUDIO FEED</span>
            </>
          ) : (
            <>
              <Mic className="w-4 h-4 text-[#00f3ff]" />
              <span>INITIATE VOICE CONNECT</span>
            </>
          )}
        </button>
        {transcript && (
          <div className="w-full p-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(0,243,255,0.1)] text-[11px] text-[#dde3ec] max-h-16 overflow-y-auto">
            <span className="text-[#00f3ff] font-bold">TRANSCRIPT: </span>{transcript}
          </div>
        )}
      </div>
    </div>
  )
}
