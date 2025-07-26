"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Provider } from "react-redux";
import { store } from "../store";
import { useAppDispatch, useAppSelector } from "../common/hooks";
import { rtcManager } from "../manager";
import { AudioVisualizer } from "./Agent/AudioVisualizer";
import { Camera } from "./Agent/Camera";
import { Microphone } from "./Agent/Microphone";
import { setRtcConnected, setEmotionData } from "../store/reducers/global";

interface EmotionData {
  attention: number;
  engagement: number;
  excitement: number;
  stress: number;
  relaxation: number;
  emotional_state: string;
  timestamp: string;
}

const TenVoiceChatInner: React.FC = () => {
  const dispatch = useAppDispatch();
  const { rtcConnected, emotionData } = useAppSelector((state) => state.global);
  const [isListening, setIsListening] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const websocketRef = useRef<WebSocket | null>(null);

  // Initialize RTC connection
  useEffect(() => {
    const initRTC = async () => {
      try {
        setIsConnecting(true);
        await rtcManager.initialize({
          appId: process.env.NEXT_PUBLIC_AGORA_APP_ID || "",
          channel: "therapist_session",
          userId: Math.floor(Math.random() * 10000),
        });
        dispatch(setRtcConnected(true));
      } catch (error) {
        console.error("RTC initialization failed:", error);
      } finally {
        setIsConnecting(false);
      }
    };

    initRTC();

    return () => {
      rtcManager.destroy();
      dispatch(setRtcConnected(false));
    };
  }, [dispatch]);

  // Connect to EEG emotion WebSocket
  useEffect(() => {
    const connectEmotionSocket = () => {
      try {
        const ws = new WebSocket("ws://localhost:8765");
        websocketRef.current = ws;

        ws.onopen = () => {
          console.log("Connected to emotion WebSocket");
        };

        ws.onmessage = (event) => {
          try {
            const emotionData: EmotionData = JSON.parse(event.data);
            dispatch(setEmotionData(emotionData));
          } catch (error) {
            console.error("Error parsing emotion data:", error);
          }
        };

        ws.onclose = () => {
          console.log("Emotion WebSocket disconnected");
          // Reconnect after 5 seconds
          setTimeout(connectEmotionSocket, 5000);
        };

        ws.onerror = (error) => {
          console.error("Emotion WebSocket error:", error);
        };
      } catch (error) {
        console.error("Failed to connect to emotion WebSocket:", error);
        // Retry after 5 seconds
        setTimeout(connectEmotionSocket, 5000);
      }
    };

    connectEmotionSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [dispatch]);

  const handleStartListening = async () => {
    if (!rtcConnected) return;
    
    try {
      setIsListening(true);
      await rtcManager.startListening();
    } catch (error) {
      console.error("Failed to start listening:", error);
      setIsListening(false);
    }
  };

  const handleStopListening = async () => {
    try {
      await rtcManager.stopListening();
      setIsListening(false);
    } catch (error) {
      console.error("Failed to stop listening:", error);
    }
  };

  const getEmotionalStateColor = (state: string) => {
    switch (state) {
      case "stressed":
        return "from-red-500 to-orange-500";
      case "relaxed":
        return "from-green-500 to-blue-500";
      case "engaged":
        return "from-blue-500 to-purple-500";
      case "excited":
        return "from-yellow-500 to-red-500";
      case "focused":
        return "from-purple-500 to-indigo-500";
      default:
        return "from-gray-400 to-gray-600";
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-6">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">AI Therapist</h1>
          <p className="text-indigo-200">Emotion-aware voice therapy with EEG integration</p>
        </div>

        {/* Emotion Status */}
        {emotionData && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 space-y-3">
            <div className="text-center">
              <div className={`inline-block px-4 py-2 rounded-full bg-gradient-to-r ${getEmotionalStateColor(emotionData.emotional_state)} text-white font-semibold`}>
                {emotionData.emotional_state?.charAt(0).toUpperCase() + emotionData.emotional_state?.slice(1) || "Neutral"}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-white/80">Attention: <span className="text-white font-medium">{(emotionData.attention * 100).toFixed(0)}%</span></div>
              <div className="text-white/80">Engagement: <span className="text-white font-medium">{(emotionData.engagement * 100).toFixed(0)}%</span></div>
              <div className="text-white/80">Stress: <span className="text-white font-medium">{(emotionData.stress * 100).toFixed(0)}%</span></div>
              <div className="text-white/80">Relaxation: <span className="text-white font-medium">{(emotionData.relaxation * 100).toFixed(0)}%</span></div>
            </div>
          </div>
        )}

        {/* Audio Visualizer */}
        <div className="flex justify-center">
          <AudioVisualizer />
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4">
          <Camera />
          <Microphone 
            isListening={isListening}
            onStart={handleStartListening}
            onStop={handleStopListening}
            disabled={!rtcConnected || isConnecting}
          />
        </div>

        {/* Connection Status */}
        <div className="text-center">
          {isConnecting ? (
            <p className="text-yellow-300">Connecting to therapy session...</p>
          ) : rtcConnected ? (
            <p className="text-green-300">✓ Connected to AI Therapist</p>
          ) : (
            <p className="text-red-300">✗ Connection failed</p>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl p-4">
          <h3 className="text-white font-semibold mb-2">How it works:</h3>
          <ul className="text-indigo-200 text-sm space-y-1">
            <li>• Your EEG headset provides real-time emotional context</li>
            <li>• The AI therapist adapts responses to your emotional state</li>
            <li>• Click the microphone to start voice conversation</li>
            <li>• Therapy sessions are private and secure</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

const TenVoiceChat: React.FC = () => {
  return (
    <Provider store={store}>
      <TenVoiceChatInner />
    </Provider>
  );
};

export default TenVoiceChat;