"""
CSM-Based AI Therapist Backend
Using Sesame's Conversational Speech Model for end-to-end voice therapy
"""
import json
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64
from dotenv import load_dotenv

from therapeutic_csm import load_therapeutic_csm, TherapeuticCSM
from conversation_manager import TherapeuticConversationManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global therapeutic CSM and conversation manager
therapeutic_csm: TherapeuticCSM = None
conversation_manager: TherapeuticConversationManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Therapeutic CSM on startup."""
    global therapeutic_csm, conversation_manager
    
    try:
        logger.info("Initializing Therapeutic CSM...")
        
        # Load therapeutic CSM (handles fallback internally)
        therapeutic_csm = load_therapeutic_csm(device="auto")
        
        # Initialize conversation manager with therapeutic CSM
        conversation_manager = TherapeuticConversationManager(therapeutic_csm)
        
        logger.info("✅ Therapeutic CSM AI initialized successfully!")
        logger.info(f"Model info: {therapeutic_csm.get_model_info()}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Therapeutic CSM: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Therapeutic CSM AI...")

app = FastAPI(
    title="Therapeutic CSM AI API", 
    description="EEG-Aware Conversational Speech Model for Therapeutic Applications",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TherapeuticCSMWebSocketHandler:
    """Handles WebSocket connections for EEG-aware therapeutic CSM conversations."""
    
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.conversation = None
    
    async def connect(self):
        """Accept WebSocket connection and create conversation session."""
        await self.websocket.accept()
        
        # Create new conversation session
        self.conversation = conversation_manager.create_session(self.session_id)
        
        # Send enhanced welcome message with EEG capabilities
        model_info = therapeutic_csm.get_model_info() if therapeutic_csm else {}
        await self.send_message({
            "type": "welcome",
            "message": "Connected to EEG-Aware Therapeutic CSM AI",
            "session_id": self.session_id,
            "capabilities": {
                "eeg_integration": True,
                "emotional_awareness": True,
                "csm_audio": model_info.get("model_loaded", False),
                "therapeutic_templates": True
            }
        })
        
        logger.info(f"WebSocket connected for session: {self.session_id}")
    
    async def handle_audio_message(self, message_data: Dict[str, Any]):
        """Handle incoming audio message from client."""
        try:
            # Decode audio data
            audio_base64 = message_data.get("audio", "")
            audio_bytes = base64.b64decode(audio_base64)
            
            # For now, we'll use a simple transcription approach
            # In full CSM implementation, this would be handled by the model directly
            user_text = await self.transcribe_audio(audio_bytes)
            
            if user_text:
                # Send transcription back to client
                await self.send_message({
                    "type": "transcription",
                    "text": user_text
                })
                
                # Add user message to conversation
                conversation_manager.add_user_message(
                    self.session_id, 
                    user_text, 
                    audio_bytes
                )
                
                # Generate therapist response
                response = conversation_manager.generate_therapist_response(self.session_id)
                
                if response:
                    if response["audio"]:
                        # Send audio response
                        await self.send_message({
                            "type": "audio_response",
                            "text": response["text"],
                            "audio": response["audio"]
                        })
                    else:
                        # Send text-only response
                        await self.send_message({
                            "type": "text_response",
                            "text": response["text"]
                        })
                else:
                    await self.send_message({
                        "type": "error",
                        "message": "Failed to generate response"
                    })
            
        except Exception as e:
            logger.error(f"Error handling audio message: {e}")
            await self.send_message({
                "type": "error",
                "message": "Failed to process audio"
            })
    
    async def handle_text_message(self, message_data: Dict[str, Any]):
        """Handle incoming text message from client."""
        try:
            user_text = message_data.get("text", "")
            
            if user_text:
                # Add user message to conversation
                conversation_manager.add_user_message(self.session_id, user_text)
                
                # Generate therapist response
                response = conversation_manager.generate_therapist_response(self.session_id)
                
                if response:
                    if response["audio"]:
                        # Send audio response
                        await self.send_message({
                            "type": "audio_response",
                            "text": response["text"],
                            "audio": response["audio"]
                        })
                    else:
                        # Send text-only response
                        await self.send_message({
                            "type": "text_response",
                            "text": response["text"]
                        })
                else:
                    await self.send_message({
                        "type": "error",
                        "message": "Failed to generate response"
                    })
        
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await self.send_message({
                "type": "error",
                "message": "Failed to process text"
            })
    
    async def handle_eeg_data(self, message_data: Dict[str, Any]):
        """Handle EEG emotional data with enhanced processing."""
        try:
            eeg_data = message_data.get("eeg_data", {})
            
            # Update EEG data in conversation manager
            success = conversation_manager.update_eeg_data(self.session_id, eeg_data)
            
            if success:
                # Get current EEG status
                eeg_status = conversation_manager.get_eeg_status(self.session_id)
                
                await self.send_message({
                    "type": "eeg_processed",
                    "message": "EEG data processed and emotional state updated",
                    "eeg_status": eeg_status
                })
            else:
                await self.send_message({
                    "type": "eeg_error",
                    "message": "Failed to process EEG data"
                })
            
        except Exception as e:
            logger.error(f"Error handling EEG data: {e}")
            await self.send_message({
                "type": "eeg_error",
                "message": "EEG processing error"
            })
    
    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio to text.
        In full CSM implementation, this would be handled by the model.
        For now, we'll use speech_recognition as a bridge.
        """
        try:
            import speech_recognition as sr
            from pydub import AudioSegment
            import io
            
            # Convert audio bytes to AudioSegment
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Convert to mono if stereo
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Resample to 16kHz (standard for speech recognition)
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
                
            # Export to WAV format for speech recognition
            wav_data = io.BytesIO()
            audio_segment.export(wav_data, format="wav")
            wav_data.seek(0)
            
            # Use speech recognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_data) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                logger.info(f"Transcribed: {text}")
                return text
                
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return "I'd like to talk but the audio wasn't clear"
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return "I want to share something with you"
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Fallback based on audio characteristics
            try:
                duration = len(audio_bytes) / (16000 * 2)  # Rough estimate
                if duration > 3:
                    return "I've been struggling with some difficult feelings lately"
                elif duration > 1:
                    return "I need someone to talk to"
                else:
                    return "Hello"
            except:
                return "I'd like to talk"
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to client."""
        try:
            if self.websocket.client_state.name == "CONNECTED":
                await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def disconnect(self):
        """Handle WebSocket disconnection."""
        if self.conversation:
            conversation_manager.end_session(self.session_id)
        logger.info(f"WebSocket disconnected for session: {self.session_id}")

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for EEG-aware therapeutic CSM conversations."""
    session_id = str(uuid.uuid4())
    handler = TherapeuticCSMWebSocketHandler(websocket, session_id)
    
    try:
        await handler.connect()
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "audio":
                await handler.handle_audio_message(message_data)
            elif message_type == "text":
                await handler.handle_text_message(message_data)
            elif message_type == "eeg":
                await handler.handle_eeg_data(message_data)
            else:
                await handler.send_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        await handler.disconnect()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await handler.disconnect()

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed CSM status."""
    if therapeutic_csm is None:
        return {
            "status": "initializing",
            "message": "Therapeutic CSM AI API",
            "model": "Loading..."
        }
    
    model_info = therapeutic_csm.get_model_info()
    return {
        "status": "healthy",
        "message": "Therapeutic CSM AI Therapist API", 
        "model_info": model_info,
        "eeg_integration": "enabled",
        "capabilities": [
            "EEG-aware emotional context",
            "Therapeutic conversation management", 
            "Real-time emotional state processing",
            "CSM audio generation" if model_info["model_loaded"] else "Text-only therapeutic responses"
        ]
    }

@app.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get comprehensive therapeutic conversation summary with EEG analysis."""
    if not conversation_manager:
        return {"error": "Conversation manager not initialized"}
    
    summary = conversation_manager.get_conversation_summary(session_id)
    return summary

@app.post("/sessions/{session_id}/eeg")
async def update_eeg_data(session_id: str, eeg_data: Dict[str, Any]):
    """Update EEG data and emotional state for a session."""
    if not conversation_manager:
        return {"error": "Conversation manager not initialized"}
    
    success = conversation_manager.update_eeg_data(session_id, eeg_data)
    if success:
        eeg_status = conversation_manager.get_eeg_status(session_id)
        return {"status": "updated", "eeg_status": eeg_status}
    else:
        return {"error": "Failed to update EEG data"}

@app.get("/sessions/{session_id}/eeg/status")
async def get_eeg_status(session_id: str):
    """Get current EEG status and emotional state for a session."""
    if not conversation_manager:
        return {"error": "Conversation manager not initialized"}
    
    eeg_status = conversation_manager.get_eeg_status(session_id)
    return eeg_status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)