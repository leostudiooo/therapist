"""
Conversation Manager for Therapeutic CSM Sessions
Manages conversation state, segments, and EEG-aware therapeutic context using original CSM
"""
import torch
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
import io
import base64
from pydub import AudioSegment
import numpy as np

# Import original CSM components and our therapeutic wrapper
from generator import Segment
from therapeutic_csm import TherapeuticCSM, EEGEmotionalState
from eeg_processor import EEGProcessor

logger = logging.getLogger(__name__)

@dataclass
class TherapeuticConversationState:
    """Represents the current state of a therapeutic conversation with EEG integration."""
    session_id: str
    segments: List[Segment]                    # CSM conversation segments
    current_eeg_state: Optional[EEGEmotionalState]  # Current emotional state
    eeg_history: List[EEGEmotionalState]       # EEG emotional state history
    therapeutic_notes: List[str]               # Session notes
    start_time: float
    
class TherapeuticConversationManager:
    """
    Manages therapeutic conversations using original CSM with EEG integration.
    
    This class orchestrates the flow between:
    1. EEG data processing → emotional state analysis
    2. Therapeutic context injection → CSM conversation segments  
    3. CSM audio generation → therapeutic responses
    """
    
    def __init__(self, therapeutic_csm: TherapeuticCSM):
        self.therapeutic_csm = therapeutic_csm
        self.eeg_processor = EEGProcessor()
        self.active_conversations: Dict[str, TherapeuticConversationState] = {}
        
        logger.info(f"Therapeutic Conversation Manager initialized with CSM: {therapeutic_csm.get_model_info()}")
        
    def create_session(self, session_id: str) -> TherapeuticConversationState:
        """Create a new therapeutic conversation session."""
        # Initialize with therapeutic persona segments from CSM
        initial_segments = self.therapeutic_csm.therapeutic_persona.copy()
        
        conversation = TherapeuticConversationState(
            session_id=session_id,
            segments=initial_segments,
            current_eeg_state=None,
            eeg_history=[],
            therapeutic_notes=[],
            start_time=torch.cuda.Event(enable_timing=True).record() if torch.cuda.is_available() else 0
        )
        
        self.active_conversations[session_id] = conversation
        logger.info(f"Created therapeutic session: {session_id}")
        return conversation
        
    def get_session(self, session_id: str) -> Optional[TherapeuticConversationState]:
        """Get an existing conversation session."""
        return self.active_conversations.get(session_id)
    
    def update_eeg_data(self, session_id: str, eeg_data: Dict[str, Any]) -> bool:
        """
        Update EEG data for a session and process into emotional state.
        
        This is called when new EEG data arrives from the EMOTIV headset.
        """
        conversation = self.get_session(session_id)
        if not conversation:
            logger.error(f"Session not found: {session_id}")
            return False
        
        try:
            # Process EEG data into emotional state
            emotional_state = self.eeg_processor.process_eeg_data(eeg_data)
            
            # Update conversation state
            conversation.current_eeg_state = emotional_state
            conversation.eeg_history.append(emotional_state)
            
            # Keep history manageable (last 100 states)
            if len(conversation.eeg_history) > 100:
                conversation.eeg_history.pop(0)
            
            logger.debug(f"Updated EEG state for {session_id}: {emotional_state.dominant_emotion}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating EEG data: {e}")
            return False
    
    def add_user_message(self, session_id: str, text: str, audio_data: Optional[bytes] = None) -> bool:
        """Add a user message to the conversation."""
        conversation = self.get_session(session_id)
        if not conversation:
            logger.error(f"Session not found: {session_id}")
            return False
        
        try:
            # Process audio if provided
            audio_tensor = None
            if audio_data:
                audio_tensor = self._audio_bytes_to_tensor(audio_data)
            else:
                # Create small silence tensor if no audio
                audio_tensor = torch.zeros(self.therapeutic_csm.sample_rate // 2)  # 0.5s silence
            
            # Create user segment in original CSM format
            user_segment = Segment(
                speaker=0,  # User speaker ID
                text=text,
                audio=audio_tensor
            )
            
            conversation.segments.append(user_segment)
            logger.info(f"Added user message to session {session_id}: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user message: {e}")
            return False
    
    def generate_therapeutic_response(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate therapeutic response using CSM with EEG-aware context.
        
        This is the core integration point where EEG emotional state
        gets injected into CSM conversation context.
        """
        conversation = self.get_session(session_id)
        if not conversation:
            return None
        
        try:
            # Get the last user message
            user_segments = [s for s in conversation.segments if s.speaker == 0]
            if not user_segments:
                return None
            
            last_user_segment = user_segments[-1]
            last_user_text = last_user_segment.text
            last_user_audio = last_user_segment.audio
            
            # Get current EEG emotional state
            current_eeg_state = conversation.current_eeg_state
            
            # Get conversation history (exclude therapeutic persona, keep recent conversation)
            conversation_history = [s for s in conversation.segments 
                                  if s not in self.therapeutic_csm.therapeutic_persona]
            
            # Generate therapeutic response using CSM with EEG context
            logger.info(f"Generating CSM response with EEG state: "
                       f"{current_eeg_state.dominant_emotion if current_eeg_state else 'None'}")
            
            response = self.therapeutic_csm.generate_therapeutic_response(
                user_text=last_user_text,
                user_audio=last_user_audio,
                eeg_state=current_eeg_state,
                conversation_history=conversation_history,
                max_audio_length_ms=15000,  # 15 seconds max
                temperature=0.7
            )
            
            # Create therapist segment and add to conversation
            therapist_audio = response.get("audio")
            if therapist_audio is None:
                # Create silence if no audio generated
                therapist_audio = torch.zeros(self.therapeutic_csm.sample_rate)
            
            therapist_segment = Segment(
                speaker=1,  # Therapist speaker ID
                text=response["text"],
                audio=therapist_audio
            )
            
            conversation.segments.append(therapist_segment)
            
            # Convert audio to base64 for transmission if available
            audio_base64 = None
            if response.get("audio") is not None:
                audio_base64 = self._tensor_to_base64_audio(response["audio"])
            
            # Add therapeutic note
            eeg_note = ""
            if current_eeg_state:
                eeg_note = f" [EEG: {current_eeg_state.dominant_emotion}, stress={current_eeg_state.stress_level:.2f}]"
            conversation.therapeutic_notes.append(f"Response generated{eeg_note}")
            
            return {
                "text": response["text"],
                "audio": audio_base64,
                "speaker": 1,
                "eeg_state": asdict(current_eeg_state) if current_eeg_state else None,
                "model_info": self.therapeutic_csm.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"Error generating therapeutic response: {e}")
            # Return fallback response
            fallback_text = "I'm here to listen and support you. Please continue sharing your thoughts."
            if conversation.current_eeg_state and conversation.current_eeg_state.stress_level > 0.7:
                fallback_text = "I can sense you're feeling stressed right now. Take a deep breath with me. What's weighing on your mind?"
            
            return {
                "text": fallback_text,
                "audio": None,
                "speaker": 1,
                "eeg_state": asdict(conversation.current_eeg_state) if conversation.current_eeg_state else None,
                "error": "Fallback response used"
            }
    
    def _audio_bytes_to_tensor(self, audio_data: bytes) -> torch.Tensor:
        """Convert audio bytes to tensor for CSM processing."""
        try:
            # Load audio using pydub
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Convert to mono if stereo
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Resample to CSM sample rate (24kHz)
            if audio_segment.frame_rate != self.therapeutic_csm.sample_rate:
                audio_segment = audio_segment.set_frame_rate(self.therapeutic_csm.sample_rate)
            
            # Convert to numpy array
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            
            # Normalize to [-1, 1]
            if audio_array.dtype == np.int16:
                audio_array = audio_array / 32768.0
            elif audio_array.dtype == np.int32:
                audio_array = audio_array / 2147483648.0
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_array)
            
            return audio_tensor
            
        except Exception as e:
            logger.error(f"Error converting audio bytes to tensor: {e}")
            return torch.zeros(self.therapeutic_csm.sample_rate)  # 1 second of silence
    
    def _tensor_to_base64_audio(self, audio_tensor: torch.Tensor) -> str:
        """Convert audio tensor to base64 encoded WAV."""
        try:
            import scipy.io.wavfile as wavfile
            
            # Ensure tensor is on CPU
            if audio_tensor.is_cuda or audio_tensor.device.type == 'mps':
                audio_tensor = audio_tensor.cpu()
            
            # Convert to numpy
            audio_numpy = audio_tensor.numpy()
            
            # Normalize and convert to int16
            if audio_numpy.max() > 0:
                audio_numpy = audio_numpy / max(abs(audio_numpy.max()), abs(audio_numpy.min()))
            audio_int16 = (audio_numpy * 32767).astype(np.int16)
            
            # Create WAV in memory
            buffer = io.BytesIO()
            wavfile.write(buffer, self.therapeutic_csm.sample_rate, audio_int16)
            
            buffer.seek(0)
            audio_bytes = buffer.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error converting tensor to base64 audio: {e}")
            return ""
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of the therapeutic conversation."""
        conversation = self.get_session(session_id)
        if not conversation:
            return {}
        
        # Analyze conversation segments
        user_messages = [s.text for s in conversation.segments if s.speaker == 0]
        therapist_messages = [s.text for s in conversation.segments if s.speaker == 1]
        
        # Analyze EEG trends
        eeg_trend = self.eeg_processor.get_current_trend() if conversation.eeg_history else {}
        
        # Current emotional state
        current_emotion = None
        if conversation.current_eeg_state:
            current_emotion = {
                "emotion": conversation.current_eeg_state.dominant_emotion,
                "stress_level": conversation.current_eeg_state.stress_level,
                "arousal_level": conversation.current_eeg_state.arousal_level,
                "valence": conversation.current_eeg_state.valence
            }
        
        return {
            "session_id": session_id,
            "total_segments": len(conversation.segments),
            "user_messages": len(user_messages),
            "therapist_messages": len(therapist_messages),
            "recent_user_messages": user_messages[-3:],
            "recent_therapist_messages": therapist_messages[-3:],
            "current_emotional_state": current_emotion,
            "eeg_trend_analysis": eeg_trend,
            "therapeutic_notes": conversation.therapeutic_notes[-5:],  # Last 5 notes
            "csm_model_info": self.therapeutic_csm.get_model_info()
        }
    
    def get_eeg_status(self, session_id: str) -> Dict[str, Any]:
        """Get current EEG status and emotional state."""
        conversation = self.get_session(session_id)
        if not conversation or not conversation.current_eeg_state:
            return {"status": "no_eeg_data"}
        
        current_state = conversation.current_eeg_state
        trend = self.eeg_processor.get_current_trend()
        
        return {
            "status": "active",
            "current_state": asdict(current_state),
            "trend_analysis": trend,
            "history_length": len(conversation.eeg_history),
            "confidence": current_state.confidence
        }
    
    def end_session(self, session_id: str) -> bool:
        """End and cleanup a conversation session."""
        if session_id in self.active_conversations:
            conversation = self.active_conversations[session_id]
            
            # Log session summary
            summary = self.get_conversation_summary(session_id)
            logger.info(f"Ending session {session_id}: "
                       f"{summary['user_messages']} user messages, "
                       f"{len(conversation.eeg_history)} EEG states")
            
            del self.active_conversations[session_id]
            return True
        return False