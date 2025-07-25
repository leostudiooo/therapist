"""
EEG Processor - Converts EEG data to emotional states for CSM integration
Handles the data pipeline from raw EEG signals to structured emotional context
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from therapeutic_csm import EEGEmotionalState

logger = logging.getLogger(__name__)

@dataclass
class EEGMetrics:
    """Raw EEG metrics from EMOTIV or other EEG devices."""
    # Performance metrics (from EMOTIV)
    attention: float = 0.0      # 0.0 to 1.0
    engagement: float = 0.0     # 0.0 to 1.0
    excitement: float = 0.0     # 0.0 to 1.0
    interest: float = 0.0       # 0.0 to 1.0
    relaxation: float = 0.0     # 0.0 to 1.0
    stress: float = 0.0         # 0.0 to 1.0
    
    # Band power data (frequency analysis)
    theta: float = 0.0          # 4-8 Hz (meditation, creativity)
    alpha: float = 0.0          # 8-13 Hz (relaxation, calm focus)
    beta: float = 0.0           # 13-30 Hz (active thinking, concentration)
    gamma: float = 0.0          # 30-100 Hz (high-level cognitive processing)
    
    # Device status
    battery_level: float = 1.0  # 0.0 to 1.0
    signal_quality: float = 1.0 # 0.0 to 1.0
    timestamp: float = 0.0      # Unix timestamp

class EEGProcessor:
    """
    Processes raw EEG data into emotional states for therapeutic CSM integration.
    
    This class bridges the gap between physiological EEG measurements and 
    the emotional context that CSM can understand and respond to appropriately.
    """
    
    def __init__(self):
        self.recent_states: List[EEGEmotionalState] = []
        self.max_history = 10  # Keep last 10 emotional states for smoothing
        
        # Emotional state mapping thresholds
        self.emotion_thresholds = {
            'stress': 0.7,      # High stress threshold
            'relaxation': 0.6,  # High relaxation threshold
            'focus': 0.7,       # High attention/engagement threshold
            'anxiety': 0.6,     # Anxiety indicator threshold
        }
    
    def process_eeg_data(self, eeg_data: Dict[str, Any]) -> EEGEmotionalState:
        """
        Convert raw EEG data to structured emotional state.
        
        Args:
            eeg_data: Raw EEG data from EMOTIV or similar device
            
        Returns:
            EEGEmotionalState with processed emotional metrics
        """
        try:
            # Parse EEG metrics from input data
            metrics = self._parse_eeg_metrics(eeg_data)
            
            # Analyze emotional state
            emotional_state = self._analyze_emotional_state(metrics)
            
            # Add to history for trend analysis
            self.recent_states.append(emotional_state)
            if len(self.recent_states) > self.max_history:
                self.recent_states.pop(0)
            
            # Apply smoothing based on recent history
            smoothed_state = self._smooth_emotional_state(emotional_state)
            
            logger.debug(f"Processed EEG state: {smoothed_state.dominant_emotion} "
                        f"(stress: {smoothed_state.stress_level:.2f}, "
                        f"arousal: {smoothed_state.arousal_level:.2f})")
            
            return smoothed_state
            
        except Exception as e:
            logger.error(f"Error processing EEG data: {e}")
            return self._get_default_state()
    
    def _parse_eeg_metrics(self, eeg_data: Dict[str, Any]) -> EEGMetrics:
        """Parse raw EEG data into structured metrics."""
        # Handle different EEG data formats
        if 'met' in eeg_data:  # EMOTIV format
            met_data = eeg_data['met']
            return EEGMetrics(
                attention=met_data.get('att', 0.0),
                engagement=met_data.get('eng', 0.0),
                excitement=met_data.get('exc', 0.0),
                interest=met_data.get('int', 0.0),
                relaxation=met_data.get('rel', 0.0),
                stress=met_data.get('str', 0.0),
                timestamp=eeg_data.get('time', 0.0)
            )
        elif 'pow' in eeg_data:  # Band power format
            pow_data = eeg_data['pow']
            return EEGMetrics(
                theta=pow_data.get('theta', 0.0),
                alpha=pow_data.get('alpha', 0.0),
                beta=pow_data.get('beta', 0.0),
                gamma=pow_data.get('gamma', 0.0),
                timestamp=eeg_data.get('time', 0.0)
            )
        else:
            # Generic format - try to extract what we can
            return EEGMetrics(
                attention=eeg_data.get('attention', 0.0),
                stress=eeg_data.get('stress', 0.0),
                relaxation=eeg_data.get('relaxation', 0.0),
                engagement=eeg_data.get('engagement', 0.0),
                timestamp=eeg_data.get('timestamp', 0.0)
            )
    
    def _analyze_emotional_state(self, metrics: EEGMetrics) -> EEGEmotionalState:
        """Analyze EEG metrics to determine emotional state."""
        
        # Determine dominant emotion based on EEG patterns
        dominant_emotion = self._classify_dominant_emotion(metrics)
        
        # Calculate arousal level (activation/energy)
        arousal_level = self._calculate_arousal(metrics)
        
        # Calculate valence (positive/negative emotional tone)
        valence = self._calculate_valence(metrics)
        
        # Use stress directly from EEG metrics
        stress_level = metrics.stress
        
        # Calculate cognitive load
        cognitive_load = self._calculate_cognitive_load(metrics)
        
        # Calculate confidence based on signal quality and consistency
        confidence = self._calculate_confidence(metrics)
        
        return EEGEmotionalState(
            dominant_emotion=dominant_emotion,
            arousal_level=arousal_level,
            valence=valence,
            stress_level=stress_level,
            cognitive_load=cognitive_load,
            confidence=confidence
        )
    
    def _classify_dominant_emotion(self, metrics: EEGMetrics) -> str:
        """Classify the dominant emotional state."""
        
        # High stress patterns
        if metrics.stress > self.emotion_thresholds['stress']:
            if metrics.excitement > 0.6:
                return "anxious"
            else:
                return "stressed"
        
        # High relaxation patterns
        elif metrics.relaxation > self.emotion_thresholds['relaxation']:
            if metrics.alpha > 0.6:  # Alpha waves indicate calm focus
                return "calm"
            else:
                return "relaxed"
        
        # High attention/engagement patterns
        elif (metrics.attention > self.emotion_thresholds['focus'] or 
              metrics.engagement > self.emotion_thresholds['focus']):
            if metrics.beta > 0.7:  # High beta indicates active thinking
                return "focused"
            else:
                return "engaged"
        
        # Low arousal patterns
        elif metrics.excitement < 0.3 and metrics.engagement < 0.3:
            if metrics.stress > 0.4:
                return "overwhelmed"
            else:
                return "tired"
        
        # Balanced state
        else:
            return "neutral"
    
    def _calculate_arousal(self, metrics: EEGMetrics) -> float:
        """Calculate arousal level (0.0 = very calm, 1.0 = very activated)."""
        # Combine excitement, engagement, and beta waves
        arousal_components = [
            metrics.excitement * 0.4,
            metrics.engagement * 0.3,
            metrics.beta * 0.2,
            (1.0 - metrics.relaxation) * 0.1  # Inverse of relaxation
        ]
        
        return min(1.0, sum(arousal_components))
    
    def _calculate_valence(self, metrics: EEGMetrics) -> float:
        """Calculate valence (-1.0 = very negative, 1.0 = very positive)."""
        # Positive indicators: relaxation, alpha waves, low stress
        positive_score = (
            metrics.relaxation * 0.4 +
            metrics.alpha * 0.3 +
            (1.0 - metrics.stress) * 0.3
        )
        
        # Negative indicators: high stress, low interest
        negative_score = (
            metrics.stress * 0.5 +
            (1.0 - metrics.interest) * 0.3 +
            max(0, metrics.excitement - 0.8) * 0.2  # Very high excitement can be negative
        )
        
        # Convert to -1 to 1 scale
        return (positive_score - negative_score)
    
    def _calculate_cognitive_load(self, metrics: EEGMetrics) -> float:
        """Calculate cognitive load (0.0 = very low, 1.0 = very high)."""
        # High cognitive load indicators: high attention + high beta + high engagement
        load_components = [
            metrics.attention * 0.4,
            metrics.beta * 0.3,
            metrics.engagement * 0.2,
            metrics.gamma * 0.1  # Gamma waves indicate high-level processing
        ]
        
        return min(1.0, sum(load_components))
    
    def _calculate_confidence(self, metrics: EEGMetrics) -> float:
        """Calculate confidence in the emotional state assessment."""
        # Base confidence on signal quality and data completeness
        confidence_factors = []
        
        # Signal quality if available
        if hasattr(metrics, 'signal_quality'):
            confidence_factors.append(metrics.signal_quality * 0.5)
        
        # Data completeness (how many metrics have reasonable values)
        metric_values = [
            metrics.attention, metrics.engagement, metrics.stress,
            metrics.relaxation, metrics.excitement
        ]
        valid_metrics = sum(1 for v in metric_values if 0.1 <= v <= 0.9)
        completeness = valid_metrics / len(metric_values)
        confidence_factors.append(completeness * 0.5)
        
        return sum(confidence_factors) if confidence_factors else 0.5
    
    def _smooth_emotional_state(self, current_state: EEGEmotionalState) -> EEGEmotionalState:
        """Apply smoothing based on recent emotional state history."""
        if len(self.recent_states) < 2:
            return current_state
        
        # Simple moving average for numerical values
        recent_values = self.recent_states[-3:]  # Last 3 states
        
        smoothed_arousal = np.mean([s.arousal_level for s in recent_values])
        smoothed_valence = np.mean([s.valence for s in recent_values])
        smoothed_stress = np.mean([s.stress_level for s in recent_values])
        smoothed_cognitive_load = np.mean([s.cognitive_load for s in recent_values])
        
        # Keep the current dominant emotion unless there's a strong trend
        emotion_counts = {}
        for state in recent_values:
            emotion_counts[state.dominant_emotion] = emotion_counts.get(state.dominant_emotion, 0) + 1
        
        # Use most common recent emotion if it appears more than once
        most_common_emotion = max(emotion_counts, key=emotion_counts.get)
        if emotion_counts[most_common_emotion] > 1:
            dominant_emotion = most_common_emotion
        else:
            dominant_emotion = current_state.dominant_emotion
        
        return EEGEmotionalState(
            dominant_emotion=dominant_emotion,
            arousal_level=float(smoothed_arousal),
            valence=float(smoothed_valence),
            stress_level=float(smoothed_stress),
            cognitive_load=float(smoothed_cognitive_load),
            confidence=current_state.confidence
        )
    
    def _get_default_state(self) -> EEGEmotionalState:
        """Return a default neutral emotional state."""
        return EEGEmotionalState(
            dominant_emotion="neutral",
            arousal_level=0.5,
            valence=0.0,
            stress_level=0.3,
            cognitive_load=0.4,
            confidence=0.1  # Low confidence for default state
        )
    
    def get_current_trend(self) -> Dict[str, Any]:
        """Get trend analysis of recent emotional states."""
        if len(self.recent_states) < 3:
            return {"trend": "insufficient_data"}
        
        recent = self.recent_states[-5:]  # Last 5 states
        
        # Calculate trends
        stress_trend = np.polyfit(range(len(recent)), [s.stress_level for s in recent], 1)[0]
        arousal_trend = np.polyfit(range(len(recent)), [s.arousal_level for s in recent], 1)[0]
        valence_trend = np.polyfit(range(len(recent)), [s.valence for s in recent], 1)[0]
        
        return {
            "stress_trend": "increasing" if stress_trend > 0.02 else "decreasing" if stress_trend < -0.02 else "stable",
            "arousal_trend": "increasing" if arousal_trend > 0.02 else "decreasing" if arousal_trend < -0.02 else "stable",
            "valence_trend": "improving" if valence_trend > 0.02 else "declining" if valence_trend < -0.02 else "stable",
            "dominant_emotions": [s.dominant_emotion for s in recent],
            "average_confidence": np.mean([s.confidence for s in recent])
        }

# Factory function
def create_eeg_processor() -> EEGProcessor:
    """Create EEG processor instance."""
    return EEGProcessor()