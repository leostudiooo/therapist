#!/usr/bin/env python3
"""
AI Therapy Emotion Detection Demo

Demonstrates enhanced emotion analysis specifically designed for AI therapy
applications, including crisis detection and severity assessment.
"""

import json
import time
import numpy as np
from emotion_analyzer import EmotionAnalyzer

class TherapySession:
    """Simulates a therapy session with emotional progression."""
    
    def __init__(self):
        self.analyzer = EmotionAnalyzer()
        self.session_data = []
        
    def simulate_session(self, scenario: str = "anxiety_crisis"):
        """Simulate a therapy session with realistic emotional progression."""
        
        scenarios = {
            "anxiety_crisis": [
                # [engagement, excitement, stress, relaxation, interest, attention]
                [0.3, 0.2, 0.4, 0.7, 0.3, 0.4],  # Initial calm
                [0.4, 0.5, 0.7, 0.5, 0.4, 0.6],  # Rising anxiety
                [0.6, 0.8, 0.9, 0.2, 0.5, 0.8],  # Peak anxiety
                [0.5, 0.6, 0.8, 0.3, 0.4, 0.7],  # Sustained high
                [0.4, 0.4, 0.6, 0.5, 0.4, 0.6],  # Beginning to calm
                [0.3, 0.3, 0.4, 0.7, 0.3, 0.5],  # Return to baseline
            ],
            "depression_episode": [
                [0.5, 0.4, 0.5, 0.6, 0.5, 0.6],  # Normal baseline
                [0.3, 0.2, 0.7, 0.3, 0.2, 0.3],  # Dropping mood
                [0.2, 0.1, 0.8, 0.2, 0.1, 0.2],  # Deep depression
                [0.1, 0.1, 0.9, 0.1, 0.1, 0.1],  # Severe episode
                [0.2, 0.2, 0.8, 0.2, 0.2, 0.2],  # Still low
                [0.3, 0.3, 0.6, 0.4, 0.3, 0.4],  # Slight improvement
            ],
            "anger_management": [
                [0.6, 0.4, 0.3, 0.7, 0.5, 0.6],  # Calm baseline
                [0.7, 0.6, 0.5, 0.6, 0.6, 0.7],  # Rising tension
                [0.8, 0.9, 0.8, 0.2, 0.7, 0.9],  # Anger peak
                [0.9, 0.9, 0.9, 0.1, 0.8, 0.9],  # Rage
                [0.7, 0.7, 0.7, 0.3, 0.6, 0.7],  # De-escalating
                [0.5, 0.4, 0.4, 0.6, 0.5, 0.5],  # Return to calm
            ]
        }
        
        data_sequence = scenarios.get(scenario, scenarios["anxiety_crisis"])
        start_time = time.time()
        
        print(f"=== Therapy Session: {scenario.replace('_', ' ').title()} ===")
        print()
        
        for i, metrics in enumerate(data_sequence):
            timestamp = start_time + i * 5  # 5 second intervals
            
            metrics_dict = {
                'engagement': metrics[0],
                'excitement': metrics[1],
                'stress': metrics[2],
                'relaxation': metrics[3],
                'interest': metrics[4],
                'attention': metrics[5]
            }
            
            event = self.analyzer.analyze_emotion(metrics_dict, timestamp)
            self.session_data.append(event)
            
            # Print therapy-focused output
            print(f"[{i+1}] {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
            print(f"    Emotion: {event['emotion'].upper()} (confidence: {event['confidence']})")
            
            # Crisis indicators
            if event['therapy_indicators']['needs_intervention']:
                print(f"    ⚠️  CRISIS DETECTED! Level: {event['therapy_indicators']['crisis_level']}")
            
            if event['therapy_indicators']['is_negative']:
                print(f"    🎯 Negative emotion detected - Severity: {event['therapy_indicators']['severity']}")
            
            print(f"    Stress: {metrics[2]:.2f}, Relaxation: {metrics[3]:.2f}")
            print()
            
            time.sleep(0.5)  # Brief pause for readability
    
    def generate_therapy_report(self):
        """Generate comprehensive therapy session report."""
        if not self.session_data:
            print("No session data available")
            return
        
        print("=== Therapy Session Report ===")
        print()
        
        # Overall emotion distribution
        emotions = [event['emotion'] for event in self.session_data]
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        print("Emotion Distribution:")
        for emotion, count in emotion_counts.items():
            percentage = (count / len(emotions)) * 100
            print(f"  {emotion}: {count} ({percentage:.1f}%)")
        
        # Crisis analysis
        crisis_events = [e for e in self.session_data if e['therapy_indicators']['needs_intervention']]
        print(f"\nCrisis Events: {len(crisis_events)}")
        
        if crisis_events:
            max_crisis = max(crisis_events, key=lambda x: x['therapy_indicators']['crisis_level'])
            print(f"  Peak Crisis: {max_crisis['therapy_indicators']['crisis_level']:.3f} at {max_crisis['emotion']}")
        
        # Negative emotion analysis
        negative_events = [e for e in self.session_data if e['therapy_indicators']['is_negative']]
        print(f"\nNegative Emotions: {len(negative_events)}/{len(self.session_data)} ({len(negative_events)/len(self.session_data)*100:.1f}%)")
        
        if negative_events:
            avg_severity = np.mean([e['therapy_indicators']['severity'] for e in negative_events])
            print(f"  Average Severity: {avg_severity:.3f}")
        
        # Session trend
        trend = self.analyzer.get_emotion_trend(len(self.session_data))
        print(f"\nSession Trend:")
        print(f"  Dominant Emotion: {trend['trend']}")
        print(f"  Stability: {trend['stability']}")
        print(f"  Negative Ratio: {trend['therapy_indicators']['negative_ratio']}")
        print(f"  Crisis Average: {trend['therapy_indicators']['crisis_average']}")
        
        return {
            'total_events': len(self.session_data),
            'emotion_distribution': emotion_counts,
            'crisis_events': len(crisis_events),
            'negative_emotions': len(negative_events),
            'trend': trend
        }

def run_therapy_demo():
    """Run comprehensive therapy demo."""
    
    session = TherapySession()
    
    print("🧠 AI Therapy Emotion Detection System")
    print("=" * 50)
    print()
    
    # Run different scenarios
    scenarios = ["anxiety_crisis", "depression_episode", "anger_management"]
    
    for scenario in scenarios:
        session.session_data.clear()  # Reset for each scenario
        session.simulate_session(scenario)
        
        report = session.generate_therapy_report()
        
        print("\n" + "="*50)
        print()
        
        # Save scenario data
        filename = f"therapy_session_{scenario}.json"
        with open(filename, 'w') as f:
            json.dump({
                'scenario': scenario,
                'report': report,
                'events': session.session_data
            }, f, indent=2)
        
        print(f"Session data saved to {filename}")
        print()

if __name__ == "__main__":
    run_therapy_demo()