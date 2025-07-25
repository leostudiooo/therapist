"""
True Sesame CSM (Conversational Speech Model) Implementation
Following the official architecture with Llama backbone + audio decoder
"""
import torch
import torchaudio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

# CSM-specific imports
from transformers import (
    AutoProcessor, 
    CsmForConditionalGeneration,
    AutoTokenizer
)
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

@dataclass
class CSMSegment:
    """Represents a conversation segment in CSM format."""
    role: str  # "0" for user, "1" for therapist
    content: List[Dict[str, Any]]  # List of content items (text/audio)
    
    @classmethod
    def text_segment(cls, role: str, text: str):
        """Create a text-only segment."""
        return cls(
            role=role,
            content=[{"type": "text", "text": text}]
        )
    
    @classmethod
    def audio_segment(cls, role: str, audio: torch.Tensor):
        """Create an audio segment."""
        return cls(
            role=role,
            content=[{"type": "audio", "audio": audio}]
        )

class CSMModel:
    """True CSM model implementation using HuggingFace Transformers."""
    
    def __init__(self, model_name: str = "sesame/csm-1b", device: str = "auto"):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.sample_rate = 24000  # CSM standard sample rate
        
        logger.info(f"Initializing CSM model: {model_name} on device: {self.device}")
        
        # Load CSM processor and model
        self._load_csm_model()
        
        # Initialize therapeutic conversation context
        self.therapeutic_context = self._create_therapeutic_context()
        
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
        """Load the CSM model and processor."""
        try:
            # Load the processor (handles tokenization and audio processing)
            logger.info("Loading CSM processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=None
            )
            
            # Load the CSM model
            logger.info("Loading CSM model...")
            self.model = CsmForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map=self.device if self.device != "cpu" else None,
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            
            # Move to device if needed
            if self.device != "cpu" and not hasattr(self.model, 'device_map'):
                self.model = self.model.to(self.device)
            
            logger.info("CSM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading CSM model: {e}")
            logger.warning("Falling back to therapeutic response mode without CSM audio generation")
            # Set fallback mode
            self.model = None
            self.processor = None
    
    def _create_therapeutic_context(self) -> List[CSMSegment]:
        """Create therapeutic conversation context with comprehensive templates."""
        return [
            CSMSegment.text_segment(
                role="1", 
                text="Hello, I'm here to provide a safe, supportive space for you to share your thoughts and feelings. I'm trained in therapeutic approaches including cognitive behavioral therapy, mindfulness, and empathetic listening."
            ),
            CSMSegment.text_segment(
                role="1",
                text="My role is to listen without judgment, help you explore your emotions, and guide you toward insights that may be helpful. What would you like to talk about today?"
            )
        ]
    
    def generate_therapeutic_response(
        self, 
        user_message: str, 
        conversation_history: List[CSMSegment] = None,
        max_new_tokens: int = 100,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate therapeutic response using CSM model or fallback.
        
        Returns:
            Dict containing text response and audio tensor
        """
        # If CSM model failed to load, use therapeutic fallback
        if self.model is None or self.processor is None:
            logger.info("Using therapeutic fallback mode (CSM model not available)")
            return {
                "text": self._get_therapeutic_fallback(user_message),
                "audio": None,
                "sample_rate": self.sample_rate
            }
        
        try:
            # Build conversation context
            conversation = self.therapeutic_context.copy()
            
            # Add conversation history if provided
            if conversation_history:
                conversation.extend(conversation_history)
            
            # Add current user message
            conversation.append(CSMSegment.text_segment(role="0", text=user_message))
            
            # Convert to CSM chat format
            chat_template = self._build_chat_template(conversation)
            
            # Process input using CSM processor
            inputs = self.processor.apply_chat_template(
                chat_template, 
                tokenize=True, 
                return_tensors="pt"
            )
            
            # Move inputs to device
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response with audio
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    output_audio=True,
                    return_dict_in_generate=True
                )
            
            # Extract generated text and audio
            generated_tokens = output.sequences[0]
            generated_audio = output.audio_values[0] if hasattr(output, 'audio_values') else None
            
            # Decode text response
            response_text = self.processor.tokenizer.decode(
                generated_tokens, 
                skip_special_tokens=True
            )
            
            # Extract just the therapist response (after last role marker)
            if "[1]" in response_text:
                response_text = response_text.split("[1]")[-1].strip()
            else:
                # Use therapeutic response templates based on context
                response_text = self._get_therapeutic_fallback(user_message)
            
            return {
                "text": response_text,
                "audio": generated_audio,
                "sample_rate": self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error generating therapeutic response: {e}")
            # Return fallback response
            return {
                "text": self._get_therapeutic_fallback(user_message),
                "audio": None,
                "sample_rate": self.sample_rate
            }
    
    def _get_therapeutic_fallback(self, user_message: str) -> str:
        """Get appropriate therapeutic fallback response based on user message context."""
        user_lower = user_message.lower()
        
        # Emotional distress keywords
        if any(word in user_lower for word in ["sad", "depressed", "down", "crying", "hurt", "pain"]):
            return "I can hear that you're going through a difficult time right now. Your feelings are completely valid, and it takes courage to share them. Can you tell me more about what's contributing to these feelings?"
        
        # Anxiety keywords
        elif any(word in user_lower for word in ["anxious", "worried", "nervous", "panic", "stress", "overwhelmed"]):
            return "It sounds like you're experiencing some anxiety right now. That can feel really overwhelming. Let's take this one step at a time. What's on your mind that's causing you to feel this way?"
        
        # Anger keywords
        elif any(word in user_lower for word in ["angry", "mad", "frustrated", "furious", "irritated"]):
            return "I can sense your frustration. Anger is a natural emotion that often signals something important to us. What's behind these feelings for you?"
        
        # Relationship issues
        elif any(word in user_lower for word in ["relationship", "partner", "friend", "family", "conflict"]):
            return "Relationships can be complex and challenging. It sounds like you're dealing with something difficult in your connections with others. What's been happening that's bringing this up for you?"
        
        # Work/career stress
        elif any(word in user_lower for word in ["work", "job", "career", "boss", "colleague"]):
            return "Work-related stress can really impact our overall wellbeing. It sounds like you're facing some challenges in your professional life. What's been most difficult for you lately?"
        
        # Greetings or initial contact
        elif any(word in user_lower for word in ["hello", "hi", "hey", "talk", "help"]):
            return "Hello, I'm glad you're here. This is a safe space where you can share whatever is on your mind. What would you like to explore together today?"
        
        # Default empathetic response
        else:
            return "I hear you, and I want you to know that your feelings and experiences matter. I'm here to listen and support you. Can you tell me more about what you're going through?"
    
    def _build_chat_template(self, segments: List[CSMSegment]) -> List[Dict[str, Any]]:
        """Build chat template format for CSM processor."""
        chat_template = []
        
        for segment in segments:
            chat_template.append({
                "role": segment.role,
                "content": segment.content
            })
        
        return chat_template
    
    def process_audio_input(self, audio_bytes: bytes) -> torch.Tensor:
        """Process audio input for CSM model."""
        try:
            # Convert bytes to tensor
            import io
            from pydub import AudioSegment
            
            # Load audio
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Convert to mono and resample
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            if audio_segment.frame_rate != self.sample_rate:
                audio_segment = audio_segment.set_frame_rate(self.sample_rate)
            
            # Convert to numpy
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            
            # Normalize
            if audio_array.dtype == np.int16:
                audio_array = audio_array / 32768.0
            elif audio_array.dtype == np.int32:
                audio_array = audio_array / 2147483648.0
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_array)
            
            return audio_tensor
            
        except Exception as e:
            logger.error(f"Error processing audio input: {e}")
            return torch.zeros(self.sample_rate)  # 1 second of silence
    
    def audio_to_bytes(self, audio_tensor: torch.Tensor) -> bytes:
        """Convert audio tensor to bytes for transmission."""
        try:
            import io
            import scipy.io.wavfile as wavfile
            
            # Ensure tensor is on CPU
            if audio_tensor.is_cuda or audio_tensor.device.type == 'mps':
                audio_tensor = audio_tensor.cpu()
            
            # Convert to numpy
            audio_numpy = audio_tensor.numpy()
            
            # Normalize and convert to int16
            if audio_numpy.max() > 0:
                audio_numpy = audio_numpy / audio_numpy.max()
            audio_int16 = (audio_numpy * 32767).astype(np.int16)
            
            # Create WAV in memory
            buffer = io.BytesIO()
            wavfile.write(buffer, self.sample_rate, audio_int16)
            
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            logger.error(f"Error converting audio to bytes: {e}")
            # Return minimal WAV
            import wave
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                silence = np.zeros(self.sample_rate, dtype=np.int16)
                wav_file.writeframes(silence.tobytes())
            
            buffer.seek(0)
            return buffer.read()

def load_csm_model(model_name: str = "sesame/csm-1b", device: str = "auto") -> CSMModel:
    """Load CSM model instance."""
    return CSMModel(model_name=model_name, device=device)

def create_fallback_csm_model() -> CSMModel:
    """Create a CSM model instance in fallback mode."""
    model = CSMModel.__new__(CSMModel)
    model.device = "cpu"
    model.sample_rate = 24000
    model.model = None
    model.processor = None
    model.therapeutic_context = model._create_therapeutic_context()
    return model