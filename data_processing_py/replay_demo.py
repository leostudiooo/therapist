#!/usr/bin/env python3
"""
CSV Emotion Analysis Demo

Demonstrates emotion analysis from recorded Emotiv CSV files.
Provides both batch analysis and real-time replay modes.
"""

import json
import time
import argparse
import matplotlib.pyplot as plt
import numpy as np
from csv_replay import CSVReplayEngine, list_available_csvs
from emotion_analyzer import EmotionAnalyzer

def run_batch_analysis(csv_file: str, output_file: str = None):
    """
    Run batch emotion analysis on CSV file.
    
    Args:
        csv_file: Path to CSV file
        output_file: Optional output file for JSON results
    """
    print("=== Batch Emotion Analysis ===")
    
    engine = CSVReplayEngine(csv_file)
    
    # Load and analyze
    if not engine.load_csv():
        return []
    
    # Get summary
    summary = engine.get_summary()
    print(f"Data Summary:")
    print(f"  Duration: {summary.get('time_range', {}).get('duration', 0):.2f} seconds")
    print(f"  Samples: {summary.get('total_rows', 0)}")
    print(f"  Metrics: {summary.get('available_metrics', [])}")
    
    # Batch analyze with smoothing
    print("\nAnalyzing emotions...")
    events = engine.batch_analyze(window_size=5)
    
    print(f"Generated {len(events)} emotion events")
    
    # Save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"Results saved to {output_file}")
    
    # Print sample events
    if events:
        print("\nSample events:")
        for event in events[:5]:
            print(f"  {json.dumps(event)}")
    
    return events

def run_replay_demo(csv_file: str, replay_speed: float = 1.0, duration: float = 30.0, start_time: float = 0.0):
    """
    Run real-time replay demo.
    
    Args:
        csv_file: Path to CSV file
        replay_speed: Speed multiplier
        duration: Duration to replay in seconds
        start_time: Start time offset in seconds from beginning
    """
    print("=== Real-time Replay Demo ===")
    print(f"File: {csv_file}")
    print(f"Replay speed: {replay_speed}x")
    print(f"Duration: {duration}s")
    
    engine = CSVReplayEngine(csv_file)
    
    # Start replay
    events = engine.replay(
        replay_speed=replay_speed,
        start_time=0,
        end_time=duration,
        output_file="replay_output.json"
    )
    
    print(f"\nReplay complete: {len(events)} events")
    return events

def visualize_emotions(events: list):
    """
    Create simple visualization of emotion timeline.
    
    Args:
        events: List of emotion events
    """
    if not events:
        print("No events to visualize")
        return
    
    # Extract data for plotting
    timestamps = [event['timestamp'] for event in events]
    emotions = [event['emotion'] for event in events]
    confidences = [event['confidence'] for event in events]
    
    # Convert timestamps to relative time
    start_time = min(timestamps)
    relative_times = [t - start_time for t in timestamps]
    
    # Create emotion mapping for colors
    emotion_colors = {
        'excited': 'red',
        'focused': 'blue',
        'calm': 'green',
        'stressed': 'orange',
        'interested': 'purple',
        'neutral': 'gray'
    }
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Emotion timeline
    emotion_colors_list = [emotion_colors.get(e, 'black') for e in emotions]
    ax1.scatter(relative_times, emotions, c=emotion_colors_list, alpha=0.7, s=50)
    ax1.set_ylabel('Emotion')
    ax1.set_title('Emotion Timeline')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Emotion transitions
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    ax2.bar(emotion_counts.keys(), emotion_counts.values(), 
            color=[emotion_colors.get(e, 'black') for e in emotion_counts.keys()])
    ax2.set_ylabel('Frequency')
    ax2.set_title('Emotion Distribution')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('emotion_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("Visualization saved as 'emotion_analysis.png'")

def create_emotion_report(events: list):
    """
    Create detailed emotion analysis report.
    
    Args:
        events: List of emotion events
    """
    if not events:
        print("No events to analyze")
        return
    
    print("\n=== Emotion Analysis Report ===")
    
    # Basic statistics
    emotions = [event['emotion'] for event in events]
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    print("\nEmotion Distribution:")
    for emotion, count in emotion_counts.items():
        percentage = (count / len(events)) * 100
        print(f"  {emotion}: {count} ({percentage:.1f}%)")
    
    # Average confidence by emotion
    confidence_by_emotion = {}
    for event in events:
        emotion = event['emotion']
        confidence = event['confidence']
        if emotion not in confidence_by_emotion:
            confidence_by_emotion[emotion] = []
        confidence_by_emotion[emotion].append(confidence)
    
    print("\nAverage Confidence by Emotion:")
    for emotion, confidences in confidence_by_emotion.items():
        avg_conf = np.mean(confidences)
        print(f"  {emotion}: {avg_conf:.3f}")
    
    # Emotion transitions
    transitions = []
    for i in range(1, len(events)):
        prev_emotion = events[i-1]['emotion']
        curr_emotion = events[i]['emotion']
        if prev_emotion != curr_emotion:
            transitions.append((prev_emotion, curr_emotion))
    
    print(f"\nTotal Emotion Changes: {len(transitions)}")
    print(f"Stability Rate: {((len(events) - len(transitions)) / len(events)) * 100:.1f}%")
    
    # Save report
    report = {
        'total_events': len(events),
        'emotion_distribution': emotion_counts,
        'average_confidence': {k: np.mean(v) for k, v in confidence_by_emotion.items()},
        'transitions': len(transitions),
        'stability_rate': ((len(events) - len(transitions)) / len(events)) * 100
    }
    
    with open('emotion_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("Report saved to 'emotion_report.json'")

def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description='Emotiv CSV Emotion Analysis Demo')
    parser.add_argument('--csv', type=str, 
                       default='recorded_samples/Record Sample_INSIGHT2_432033_2025.07.25T15.25.42+08.00.pm.bp.csv',
                       help='CSV file to analyze')
    parser.add_argument('--mode', choices=['batch', 'replay'], default='batch',
                       help='Analysis mode')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Replay speed multiplier')
    parser.add_argument('--duration', type=float, default=30.0,
                       help='Duration to replay (seconds)')
    parser.add_argument('--start_time', type=float, default=0.0,
                       help='Start time offset in seconds from beginning')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--visualize', action='store_true',
                       help='Create visualization')
    parser.add_argument('--report', action='store_true',
                       help='Generate detailed report')
    parser.add_argument('--list', action='store_true',
                       help='List available CSV files')
    
    args = parser.parse_args()
    
    if args.list:
        csvs = list_available_csvs()
        print("Available CSV files:")
        for csv in csvs:
            print(f"  {csv}")
        return
    
    print("Emotiv CSV Emotion Analysis Demo")
    print("=" * 40)
    
    if args.mode == 'batch':
        events = run_batch_analysis(args.csv, args.output)
    else:  # replay
        events = run_replay_demo(args.csv, args.speed, args.duration, args.start_time)
    
    if events:
        if args.visualize:
            visualize_emotions(events)
        
        if args.report:
            create_emotion_report(events)
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()