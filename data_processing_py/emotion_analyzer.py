import json
import time
import numpy as np
from typing import Dict, List, Optional, Tuple

class EmotionAnalyzer:
    """
    Real-time emotion analysis from Emotiv performance metrics.
    
    Uses performance metrics (engagement, excitement, stress, relaxation, interest)
    to classify emotional states into discrete categories.
    """
    
    # Comprehensive emotion vectors for AI therapy context
    # Format: [engagement, excitement, stress, relaxation, interest, attention]
    EMOTION_VECTORS = {
        # Positive states
        'excited':      [0.85, 0.85, 0.25, 0.30, 0.75, 0.80],
        'focused':      [0.90, 0.50, 0.20, 0.65, 0.70, 0.95],
        'calm':         [0.40, 0.20, 0.15, 0.85, 0.45, 0.60],
        'interested':   [0.80, 0.70, 0.20, 0.55, 0.95, 0.85],
        'relaxed':      [0.35, 0.25, 0.10, 0.90, 0.40, 0.50],
        'alert':        [0.85, 0.65, 0.30, 0.50, 0.80, 0.90],
        
        # Negative states for therapy
        'stressed':     [0.70, 0.60, 0.90, 0.15, 0.30, 0.75],
        'anxious':      [0.65, 0.75, 0.85, 0.20, 0.40, 0.70],
        'depressed':    [0.20, 0.10, 0.75, 0.25, 0.15, 0.30],
        'overwhelmed':  [0.55, 0.80, 0.95, 0.05, 0.25, 0.85],
        'frustrated':   [0.75, 0.85, 0.80, 0.10, 0.60, 0.90],
        'hopeless':     [0.15, 0.05, 0.85, 0.10, 0.05, 0.20],
        'lonely':       [0.25, 0.15, 0.65, 0.35, 0.20, 0.40],
        'guilty':       [0.45, 0.30, 0.90, 0.15, 0.35, 0.55],
        'ashamed':      [0.35, 0.25, 0.80, 0.20, 0.25, 0.45],
        'angry':        [0.80, 0.95, 0.90, 0.05, 0.70, 0.85],
        'disgusted':    [0.60, 0.70, 0.85, 0.10, 0.50, 0.75],
        'fearful':      [0.70, 0.90, 0.95, 0.05, 0.65, 0.95],
        
        # Neutral/baseline
        'neutral':      [0.50, 0.50, 0.50, 0.50, 0.50, 0.50],
        'bored':        [0.20, 0.15, 0.25, 0.60, 0.15, 0.25]
    }
    
    # Emotion descriptions for better understanding
    EMOTION_DESCRIPTIONS = {
        # Positive states
        'excited': 'High arousal, positive valence - energetic and enthusiastic state',
        'focused': 'High cognitive engagement with low stress - concentrated attention',
        'calm': 'Low arousal, positive valence - peaceful and relaxed state',
        'interested': 'Curious and engaged with sustained attention',
        'relaxed': 'Low arousal, positive valence - comfortable and at ease',
        'alert': 'High attention with moderate arousal - ready and responsive',
        
        # Negative states for therapy
        'stressed': 'High arousal, negative valence - tense and anxious state',
        'anxious': 'High arousal, negative valence - worried and uneasy',
        'depressed': 'Low arousal, negative valence - sad and disengaged state',
        'overwhelmed': 'Very high arousal with cognitive overload - unable to cope',
        'frustrated': 'High arousal with blocked goals - annoyed and irritated',
        'hopeless': 'Low arousal, negative valence - despair and loss of hope',
        'lonely': 'Low social engagement with negative affect - isolated feeling',
        'guilty': 'Self-directed negative emotion with high stress - remorseful',
        'ashamed': 'Self-conscious negative emotion with social anxiety - embarrassed',
        'angry': 'High arousal, negative valence - hostile and aggressive state',
        'disgusted': 'Aversive reaction to stimuli - repulsion and distaste',
        'fearful': 'High arousal, negative valence - afraid and threatened',
        
        'bored': 'Low arousal, negative valence - disengaged and uninterested',
        'neutral': 'Baseline state with balanced metrics'
    }
    
    def __init__(self, thresholds: Optional[Dict] = None):
        """
        Initialize emotion analyzer with configurable thresholds.
        
        Args:
            thresholds: Custom thresholds for emotion detection
        """
        self.thresholds = thresholds or {
            'engagement': 0.7,
            'excitement': 0.7,
            'stress': 0.7,
            'relaxation': 0.7,
            'interest': 0.7
        }
        self.previous_emotion = None
        self.emotion_history = []
        self.smoothing_window = 5
        self.min_change_threshold = 0.2
        
        # Therapy-specific thresholds
        self.crisis_threshold = 0.85  # High stress + low relaxation
        self.negative_emotions = {
            'stressed', 'anxious', 'depressed', 'overwhelmed', 'frustrated',
            'hopeless', 'lonely', 'guilty', 'ashamed', 'angry', 'disgusted', 'fearful'
        }
        
    def analyze_emotion(self, metrics: Dict[str, float], timestamp: float) -> Dict:
        """
        Analyze emotion from performance metrics with therapy context.
        
        Args:
            metrics: Dictionary with keys: engagement, excitement, stress, relaxation, interest
            timestamp: Unix timestamp
            
        Returns:
            Dictionary with emotion event data including therapy indicators
        """
        # Normalize metrics to 0-1 range
        normalized_metrics = self._normalize_metrics(metrics)
        
        # Calculate emotion scores
        emotion_scores = self._calculate_emotion_scores(normalized_metrics)
        
        # Determine dominant emotion
        dominant_emotion = self._get_dominant_emotion(emotion_scores)
        
        # Calculate confidence based on score strength
        confidence = emotion_scores[dominant_emotion]
        
        # Check for significant emotion change
        if self.previous_emotion and dominant_emotion != self.previous_emotion:
            if abs(confidence - self._get_previous_confidence()) < self.min_change_threshold:
                dominant_emotion = self.previous_emotion
                
        # Therapy-specific analysis
        crisis_level = self._calculate_crisis_level(normalized_metrics)
        is_negative = dominant_emotion in self.negative_emotions
        severity = self._calculate_severity(normalized_metrics, dominant_emotion)
        
        # Create emotion event
        emotion_event = {
            'timestamp': timestamp,
            'emotion': dominant_emotion,
            'confidence': round(confidence, 3),
            'metrics': {
                'engagement': round(normalized_metrics.get('engagement', 0), 3),
                'excitement': round(normalized_metrics.get('excitement', 0), 3),
                'stress': round(normalized_metrics.get('stress', 0), 3),
                'relaxation': round(normalized_metrics.get('relaxation', 0), 3),
                'interest': round(normalized_metrics.get('interest', 0), 3),
                'attention': round(normalized_metrics.get('attention', 0), 3)
            },
            'therapy_indicators': {
                'crisis_level': round(crisis_level, 3),
                'is_negative': is_negative,
                'severity': round(severity, 3),
                'needs_intervention': crisis_level > 0.7
            }
        }
        
        # Update history
        self.previous_emotion = dominant_emotion
        self.emotion_history.append(emotion_event)
        
        # Keep only recent history
        if len(self.emotion_history) > self.smoothing_window * 10:
            self.emotion_history = self.emotion_history[-self.smoothing_window * 10:]
            
        return emotion_event
    
    def _normalize_metrics(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """Normalize metrics to 0-1 range based on Emotiv scaling."""
        normalized = {}
        for key, value in metrics.items():
            # Emotiv scaled values are already 0-1
            normalized[key] = max(0, min(1, float(value)))
        return normalized
    
    def _calculate_emotion_scores(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate similarity scores for each emotion category."""
        scores = {}
        
        for emotion, requirements in self.EMOTIONS.items():
            score = 0
            count = 0
            
            for metric, target in requirements.items():
                if metric in metrics:
                    # Calculate similarity (1 - absolute difference)
                    similarity = 1 - abs(metrics[metric] - target)
                    score += similarity
                    count += 1
            
            # Average similarity score
            scores[emotion] = score / count if count > 0 else 0
            
        return scores
    
    def _get_dominant_emotion(self, scores: Dict[str, float]) -> str:
        """Get the dominant emotion based on highest score."""
        return max(scores, key=scores.get)
    
    def _get_previous_confidence(self) -> float:
        """Get confidence of previous emotion from history."""
        if self.emotion_history:
            return self.emotion_history[-1]['confidence']
        return 0.0
    
    def _calculate_crisis_level(self, metrics: Dict[str, float]) -> float:
        """Calculate crisis level based on stress and relaxation balance."""
        stress = metrics.get('stress', 0)
        relaxation = metrics.get('relaxation', 0)
        
        # Crisis is high stress + low relaxation
        crisis = (stress * 0.7) + ((1 - relaxation) * 0.3)
        return min(1.0, crisis)
    
    def _calculate_severity(self, metrics: Dict[str, float], emotion: str) -> float:
        """Calculate emotion severity based on metric intensity."""
        if emotion in ['depressed', 'hopeless', 'lonely']:
            # Low engagement + high stress
            return max(0, 1 - metrics.get('engagement', 0)) * 0.5 + metrics.get('stress', 0) * 0.5
        elif emotion in ['anxious', 'fearful', 'overwhelmed']:
            # High stress + high excitement
            return metrics.get('stress', 0) * 0.6 + metrics.get('excitement', 0) * 0.4
        elif emotion in ['angry', 'frustrated']:
            # High stress + high excitement + low relaxation
            return (metrics.get('stress', 0) + metrics.get('excitement', 0) + (1 - metrics.get('relaxation', 0))) / 3
        else:
            return 0.5  # Neutral severity
    
    def get_emotion_trend(self, window_size: int = 10) -> Dict:
        """
        Get emotion trend over recent history with therapy context.
        
        Args:
            window_size: Number of recent events to analyze
            
        Returns:
            Dictionary with trend analysis including therapy indicators
        """
        if len(self.emotion_history) < window_size:
            return {
                'trend': 'insufficient_data', 
                'stability': 0.0,
                'therapy_indicators': {
                    'negative_ratio': 0.0,
                    'crisis_average': 0.0,
                    'severity_trend': 'stable'
                }
            }
        
        recent = self.emotion_history[-window_size:]
        emotions = [event['emotion'] for event in recent]
        
        # Calculate emotion stability
        unique_emotions = len(set(emotions))
        stability = 1 - (unique_emotions / len(emotions))
        
        # Find dominant emotion in window
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # Therapy-specific analysis
        negative_count = sum(1 for e in emotions if e in self.negative_emotions)
        negative_ratio = negative_count / len(emotions)
        
        crisis_avg = np.mean([event['therapy_indicators']['crisis_level'] for event in recent])
        
        # Severity trend
        severities = [event['therapy_indicators']['severity'] for event in recent]
        if len(severities) > 1:
            trend = 'increasing' if severities[-1] > severities[0] else 'decreasing' if severities[-1] < severities[0] else 'stable'
        else:
            trend = 'stable'
        
        return {
            'trend': dominant_emotion,
            'stability': round(stability, 3),
            'emotion_distribution': emotion_counts,
            'therapy_indicators': {
                'negative_ratio': round(negative_ratio, 3),
                'crisis_average': round(crisis_avg, 3),
                'severity_trend': trend,
                'negative_emotions': negative_count
            }
        }
    
    def export_emotion_stream(self) -> str:
        """Export emotion history as JSON string."""
        return json.dumps(self.emotion_history, indent=2)
    
    def reset(self):
        """Reset analyzer state."""
        self.previous_emotion = None
        self.emotion_history = []


class EmotionStreamProcessor:
    """Process emotion data for streaming output."""
    
    def __init__(self, analyzer: EmotionAnalyzer):
        self.analyzer = analyzer
        self.output_callback = None
        
    def set_output_callback(self, callback):
        """Set callback function for streaming output."""
        self.output_callback = callback
        
    def process_metrics(self, metrics: Dict[str, float], timestamp: float):
        """Process metrics and emit emotion event."""
        emotion_event = self.analyzer.analyze_emotion(metrics, timestamp)
        
        if self.output_callback:
            self.output_callback(emotion_event)
        
        # Also print to console
        print(json.dumps(emotion_event))
        
    def start_csv_replay(self, csv_file: str, replay_speed: float = 1.0):
        """Start replaying emotion data from CSV."""
        import pandas as pd
        
        try:
            df = pd.read_csv(csv_file, skiprows=1)  # Skip header
            
            # Find PM columns
            pm_columns = [col for col in df.columns if col.startswith('PM.')]
            
            for idx, row in df.iterrows():
                timestamp = float(row['Timestamp'])
                
                # Extract performance metrics
                metrics = {
                    'engagement': float(row.get('PM.Engagement.Scaled', 0)),
                    'excitement': float(row.get('PM.Excitement.Scaled', 0)),
                    'stress': float(row.get('PM.Stress.Scaled', 0)),
                    'relaxation': float(row.get('PM.Relaxation.Scaled', 0)),
                    'interest': float(row.get('PM.Interest.Scaled', 0))
                }
                
                self.process_metrics(metrics, timestamp)
                
                # Control replay speed
                if idx < len(df) - 1:
                    next_time = float(df.iloc[idx + 1]['Timestamp'])
                    delay = (next_time - timestamp) / replay_speed
                    time.sleep(max(0, delay))
                    
        except Exception as e:
            print(f"Error processing CSV: {e}")


if __name__ == "__main__":
    # Demo usage
    analyzer = EmotionAnalyzer()
    
    # Sample data
    sample_metrics = {
        'engagement': 0.8,
        'excitement': 0.7,
        'stress': 0.2,
        'relaxation': 0.6,
        'interest': 0.9
    }
    
    result = analyzer.analyze_emotion(sample_metrics, time.time())
    print("Demo emotion event:")
    print(json.dumps(result, indent=2))
    
    # CSV replay demo
    # processor = EmotionStreamProcessor(analyzer)
    # processor.start_csv_replay("recorded_samples/sample.csv")