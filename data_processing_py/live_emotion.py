import json
import time
import threading
from typing import Dict, Optional, Callable
from emotion_analyzer import EmotionAnalyzer, EmotionStreamProcessor
from sub_data import Subcribe

class LiveEmotionStreamer:
    """
    Real-time emotion streaming from Emotiv headset.
    
    Connects to live Emotiv data streams and provides real-time
    emotion analysis as JSON events.
    """
    
    def __init__(self, app_client_id: str, app_client_secret: str):
        """
        Initialize live emotion streaming.
        
        Args:
            app_client_id: Emotiv app client ID
            app_client_secret: Emotiv app client secret
        """
        self.app_client_id = app_client_id
        self.app_client_secret = app_client_secret
        
        self.analyzer = EmotionAnalyzer()
        self.subscriber = None
        self.is_streaming = False
        self.output_callback = None
        
        # Performance metrics state
        self.current_metrics = {
            'engagement': 0.0,
            'excitement': 0.0,
            'stress': 0.0,
            'relaxation': 0.0,
            'interest': 0.0
        }
        
        self.last_update_time = 0.0
        self.metrics_timeout = 2.0  # seconds
        
    def set_output_callback(self, callback: Callable[[Dict], None]):
        """Set callback for streaming output."""
        self.output_callback = callback
        
    def start_streaming(self, streams: list = None) -> bool:
        """
        Start real-time emotion streaming.
        
        Args:
            streams: List of data streams to subscribe to
            
        Returns:
            True if successful
        """
        if streams is None:
            streams = ['met']  # Performance metrics
            
        try:
            # Initialize subscriber
            self.subscriber = Subcribe(self.app_client_id, self.app_client_secret)
            
            # Override callback methods to process our data
            original_on_new_met_data = self.subscriber.on_new_met_data
            
            def custom_on_new_met_data(*args, **kwargs):
                self._handle_met_data(*args, **kwargs)
                original_on_new_met_data(*args, **kwargs)
            
            self.subscriber.on_new_met_data = custom_on_new_met_data
            
            # Start streaming
            self.is_streaming = True
            
            # Create and start streaming thread
            streaming_thread = threading.Thread(
                target=self._streaming_loop,
                daemon=True
            )
            streaming_thread.start()
            
            # Start Emotiv subscription
            self.subscriber.start(streams)
            
            return True
            
        except Exception as e:
            print(f"Error starting streaming: {e}")
            return False
    
    def stop_streaming(self):
        """Stop emotion streaming."""
        self.is_streaming = False
        if self.subscriber:
            # Note: Need to add close method to Subcribe class
            pass
    
    def _handle_met_data(self, *args, **kwargs):
        """Handle incoming met data from Emotiv."""
        data = kwargs.get('data')
        if not data or 'met' not in data:
            return
            
        try:
            # Extract metrics from met data
            met_values = data['met']
            timestamp = data.get('time', time.time())
            
            # Map met indices to metrics (based on Emotiv format)
            # met: ['eng.isActive', 'eng', 'exc.isActive', 'exc', 'lex', 'str.isActive', 'str', 'rel.isActive', 'rel', 'int.isActive', 'int', 'foc.isActive', 'foc']
            if len(met_values) >= 13:
                self.current_metrics = {
                    'engagement': float(met_values[1]) if met_values[0] else 0.0,
                    'excitement': float(met_values[3]) if met_values[2] else 0.0,
                    'stress': float(met_values[6]) if met_values[5] else 0.0,
                    'relaxation': float(met_values[8]) if met_values[7] else 0.0,
                    'interest': float(met_values[10]) if met_values[9] else 0.0,
                    'focus': float(met_values[12]) if met_values[11] else 0.0
                }
                
                self.last_update_time = time.time()
                
                # Analyze emotion
                emotion_event = self.analyzer.analyze_emotion(self.current_metrics, timestamp)
                
                # Output event
                if self.output_callback:
                    self.output_callback(emotion_event)
                else:
                    print(json.dumps(emotion_event))
                    
        except (IndexError, ValueError) as e:
            print(f"Error processing met data: {e}")
    
    def _streaming_loop(self):
        """Background thread for streaming management."""
        while self.is_streaming:
            # Check for stale data
            if time.time() - self.last_update_time > self.metrics_timeout:
                # Emit neutral emotion for stale data
                stale_event = {
                    'timestamp': time.time(),
                    'emotion': 'neutral',
                    'confidence': 0.5,
                    'metrics': self.current_metrics,
                    'status': 'stale_data'
                }
                
                if self.output_callback:
                    self.output_callback(stale_event)
                else:
                    print(json.dumps(stale_event))
            
            time.sleep(0.5)  # Check every 500ms
    
    def get_current_state(self) -> Dict:
        """Get current emotion state."""
        return {
            'is_streaming': self.is_streaming,
            'current_metrics': self.current_metrics,
            'last_update': self.last_update_time,
            'emotion_history': self.analyzer.emotion_history[-10:]  # Last 10 events
        }


class EmotionStreamServer:
    """
    HTTP server for streaming emotion events to clients.
    """
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.streamer = None
        self.server_thread = None
        
    def start_server(self, app_client_id: str, app_client_secret: str):
        """Start emotion streaming server."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        self.streamer = LiveEmotionStreamer(app_client_id, app_client_secret)
        
        class EmotionHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'close')
                self.end_headers()
                
                # Start streaming
                def send_event(event):
                    try:
                        self.wfile.write(f"{json.dumps(event)}\n".encode())
                        self.wfile.flush()
                    except:
                        pass
                
                self.streamer.set_output_callback(send_event)
                self.streamer.start_streaming()
                
                # Keep connection open
                try:
                    while True:
                        time.sleep(1)
                except:
                    pass
        
        self.server = HTTPServer(('localhost', self.port), EmotionHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"Emotion stream server started on http://localhost:{self.port}")


def demo_live_streaming():
    """Demonstrate live emotion streaming from headset."""
    import dotenv
    
    # Load credentials from .env
    app_client_id = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_ID')
    app_client_secret = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_SECRET')
    
    if not app_client_id or not app_client_secret:
        print("Please set EMOTIV_APP_CLIENT_ID and EMOTIV_APP_CLIENT_SECRET in .env file")
        return
    
    print("=== Live Emotion Streaming Demo ===")
    print("Connecting to Emotiv headset...")
    print("Streaming emotion events as JSON:")
    print()
    
    streamer = LiveEmotionStreamer(app_client_id, app_client_secret)
    
    # Simple console output
    def print_event(event):
        print(f"\r{json.dumps(event)}", end="", flush=True)
    
    streamer.set_output_callback(print_event)
    
    try:
        if streamer.start_streaming(['met']):
            print("Started streaming. Press Ctrl+C to stop...")
            
            # Keep running
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping streaming...")
        streamer.stop_streaming()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    demo_live_streaming()