#!/usr/bin/env python3
"""
Emotion Visualization Module

Provides comprehensive visualization tools for emotion analysis
including timeline plots, heatmaps, and real-time dashboards.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

def create_emotion_timeline(events: List[Dict], save_path: str = None) -> plt.Figure:
    """
    Create timeline visualization of emotion events.
    
    Args:
        events: List of emotion events
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure
    """
    if not events:
        print("No events to visualize")
        return None
    
    # Prepare data
    timestamps = [event['timestamp'] for event in events]
    emotions = [event['emotion'] for event in events]
    confidences = [event['confidence'] for event in events]
    
    # Convert to relative time
    start_time = min(timestamps)
    relative_times = [(t - start_time) for t in timestamps]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # Color mapping
    emotion_colors = {
        'excited': '#FF6B6B',
        'focused': '#4ECDC4',
        'calm': '#45B7D1',
        'stressed': '#FFA500',
        'interested': '#9B59B6',
        'neutral': '#95A5A6'
    }
    
    # Plot 1: Emotion timeline with confidence
    ax1.set_title('Emotion Timeline with Confidence', fontsize=16, fontweight='bold', pad=20)
    
    for i, (time_point, emotion, confidence) in enumerate(zip(relative_times, emotions, confidences)):
        color = emotion_colors.get(emotion, 'gray')
        
        # Plot emotion as colored bar
        ax1.barh(emotion, 1, left=time_point, color=color, alpha=0.7, height=0.8)
        
        # Add confidence as circle size
        size = confidence * 100
        ax1.scatter(time_point, emotion, s=size, color=color, edgecolors='white', linewidth=2)
    
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Emotion', fontsize=12)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Plot 2: Confidence over time
    ax2.set_title('Emidence Confidence Over Time', fontsize=16, fontweight='bold', pad=20)
    
    for emotion in set(emotions):
        mask = [e == emotion for e in emotions]
        emotion_times = [t for t, m in zip(relative_times, mask) if m]
        emotion_confidences = [c for c, m in zip(confidences, mask) if m]
        
        if emotion_times:
            ax2.plot(emotion_times, emotion_confidences, 
                    marker='o', linestyle='-', linewidth=2, 
                    label=emotion, color=emotion_colors.get(emotion, 'gray'))
    
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Confidence', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Timeline saved to {save_path}")
    
    return fig

def create_emotion_heatmap(events: List[Dict], save_path: str = None) -> plt.Figure:
    """
    Create heatmap of emotion metrics over time.
    
    Args:
        events: List of emotion events
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure
    """
    if not events:
        return None
    
    # Prepare data
    timestamps = [event['timestamp'] for event in events]
    start_time = min(timestamps)
    relative_times = [(t - start_time) for t in timestamps]
    
    # Extract metrics
    metrics_data = []
    for event in events:
        metrics = event['metrics']
        metrics_data.append([
            metrics.get('engagement', 0),
            metrics.get('excitement', 0),
            metrics.get('stress', 0),
            metrics.get('relaxation', 0),
            metrics.get('interest', 0)
        ])
    
    metrics_df = pd.DataFrame(metrics_data, 
                             columns=['Engagement', 'Excitement', 'Stress', 'Relaxation', 'Interest'])
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Heatmap 1: Metrics over time
    ax1.set_title('Performance Metrics Heatmap', fontsize=14, fontweight='bold')
    
    # Create time bins
    time_bins = np.linspace(0, max(relative_times), min(len(events), 50))
    bin_indices = np.digitize(relative_times, time_bins)
    
    binned_data = []
    for i in range(1, len(time_bins) + 1):
        mask = bin_indices == i
        if np.any(mask):
            binned_data.append(np.mean(metrics_df[mask], axis=0))
        else:
            binned_data.append([0, 0, 0, 0, 0])
    
    binned_df = pd.DataFrame(binned_data, columns=['Engagement', 'Excitement', 'Stress', 'Relaxation', 'Interest'])
    
    sns.heatmap(binned_df.T, ax=ax1, cmap='RdYlBu_r', cbar_kws={'label': 'Intensity'})
    ax1.set_xlabel('Time Bins')
    ax1.set_ylabel('Metrics')
    
    # Heatmap 2: Emotion distribution
    ax2.set_title('Emotion Distribution Over Time', fontsize=14, fontweight='bold')
    
    emotions = [event['emotion'] for event in events]
    unique_emotions = list(set(emotions))
    
    # Create emotion matrix
    emotion_matrix = []
    for emotion in unique_emotions:
        emotion_counts = []
        for i in range(1, len(time_bins) + 1):
            mask = (bin_indices == i) & ([e == emotion for e in emotions])
            emotion_counts.append(np.sum(mask))
        emotion_matrix.append(emotion_counts)
    
    emotion_df = pd.DataFrame(emotion_matrix, index=unique_emotions)
    
    sns.heatmap(emotion_df, ax=ax2, cmap='YlOrRd', cbar_kws={'label': 'Count'})
    ax2.set_xlabel('Time Bins')
    ax2.set_ylabel('Emotion')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Heatmap saved to {save_path}")
    
    return fig

def create_metrics_dashboard(events: List[Dict], save_path: str = None) -> plt.Figure:
    """
    Create comprehensive metrics dashboard.
    
    Args:
        events: List of emotion events
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure
    """
    if not events:
        return None
    
    # Prepare data
    timestamps = [event['timestamp'] for event in events]
    start_time = min(timestamps)
    relative_times = [(t - start_time) for t in timestamps]
    
    # Extract all metrics
    metrics = {key: [] for key in ['engagement', 'excitement', 'stress', 'relaxation', 'interest']}
    
    for event in events:
        for key in metrics:
            metrics[key].append(event['metrics'].get(key, 0))
    
    # Create figure
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle('Emotion Metrics Dashboard', fontsize=18, fontweight='bold')
    
    # Plot 1: Individual metrics
    colors = {'engagement': '#3498db', 'excitement': '#e74c3c', 'stress': '#f39c12', 
              'relaxation': '#2ecc71', 'interest': '#9b59b6'}
    
    for i, (metric_name, values) in enumerate(metrics.items()):
        ax = axes[i//2, i%2] if i < 5 else axes[2, 0]
        ax.plot(relative_times, values, color=colors[metric_name], linewidth=2, marker='o', markersize=3)
        ax.set_title(f'{metric_name.title()} Over Time', fontweight='bold')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Intensity')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        ax.fill_between(relative_times, 0, values, alpha=0.3, color=colors[metric_name])
    
    # Plot 6: Emotion correlation matrix
    if len(events) > 1:
        ax_corr = axes[2, 1]
        
        # Create correlation matrix
        data = np.array([list(event['metrics'].values()) for event in events])
        correlation_matrix = np.corrcoef(data.T)
        
        # Labels
        labels = ['Engagement', 'Excitement', 'Stress', 'Relaxation', 'Interest']
        
        sns.heatmap(correlation_matrix, annot=True, fmt='.2f', 
                   xticklabels=labels, yticklabels=labels,
                   cmap='coolwarm', center=0, ax=ax_corr)
        ax_corr.set_title('Metrics Correlation Matrix', fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Dashboard saved to {save_path}")
    
    return fig

def create_realtime_dashboard(events: List[Dict], update_interval: float = 1.0):
    """
    Create real-time updating dashboard.
    
    Args:
        events: List of emotion events
        update_interval: Update interval in seconds
    """
    import matplotlib.animation as animation
    
    if not events:
        return
    
    # Setup figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Initialize data
    timestamps = [event['timestamp'] for event in events]
    start_time = min(timestamps)
    relative_times = [t - start_time for t in timestamps]
    emotions = [event['emotion'] for event in events]
    
    # Color mapping
    emotion_colors = {
        'excited': '#FF6B6B',
        'focused': '#4ECDC4',
        'calm': '#45B7D1',
        'stressed': '#FFA500',
        'interested': '#9B59B6',
        'neutral': '#95A5A6'
    }
    
    # Setup axes
    ax1.set_title('Real-time Emotion Timeline', fontsize=14)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Emotion')
    ax1.set_ylim(-0.5, len(set(emotions)) - 0.5)
    ax1.grid(True, alpha=0.3)
    
    emotion_labels = list(set(emotions))
    emotion_to_y = {label: i for i, label in enumerate(emotion_labels)}
    emotion_y = [emotion_to_y[e] for e in emotions]
    
    # Create scatter plot
    scatter = ax1.scatter([], [], c=[], s=50, alpha=0.7)
    
    ax2.set_title('Metrics Evolution', fontsize=14)
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Intensity')
    ax2.set_ylim(0, 1.1)
    ax2.grid(True, alpha=0.3)
    
    # Initialize lines
    lines = {}
    metrics = ['engagement', 'excitement', 'stress', 'relaxation', 'interest']
    colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
    
    for metric, color in zip(metrics, colors):
        line, = ax2.plot([], [], label=metric.title(), color=color, linewidth=2)
        lines[metric] = line
    
    ax2.legend()
    
    def animate(frame):
        # Update data
        end_idx = min(frame + 1, len(events))
        current_times = relative_times[:end_idx]
        current_emotions = emotions[:end_idx]
        current_y = [emotion_to_y[e] for e in current_emotions]
        
        # Update scatter plot
        scatter.set_offsets(np.c_[current_times, current_y])
        scatter.set_array([list(emotion_colors.values())[i] for i in [emotion_to_y[e] for e in current_emotions]])
        
        # Update metrics
        for metric, line in lines.items():
            values = [event['metrics'].get(metric, 0) for event in events[:end_idx]]
            line.set_data(current_times, values)
        
        # Update axes limits
        if current_times:
            ax1.set_xlim(0, max(current_times) + 1)
            ax2.set_xlim(0, max(current_times) + 1)
    
    anim = animation.FuncAnimation(fig, animate, frames=len(events), 
                                 interval=update_interval*1000, repeat=True)
    
    plt.tight_layout()
    plt.show()
    
    return anim

def generate_summary_report(events: List[Dict], output_dir: str = "./"):
    """
    Generate comprehensive analysis report with all visualizations.
    
    Args:
        events: List of emotion events
        output_dir: Directory to save reports
    """
    import os
    
    if not events:
        print("No events to report")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all visualizations
    create_emotion_timeline(events, os.path.join(output_dir, "emotion_timeline.png"))
    create_emotion_heatmap(events, os.path.join(output_dir, "emotion_heatmap.png"))
    create_metrics_dashboard(events, os.path.join(output_dir, "metrics_dashboard.png"))
    
    # Generate JSON summary
    summary = {
        'total_events': len(events),
        'time_range': {
            'start': min(event['timestamp'] for event in events),
            'end': max(event['timestamp'] for event in events),
            'duration': max(event['timestamp'] for event in events) - min(event['timestamp'] for event in events)
        },
        'emotion_distribution': {},
        'average_metrics': {}
    }
    
    # Calculate emotion distribution
    emotions = [event['emotion'] for event in events]
    for emotion in set(emotions):
        summary['emotion_distribution'][emotion] = emotions.count(emotion)
    
    # Calculate average metrics
    for metric in ['engagement', 'excitement', 'stress', 'relaxation', 'interest']:
        values = [event['metrics'].get(metric, 0) for event in events]
        summary['average_metrics'][metric] = float(np.mean(values))
    
    with open(os.path.join(output_dir, "analysis_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Analysis report saved to {output_dir}")


def demo_visualization():
    """Demo the visualization capabilities."""
    # Sample data for demonstration
    sample_events = [
        {'timestamp': 1000.0, 'emotion': 'calm', 'confidence': 0.8, 'metrics': {'engagement': 0.3, 'excitement': 0.2, 'stress': 0.1, 'relaxation': 0.9, 'interest': 0.4}},
        {'timestamp': 1001.0, 'emotion': 'calm', 'confidence': 0.85, 'metrics': {'engagement': 0.35, 'excitement': 0.25, 'stress': 0.15, 'relaxation': 0.85, 'interest': 0.45}},
        {'timestamp': 1002.0, 'emotion': 'interested', 'confidence': 0.75, 'metrics': {'engagement': 0.7, 'excitement': 0.6, 'stress': 0.2, 'relaxation': 0.6, 'interest': 0.8}},
        {'timestamp': 1003.0, 'emotion': 'focused', 'confidence': 0.9, 'metrics': {'engagement': 0.8, 'excitement': 0.5, 'stress': 0.1, 'relaxation': 0.7, 'interest': 0.6}},
        {'timestamp': 1004.0, 'emotion': 'excited', 'confidence': 0.8, 'metrics': {'engagement': 0.9, 'excitement': 0.8, 'stress': 0.3, 'relaxation': 0.5, 'interest': 0.7}},
    ]
    
    print("Creating demo visualizations...")
    
    # Create all visualizations
    create_emotion_timeline(sample_events, "demo_timeline.png")
    create_emotion_heatmap(sample_events, "demo_heatmap.png")
    create_metrics_dashboard(sample_events, "demo_dashboard.png")
    
    print("Demo visualizations created:")
    print("  - demo_timeline.png")
    print("  - demo_heatmap.png")
    print("  - demo_dashboard.png")


if __name__ == "__main__":
    demo_visualization()