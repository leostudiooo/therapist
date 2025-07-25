# AI Therapist Voice Chat System

A production-ready AI voice chat therapist that provides compassionate, real-time therapeutic conversations through voice interaction.

## 🎯 Features

- **Real-time Voice Chat**: Speak naturally and receive voice responses
- **Siri-like Interface**: Beautiful animated orb that reacts to your voice
- **Professional Therapy**: AI responses trained for therapeutic conversations
- **WebSocket Communication**: Low-latency real-time audio streaming
- **Volume Visualization**: Dynamic visual feedback based on audio input
- **Text Transcription**: See what you said and the AI's responses

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your HF_TOKEN (required)
   # Optionally add OPENAI_API_KEY for better responses
   ```

2. **Run the System**:
   ```bash
   ./run.sh
   ```

3. **Access the Interface**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🏗️ Architecture

### Backend (FastAPI)
- **WebSocket Server**: Real-time audio communication
- **Speech-to-Text**: Converts voice input to text
- **AI Therapist**: Generates compassionate responses
- **Text-to-Speech**: Uses Sesame CVM for natural voice synthesis
- **Fallback Responses**: Works without DeepSeek API

### Frontend (Next.js)
- **Voice Recording**: Browser-based audio capture
- **Real-time Visualization**: Volume-reactive UI animations
- **WebSocket Client**: Handles audio streaming
- **Responsive Design**: Mobile and desktop compatible

## 🛠️ Technical Stack

- **Backend**: FastAPI, WebSockets, SpeechRecognition, Requests
- **Frontend**: Next.js 14, React, TypeScript, Framer Motion, Tailwind CSS
- **AI Services**: Sesame CVM (TTS), DeepSeek Chat (optional), Google Speech Recognition
- **Real-time**: WebSocket connections for low-latency audio

## 🎨 UI Components

### VoiceBlob
- Animated orb that responds to voice input
- Color changes based on state (listening/speaking/idle)
- Volume-based scaling and particle effects
- Smooth animations using Framer Motion

### VoiceChat
- Manages WebSocket connections
- Handles audio recording and playback
- Displays transcriptions and responses
- Controls user interaction flow

## 🔧 Configuration

### Required Environment Variables
```bash
HF_TOKEN=your_hugging_face_token  # Required for TTS
```

### Optional Environment Variables
```bash
DEEPSEEK_API_KEY=your_deepseek_key   # For better AI responses using DeepSeek
```

## 📱 Usage

1. **Click the Orb**: Start voice recording
2. **Speak Naturally**: Talk about what's on your mind
3. **Click Again**: Stop recording and send to AI
4. **Listen**: AI responds with voice and text
5. **Continue**: Keep the conversation going

## 🔍 API Endpoints

- `GET /health`: Health check endpoint
- `WebSocket /ws/chat`: Real-time voice chat communication

## 🎵 Audio Flow

1. **User Speech** → Browser MediaRecorder
2. **Audio Data** → WebSocket → FastAPI Backend  
3. **Speech-to-Text** → Google Speech Recognition
4. **Text** → AI Therapist → Response Text
5. **Text-to-Speech** → Sesame CVM → Audio Response
6. **Audio Response** → WebSocket → Browser Playback

## 🚨 Troubleshooting

### Connection Issues
- Ensure backend is running on port 8000
- Check WebSocket connection in browser dev tools
- Verify .env file has correct HF_TOKEN

### Audio Issues
- Grant microphone permissions in browser
- Check audio input/output devices
- Ensure HTTPS for production deployment

### API Issues
- Verify HF_TOKEN is valid and has access
- Check Hugging Face API status
- Review backend logs for errors

## 🔮 Future Enhancements

- **EEG Integration**: Connect with EMOTIV headset data (already prepared)
- **Emotion Detection**: Visual emotional state indicators
- **Session Memory**: Conversation history and context
- **Voice Cloning**: Personalized therapist voice
- **Mobile App**: Native iOS/Android versions

## 📋 Development

### Manual Setup
```bash
# Backend
cd backend
uv sync --frozen
uv run --no-project uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### File Structure
```
therapist/
├── backend/
│   ├── main.py              # FastAPI server
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── VoiceBlob.tsx
│   │   │   └── VoiceChat.tsx
│   │   ├── page.tsx
│   │   └── layout.tsx
│   └── package.json
├── .env.example
└── run.sh                   # Startup script
```

This system provides a solid foundation for voice-based AI therapy that can be extended with EEG integration and other advanced features.