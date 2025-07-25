'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface VoiceBlobProps {
  isListening: boolean
  isSpeaking: boolean
  volume: number
}

export default function VoiceBlob({ isListening, isSpeaking, volume }: VoiceBlobProps) {
  const [blobScale, setBlobScale] = useState(1)
  
  useEffect(() => {
    if (isListening || isSpeaking) {
      const scale = 1 + (volume * 0.5)
      setBlobScale(scale)
    } else {
      setBlobScale(1)
    }
  }, [volume, isListening, isSpeaking])

  const getBlobColor = () => {
    if (isSpeaking) return 'from-green-400 to-blue-500'
    if (isListening) return 'from-purple-400 to-pink-500'
    return 'from-gray-400 to-gray-600'
  }

  const getAnimationDuration = () => {
    if (isSpeaking) return 0.5
    if (isListening) return 1
    return 2
  }

  return (
    <div className="flex items-center justify-center w-80 h-80">
      <motion.div
        className={`relative w-64 h-64 rounded-full bg-gradient-to-br ${getBlobColor()}`}
        animate={{
          scale: blobScale,
        }}
        transition={{
          duration: getAnimationDuration(),
          ease: "easeInOut",
        }}
      >
        {/* Outer glow ring */}
        <motion.div
          className={`absolute inset-0 rounded-full bg-gradient-to-br ${getBlobColor()} opacity-30`}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.1, 0.3],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        
        {/* Middle ring */}
        <motion.div
          className={`absolute inset-4 rounded-full bg-gradient-to-br ${getBlobColor()} opacity-50`}
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 0.2, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.2,
          }}
        />
        
        {/* Inner core */}
        <motion.div
          className={`absolute inset-8 rounded-full bg-gradient-to-br ${getBlobColor()}`}
          animate={{
            scale: isListening || isSpeaking ? [1, 1.05, 1] : 1,
          }}
          transition={{
            duration: 0.8,
            repeat: isListening || isSpeaking ? Infinity : 0,
            ease: "easeInOut",
          }}
        />
        
        {/* Central dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="w-4 h-4 bg-white rounded-full"
            animate={{
              scale: isListening || isSpeaking ? [1, 1.5, 1] : 1,
              opacity: [1, 0.7, 1],
            }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        </div>
        
        {/* Volume-based particles */}
        {(isListening || isSpeaking) && volume > 0.1 && (
          <>
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className={`absolute w-2 h-2 bg-white rounded-full opacity-60`}
                style={{
                  top: '50%',
                  left: '50%',
                  transformOrigin: 'center',
                }}
                animate={{
                  x: [0, (Math.cos((i * Math.PI) / 3) * 80) * volume],
                  y: [0, (Math.sin((i * Math.PI) / 3) * 80) * volume],
                  opacity: [0.6, 0, 0.6],
                  scale: [1, 0.5, 1],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "easeOut",
                  delay: i * 0.1,
                }}
              />
            ))}
          </>
        )}
      </motion.div>
    </div>
  )
}