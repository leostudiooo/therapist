import pandas as pd
import json
import time
import numpy as np
from typing import Dict, List, Optional
from emotion_analyzer import EmotionAnalyzer, EmotionStreamProcessor

class CSVReplayEngine:
    """
    Replay recorded Emotiv CSV files as streaming emotion events.
    
    Handles CSV parsing, performance metrics extraction, and
    real-time emotion analysis with configurable replay speed.
    """
    
    def __init__(self, csv_file: str):
        """
        Initialize CSV replay engine.
        
        Args:
            csv_file: Path to Emotiv CSV file
        """
        self.csv_file = csv_file
        self.df = None
        self.analyzer = EmotionAnalyzer()
        self.processor = EmotionStreamProcessor(self.analyzer)
        self.original_sampling_rate = None
        self.start_timestamp = None
        
    def load_csv(self) -> bool:
        """
        Load and parse the CSV file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Skip the header line and read CSV
            self.df = pd.read_csv(self.csv_file, skiprows=1)
            
            # Extract metadata from header
            with open(self.csv_file, 'r') as f:
                header = f.readline()
                
            # Parse sampling rates from header
            if 'sampling rate:eeg_128;pm_2;pow_8' in header:
                self.original_sampling_rate = 2  # PM data at 2Hz
            
            # Extract start timestamp
            if 'start timestamp:' in header:
                import re
                match = re.search(r'start timestamp:([0-9.]+)', header)
                if match:
                    self.start_timestamp = float(match.group(1))
            
            print(f"Loaded CSV: {len(self.df)} rows")
            print(f"Original PM sampling rate: {self.original_sampling_rate}Hz")
            print(f"Start timestamp: {self.start_timestamp}")
            
            return True
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def extract_metrics(self, row: pd.Series) -> Dict[str, float]:
        """
        Extract performance metrics from a CSV row.
        
        Args:
            row: Single row from CSV DataFrame
            
        Returns:
            Dictionary of normalized performance metrics, or None if invalid
        """
        metrics = {}
        
        # Map CSV columns to normalized metrics
        metric_mapping = {
            'engagement': 'PM.Engagement.Scaled',
            'excitement': 'PM.Excitement.Scaled',
            'stress': 'PM.Stress.Scaled',
            'relaxation': 'PM.Relaxation.Scaled',
            'interest': 'PM.Interest.Scaled'
        }
        
        # Check if all required columns exist and have valid data
        valid = True
        for metric_name, csv_column in metric_mapping.items():
            if csv_column not in row or pd.isna(row[csv_column]):
                valid = False
                break
            value = float(row[csv_column])
            metrics[metric_name] = max(0, min(1, value))
        
        return metrics if valid else None
    
    def replay(self, replay_speed: float = 1.0, start_time: float = 0.0,
               end_time: Optional[float] = None, output_file: Optional[str] = None) -> List[Dict]:
        """
        Replay CSV data as emotion events.
        
        Args:
            replay_speed: Speed multiplier (1.0 = real-time, 2.0 = 2x speed)
            start_time: Start time offset in seconds from beginning
            end_time: End time offset in seconds from beginning
            output_file: Optional file to save JSON output
            
        Returns:
            List of emotion events
        """
        if self.df is None:
            if not self.load_csv():
                return []
        
        events = []
        
        # Filter by time range
        df_filtered = self.df.copy()
        
        if 'Timestamp' in df_filtered.columns:
            timestamps = df_filtered['Timestamp'].astype(float)
            
            if start_time > 0:
                df_filtered = df_filtered[timestamps >= start_time]
            if end_time:
                df_filtered = df_filtered[timestamps <= end_time]
        
        if len(df_filtered) == 0:
            print("No data in specified time range")
            return []
        
        print(f"Replaying {len(df_filtered)} data points...")
        
        # Filter for valid PM data only
        valid_rows = []
        for idx, row in df_filtered.iterrows():
            metrics = self.extract_metrics(row)
            if metrics is not None:
                valid_rows.append((idx, row, metrics))
        
        print(f"Replaying {len(valid_rows)} valid data points...")
        
        events = []
        for i, (idx, row, metrics) in enumerate(valid_rows):
            timestamp = float(row['Timestamp'])
            
            # Analyze emotion
            emotion_event = self.analyzer.analyze_emotion(metrics, timestamp)
            events.append(emotion_event)
            
            # Print streaming JSON
            print(json.dumps(emotion_event))
            
            # Control replay speed between valid rows only
            if i < len(valid_rows) - 1:
                current_time = timestamp
                next_time = float(valid_rows[i + 1][1]['Timestamp'])
                delay = (next_time - current_time) / replay_speed
                
                # Cap minimum delay to avoid too fast replay
                delay = max(0.1, min(delay, 2.0))
                time.sleep(delay)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(events, f, indent=2)
            print(f"Saved {len(events)} events to {output_file}")
        
        return events
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of the CSV data.
        
        Returns:
            Dictionary with summary information
        """
        if self.df is None:
            return {}
        
        pm_columns = [col for col in self.df.columns if col.startswith('PM.')]
        
        summary = {
            'total_rows': len(self.df),
            'time_range': {
                'start': float(self.df['Timestamp'].min()) if 'Timestamp' in self.df.columns else 0,
                'end': float(self.df['Timestamp'].max()) if 'Timestamp' in self.df.columns else 0,
                'duration': 0
            },
            'available_metrics': pm_columns,
            'sampling_rate': self.original_sampling_rate
        }
        
        if summary['time_range']['end'] > summary['time_range']['start']:
            summary['time_range']['duration'] = summary['time_range']['end'] - summary['time_range']['start']
        
        return summary
    
    def batch_analyze(self, window_size: int = 10) -> List[Dict]:
        """
        Batch analyze emotions without real-time replay.
        
        Args:
            window_size: Smoothing window for emotion stability
            
        Returns:
            List of smoothed emotion events
        """
        if self.df is None:
            if not self.load_csv():
                return []
        
        events = []
        
        for _, row in self.df.iterrows():
            timestamp = float(row['Timestamp'])
            metrics = self.extract_metrics(row)
            
            if metrics is None:  # Skip invalid rows
                continue
                
            emotion_event = self.analyzer.analyze_emotion(metrics, timestamp)
            events.append(emotion_event)
        
        # Apply smoothing if requested
        if window_size > 1:
            events = self._smooth_emotions(events, window_size)
        
        return events
    
    def _smooth_emotions(self, events: List[Dict], window_size: int) -> List[Dict]:
        """Apply moving average smoothing to emotion events."""
        if len(events) < window_size:
            return events
        
        smoothed_events = []
        
        for i in range(len(events)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(events), i + window_size // 2 + 1)
            
            window = events[start_idx:end_idx]
            
            # Find most common emotion in window
            emotions = [event['emotion'] for event in window]
            from collections import Counter
            dominant_emotion = Counter(emotions).most_common(1)[0][0]
            
            # Average confidence
            avg_confidence = np.mean([event['confidence'] for event in window])
            
            # Average metrics
            avg_metrics = {}
            for metric in ['engagement', 'excitement', 'stress', 'relaxation', 'interest']:
                avg_metrics[metric] = np.mean([event['metrics'][metric] for event in window])
            
            smoothed_event = {
                'timestamp': events[i]['timestamp'],
                'emotion': dominant_emotion,
                'confidence': round(avg_confidence, 3),
                'metrics': {k: round(v, 3) for k, v in avg_metrics.items()}
            }
            
            smoothed_events.append(smoothed_event)
        
        return smoothed_events


# Utility functions
def list_available_csvs(directory: str = "recorded_samples") -> List[str]:
    """List available CSV files in directory."""
    import os
    import glob
    
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    return [os.path.basename(f) for f in csv_files]


def quick_demo(csv_file: str = "recorded_samples/Record Sample_INSIGHT2_432033_2025.07.25T15.25.42+08.00.pm.bp.csv"):
    """Quick demo function."""
    print("=== CSV Replay Demo ===")
    
    # List available CSVs
    available = list_available_csvs()
    print(f"Available CSV files: {available}")
    
    if not available:
        print("No CSV files found in recorded_samples/")
        return
    
    # Use first available CSV if not specified
    if not csv_file and available:
        csv_file = f"recorded_samples/{available[0]}"
    
    # Initialize replay engine
    engine = CSVReplayEngine(csv_file)
    
    # Get summary
    summary = engine.get_summary()
    print(f"\nSummary: {json.dumps(summary, indent=2)}")
    
    # Batch analyze first 50 events
    print("\n=== Batch Analysis (first 50 events) ===")
    events = engine.batch_analyze(window_size=5)
    
    if events:
        print(f"Generated {len(events)} emotion events")
        for event in events[:100]:  # Show first 100
            print(json.dumps(event))
    
    return events


if __name__ == "__main__":
    # Run quick demo
    events = quick_demo()
    
    # Interactive replay
    if events:
        print("\n=== Interactive Replay ===")
        csv_file = "recorded_samples/Record Sample_INSIGHT2_432033_2025.07.25T15.25.42+08.00.pm.bp.csv"
        engine = CSVReplayEngine(csv_file)
        
        # Replay at 2x speed
        print("Replaying at 2x speed...")
        replayed_events = engine.replay(replay_speed=2.0, start_time=0, end_time=30)
        
        if replayed_events:
            print(f"Replayed {len(replayed_events)} events")