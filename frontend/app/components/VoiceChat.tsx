'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import VoiceBlob from './VoiceBlob'

export default function VoiceChat() {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [volume, setVolume] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [aiResponse, setAiResponse] = useState('')
  const [status, setStatus] = useState('Click to start talking')

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const connectWebSocket = useCallback(() => {
    try {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/chat')
      
      wsRef.current.onopen = () => {
        setIsConnected(true)
        setStatus('Connected - Click to start talking')
      }
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'welcome':
            setStatus('Connected to CSM AI Therapist')
            break
            
          case 'transcription':
            setTranscript(data.text)
            setStatus('Processing your message...')
            break
            
          case 'audio_response':
            setAiResponse(data.text)
            playAudioResponse(data.audio)
            break
            
          case 'text_response':
            setAiResponse(data.text)
            setStatus('Response ready (audio unavailable)')
            break
            
          case 'error':
            console.error('Server error:', data.message)
            setStatus('Error: ' + data.message)
            break
            
          case 'eeg_received':
            console.log('EEG data processed')
            break
        }
      }
      
      wsRef.current.onclose = () => {
        setIsConnected(false)
        setStatus('Disconnected - Click to reconnect')
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setStatus('Connection error - Click to retry')
      }
      
    } catch (error) {
      console.error('Failed to connect:', error)
      setStatus('Connection failed - Click to retry')
    }
  }, [])

  const playAudioResponse = async (audioBase64: string) => {
    try {
      setIsSpeaking(true)
      setStatus('AI is speaking...')
      
      const audioData = atob(audioBase64)
      const audioArray = new Uint8Array(audioData.length)
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i)
      }
      
      const audioBlob = new Blob([audioArray], { type: 'audio/wav' })
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      
      audio.onended = () => {
        setIsSpeaking(false)
        setStatus('Click to continue talking')
        URL.revokeObjectURL(audioUrl)
      }
      
      await audio.play()
    } catch (error) {
      console.error('Audio playback error:', error)
      setIsSpeaking(false)
      setStatus('Audio playback failed')
    }
  }

  const setupAudioAnalysis = async (stream: MediaStream) => {
    audioContextRef.current = new AudioContext()
    analyserRef.current = audioContextRef.current.createAnalyser()
    
    const source = audioContextRef.current.createMediaStreamSource(stream)
    source.connect(analyserRef.current)
    
    analyserRef.current.fftSize = 256
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    
    const updateVolume = () => {
      if (analyserRef.current && isListening) {
        analyserRef.current.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length
        setVolume(average / 255)
        requestAnimationFrame(updateVolume)
      }
    }
    
    updateVolume()
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      })
      
      await setupAudioAnalysis(stream)
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      audioChunksRef.current = []
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        sendAudioToServer(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorderRef.current.start()
      setIsListening(true)
      setStatus('Listening... Click to stop')
      
    } catch (error) {
      console.error('Failed to start recording:', error)
      setStatus('Microphone access denied')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsListening(false)
      setVolume(0)
      setStatus('Processing...')
      
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }

  const sendAudioToServer = async (audioBlob: Blob) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setStatus('Not connected to server')
      return
    }

    try {
      const reader = new FileReader()
      reader.onload = () => {
        const base64Audio = (reader.result as string).split(',')[1]
        wsRef.current?.send(JSON.stringify({
          type: 'audio',
          audio: base64Audio
        }))
      }
      reader.readAsDataURL(audioBlob)
    } catch (error) {
      console.error('Failed to send audio:', error)
      setStatus('Failed to send audio')
    }
  }

  const handleBlobClick = () => {
    if (!isConnected) {
      connectWebSocket()
    } else if (isListening) {
      stopRecording()
    } else if (!isSpeaking) {
      startRecording()
    }
  }

  useEffect(() => {
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [connectWebSocket])

  return (
    <div className="flex flex-col items-center space-y-8">
      {/* Voice Blob */}
      <div 
        className="cursor-pointer transition-transform hover:scale-105"
        onClick={handleBlobClick}
      >
        <VoiceBlob 
          isListening={isListening}
          isSpeaking={isSpeaking}
          volume={volume}
        />
      </div>
      
      {/* Status */}
      <div className="text-center">
        <p className="text-xl text-white mb-2">{status}</p>
        <div className="flex items-center justify-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-sm text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      {/* Transcript and Response */}
      <div className="w-full max-w-2xl space-y-4">
        {transcript && (
          <div className="glass-effect rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">You said:</h3>
            <p className="text-white">{transcript}</p>
          </div>
        )}
        
        {aiResponse && (
          <div className="glass-effect rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">AI Therapist:</h3>
            <p className="text-white">{aiResponse}</p>
          </div>
        )}
      </div>
      
      {/* Instructions */}
      <div className="text-center text-sm text-gray-400 max-w-md">
        <p>Click the orb to start or stop recording. Speak naturally about what's on your mind, and the AI therapist will respond with compassion and understanding.</p>
      </div>
    </div>
  )
}