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


class EmotionWebSocketServer:
    """
    WebSocket server for streaming emotion events to clients.
    """
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.streamer = None
        self.clients = set()
        
    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def broadcast_emotion(self, event):
        """Broadcast emotion event to all connected clients."""
        if self.clients:
            message = json.dumps(event)
            disconnected = set()
            
            for client in self.clients:
                try:
                    await client.send(message)
                except Exception as e:
                    disconnected.add(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.clients.discard(client)
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection."""
        await self.register_client(websocket)
        try:
            await websocket.wait_closed()
        finally:
            await self.unregister_client(websocket)
    
    def start_server(self, app_client_id: str, app_client_secret: str):
        """Start WebSocket emotion streaming server."""
        import asyncio
        import websockets
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        # Initialize emotion streamer
        self.streamer = LiveEmotionStreamer(app_client_id, app_client_secret)
        
        # Create event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Set up callback to broadcast emotions
        def emotion_callback(event):
            # Schedule coroutine in the event loop
            if self.clients and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_emotion(event), self.loop)
        
        self.streamer.set_output_callback(emotion_callback)
        
        # Start emotion streaming in background thread
        def start_emotion_streaming():
            self.streamer.start_streaming(['met'])
        
        streaming_thread = threading.Thread(target=start_emotion_streaming, daemon=True)
        streaming_thread.start()
        
        # Start WebSocket server
        print(f"Starting WebSocket emotion server on ws://localhost:{self.port}")
        
        async def main():
            try:
                async with websockets.serve(self.handle_client, "localhost", self.port):
                    print(f"WebSocket server listening on ws://localhost:{self.port}")
                    await asyncio.Future()  # Run forever
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"Port {self.port} is already in use. Try a different port or kill existing process.")
                    return
                raise
        
        try:
            self.loop.run_until_complete(main())
        except KeyboardInterrupt:
            print("\nShutting down WebSocket server...")
        finally:
            self.loop.close()


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


def demo_websocket_streaming():
    """Demonstrate WebSocket emotion streaming server."""
    import dotenv
    
    # Load credentials from .env
    app_client_id = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_ID')
    app_client_secret = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_SECRET')
    
    if not app_client_id or not app_client_secret:
        print("Please set EMOTIV_APP_CLIENT_ID and EMOTIV_APP_CLIENT_SECRET in .env file")
        return
    
    print("=== WebSocket Emotion Streaming Server ===")
    print("Starting WebSocket server for live emotion streaming...")
    print("Connect to ws://localhost:8765 to receive emotion events")
    print()
    
    server = EmotionWebSocketServer(port=8765)
    
    try:
        server.start_server(app_client_id, app_client_secret)
    except KeyboardInterrupt:
        print("\nShutting down WebSocket server...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "websocket":
        demo_websocket_streaming()
    else:
        demo_live_streaming()