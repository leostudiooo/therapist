"""
Therapeutic CSM Wrapper - EEG-Aware Conversational Speech Model
Integrates Sesame's original CSM with therapeutic context and EEG emotional data
"""
import torch
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Import original CSM components
from generator import load_csm_1b, Generator, Segment

logger = logging.getLogger(__name__)

@dataclass
class EEGEmotionalState:
    """Represents emotional state derived from EEG data."""
    dominant_emotion: str  # e.g., "calm", "anxious", "stressed", "focused"
    arousal_level: float   # 0.0 to 1.0
    valence: float         # -1.0 (negative) to 1.0 (positive)
    stress_level: float    # 0.0 to 1.0
    cognitive_load: float  # 0.0 to 1.0
    confidence: float      # 0.0 to 1.0

class TherapeuticCSM:
    """
    Therapeutic wrapper around Sesame's CSM model with EEG integration.
    
    This class enhances CSM's conversation capabilities by:
    1. Injecting EEG-derived emotional context into conversation segments
    2. Providing therapeutic response templates and guidance
    3. Maintaining conversation history with emotional awareness
    """
    
    def __init__(self, device: str = "auto"):
        self.device = self._get_device(device)
        self.generator: Optional[Generator] = None
        self.sample_rate = 24000  # CSM standard
        
        # Initialize therapeutic persona segments
        self.therapeutic_persona = self._create_therapeutic_persona()
        
        # Load CSM model
        self._load_csm_model()
    
    def _get_device(self, device: str) -> str:
        """Determine the best available device."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
    
    def _load_csm_model(self):
        """Load the original CSM model."""
        try:
            logger.info(f"Loading original CSM model on {self.device}...")
            self.generator = load_csm_1b(device=self.device)
            logger.info("✅ CSM model loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to load CSM model: {e}")
            logger.warning("Continuing in text-only mode without audio generation")
            self.generator = None
    
    def _create_therapeutic_persona(self) -> List[Segment]:
        """Create therapeutic persona segments for CSM context."""
        # Create therapeutic introduction segments
        # Note: audio=None will be handled gracefully by CSM
        therapeutic_segments = [
            Segment(
                speaker=1,  # Therapist speaker ID
                text="I am a compassionate AI therapist trained in cognitive behavioral therapy, mindfulness, and empathetic listening. I provide a safe, non-judgmental space for you to explore your thoughts and feelings.",
                audio=None
            ),
            Segment(
                speaker=1,
                text="I can sense your emotional state through physiological monitoring and adapt my responses accordingly. What would you like to talk about today?",
                audio=None
            )
        ]
        
        return therapeutic_segments
    
    def format_eeg_context(self, eeg_state: EEGEmotionalState) -> str:
        """
        Convert EEG emotional state into descriptive text for CSM context.
        
        This is the key EEG integration point - we translate physiological
        data into natural language that CSM can use as conversational context.
        """
        context_parts = [
            f"[EMOTIONAL_STATE: {eeg_state.dominant_emotion}]",
            f"[AROUSAL: {eeg_state.arousal_level:.2f}]",
            f"[VALENCE: {eeg_state.valence:.2f}]",
            f"[STRESS: {eeg_state.stress_level:.2f}]",
            f"[COGNITIVE_LOAD: {eeg_state.cognitive_load:.2f}]"
        ]
        
        # Add contextual guidance for therapeutic response
        if eeg_state.stress_level > 0.7:
            context_parts.append("[GUIDANCE: User shows high stress - use calming, grounding techniques]")
        elif eeg_state.arousal_level < 0.3:
            context_parts.append("[GUIDANCE: User seems low energy - gentle encouragement needed]")
        elif eeg_state.valence < -0.5:
            context_parts.append("[GUIDANCE: User experiencing negative emotions - empathetic validation needed]")
        
        return " ".join(context_parts)
    
    def create_eeg_context_segment(self, eeg_state: EEGEmotionalState) -> Segment:
        """Create a CSM segment containing EEG emotional context."""
        eeg_context_text = self.format_eeg_context(eeg_state)
        
        return Segment(
            speaker=0,  # System/context speaker
            text=eeg_context_text,
            audio=None  # Context segments don't need audio
        )
    
    def generate_therapeutic_response(
        self,
        user_text: str,
        user_audio: Optional[torch.Tensor] = None,
        eeg_state: Optional[EEGEmotionalState] = None,
        conversation_history: List[Segment] = None,
        max_audio_length_ms: float = 15000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate therapeutic response with EEG-aware context.
        
        Args:
            user_text: User's spoken/typed message
            user_audio: Optional audio tensor from user
            eeg_state: Current EEG-derived emotional state
            conversation_history: Previous conversation segments
            max_audio_length_ms: Maximum audio generation length
            temperature: Generation temperature for CSM
            
        Returns:
            Dict with 'text', 'audio', and 'sample_rate' keys
        """
        
        # If CSM model not available, use therapeutic fallback
        if self.generator is None:
            return {
                "text": self._get_therapeutic_fallback(user_text, eeg_state),
                "audio": None,
                "sample_rate": self.sample_rate
            }
        
        try:
            # Build context segments for CSM
            context_segments = []
            
            # 1. Start with therapeutic persona
            context_segments.extend(self.therapeutic_persona)
            
            # 2. Add EEG emotional context if available
            if eeg_state:
                eeg_segment = self.create_eeg_context_segment(eeg_state)
                context_segments.append(eeg_segment)
            
            # 3. Add conversation history (limit to last 10 segments to fit context window)
            if conversation_history:
                context_segments.extend(conversation_history[-10:])
            
            # 4. Add current user segment
            user_segment = Segment(
                speaker=0,  # User speaker ID
                text=user_text,
                audio=user_audio if user_audio is not None else torch.zeros(self.sample_rate // 2)  # 0.5s silence if no audio
            )
            context_segments.append(user_segment)
            
            # Generate therapeutic response text based on context
            therapeutic_response_text = self._generate_contextual_response(user_text, eeg_state)
            
            # Use CSM to generate audio response
            logger.info(f"Generating CSM response with {len(context_segments)} context segments")
            
            response_audio = self.generator.generate(
                text=therapeutic_response_text,
                speaker=1,  # Therapist speaker ID
                context=context_segments,
                max_audio_length_ms=max_audio_length_ms,
                temperature=temperature
            )
            
            return {
                "text": therapeutic_response_text,
                "audio": response_audio,
                "sample_rate": self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error generating CSM response: {e}")
            # Fallback to text-only therapeutic response
            return {
                "text": self._get_therapeutic_fallback(user_text, eeg_state),
                "audio": None,
                "sample_rate": self.sample_rate
            }
    
    def _generate_contextual_response(self, user_text: str, eeg_state: Optional[EEGEmotionalState]) -> str:
        """
        Generate therapeutic response text based on user input and EEG state.
        
        This combines traditional therapeutic techniques with EEG-aware responses.
        """
        user_lower = user_text.lower()
        
        # If we have EEG data, use it to inform our response
        if eeg_state:
            # High stress response
            if eeg_state.stress_level > 0.7:
                if any(word in user_lower for word in ["work", "pressure", "deadline"]):
                    return "I can sense you're feeling quite stressed right now, especially about work pressures. Your body is showing signs of high tension. Let's take a moment to breathe together - can you try taking three slow, deep breaths with me?"
                else:
                    return f"I notice your stress levels are quite elevated right now. It's completely natural to feel this way. What's weighing most heavily on your mind at this moment?"
            
            # Low arousal/energy response
            elif eeg_state.arousal_level < 0.3:
                return "I can tell you're feeling quite low energy right now. That's okay - sometimes we need to move slowly. What small thing might help you feel just a little bit better today?"
            
            # Negative valence response
            elif eeg_state.valence < -0.5:
                return "I'm sensing you're experiencing some difficult emotions right now. Your feelings are completely valid. What's been the hardest part of what you're going through?"
            
            # High cognitive load response
            elif eeg_state.cognitive_load > 0.8:
                return "It seems like your mind is working really hard right now - I can see you're processing a lot. Sometimes it helps to slow down and focus on just one thing at a time. What feels most important to address first?"
        
        # Fallback to content-based therapeutic responses
        return self._get_therapeutic_fallback(user_text, eeg_state)
    
    def _get_therapeutic_fallback(self, user_text: str, eeg_state: Optional[EEGEmotionalState] = None) -> str:
        """Get therapeutic fallback response based on text content and optional EEG state."""
        user_lower = user_text.lower()
        
        # Include EEG context in fallback if available
        eeg_prefix = ""
        if eeg_state:
            if eeg_state.stress_level > 0.7:
                eeg_prefix = "I can sense you're feeling quite stressed. "
            elif eeg_state.arousal_level < 0.3:
                eeg_prefix = "I notice your energy seems low right now. "
            elif eeg_state.valence < -0.5:
                eeg_prefix = "I can tell you're experiencing some difficult feelings. "
        
        # Emotional distress keywords
        if any(word in user_lower for word in ["sad", "depressed", "down", "crying", "hurt"]):
            return f"{eeg_prefix}I can hear that you're going through a difficult time. Your feelings are completely valid, and it takes courage to share them. Can you tell me more about what's contributing to these feelings?"
        
        # Anxiety keywords
        elif any(word in user_lower for word in ["anxious", "worried", "nervous", "panic", "overwhelmed"]):
            return f"{eeg_prefix}It sounds like you're experiencing anxiety right now. That can feel really overwhelming. Let's take this one step at a time - what's on your mind that's causing you to feel this way?"
        
        # Anger keywords
        elif any(word in user_lower for word in ["angry", "mad", "frustrated", "furious"]):
            return f"{eeg_prefix}I can sense your frustration. Anger often signals something important to us. What's behind these feelings for you?"
        
        # Work/stress keywords
        elif any(word in user_lower for word in ["work", "job", "boss", "deadline", "pressure"]):
            return f"{eeg_prefix}Work-related stress can really impact our wellbeing. What's been most challenging for you in your work situation lately?"
        
        # Greetings
        elif any(word in user_lower for word in ["hello", "hi", "hey"]):
            return f"{eeg_prefix}Hello, I'm glad you're here. This is a safe space where you can share whatever is on your mind. How are you feeling today?"
        
        # Default empathetic response
        else:
            return f"{eeg_prefix}I hear you, and I want you to know that your feelings and experiences matter. I'm here to listen and support you. Can you tell me more about what you're going through?"
    
    def is_available(self) -> bool:
        """Check if CSM model is loaded and available."""
        return self.generator is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_loaded": self.is_available(),
            "device": self.device,
            "sample_rate": self.sample_rate,
            "model_type": "Sesame CSM-1B" if self.is_available() else "Therapeutic Fallback"
        }

# Factory function for easy instantiation
def load_therapeutic_csm(device: str = "auto") -> TherapeuticCSM:
    """Load TherapeuticCSM instance."""
    return TherapeuticCSM(device=device)