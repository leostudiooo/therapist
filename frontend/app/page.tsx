'use client'

import { useState, useEffect, useRef } from 'react'
import VoiceBlob from './components/VoiceBlob'
import VoiceChat from './components/VoiceChat'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="w-full max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-light text-white mb-2">AI Therapist</h1>
          <p className="text-lg text-gray-300">Your compassionate voice companion</p>
        </div>
        
        <VoiceChat />
      </div>
    </main>
  )
}