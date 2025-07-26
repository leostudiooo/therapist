"""
Emotion Bridge Extension for TEN Framework
Connects to the therapist's EEG WebSocket server to provide real-time emotional context.
"""

import asyncio
import json
import time
import websockets
from ten import (
    AsyncExtension,
    AsyncTenEnv,
    Cmd,
    StatusCode,
    CmdResult,
    Data,
)


class EmotionBridgeExtension(AsyncExtension):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.websocket_url = "ws://localhost:8765"
        self.reconnect_interval = 5.0
        self.emotion_threshold = 0.5
        self.enable_stale_filter = True
        self.max_reconnect_attempts = 10
        self.websocket = None
        self.last_emotion_time = 0
        self.reconnect_attempts = 0
        self.is_running = False

    async def on_configure(self, ten_env: AsyncTenEnv) -> None:
        """Called when the extension is being configured."""
        ten_env.log_debug("EmotionBridgeExtension on_configure")
        
        # Get configuration from manifest
        self.websocket_url = await ten_env.get_property_string("websocket_url")
        self.reconnect_interval = await ten_env.get_property_float("reconnect_interval")
        self.emotion_threshold = await ten_env.get_property_float("emotion_threshold")
        self.enable_stale_filter = await ten_env.get_property_bool("enable_stale_filter")
        self.max_reconnect_attempts = await ten_env.get_property_int("max_reconnect_attempts")
        
        ten_env.log_info(f"Emotion bridge configured: {self.websocket_url}")

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        """Called when the extension starts."""
        ten_env.log_debug("EmotionBridgeExtension on_start")
        self.is_running = True
        
        # Start the WebSocket connection task
        asyncio.create_task(self._websocket_task(ten_env))

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        """Called when the extension stops."""
        ten_env.log_debug("EmotionBridgeExtension on_stop")
        self.is_running = False
        
        if self.websocket:
            await self.websocket.close()

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        """Handle incoming commands."""
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"EmotionBridgeExtension on_cmd: {cmd_name}")
        
        # Send response
        cmd_result = CmdResult.create(StatusCode.OK)
        await ten_env.return_result(cmd_result, cmd)

    async def _websocket_task(self, ten_env: AsyncTenEnv):
        """Main WebSocket connection task."""
        while self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                ten_env.log_info(f"Connecting to emotion WebSocket: {self.websocket_url}")
                
                async with websockets.connect(self.websocket_url) as websocket:
                    self.websocket = websocket
                    self.reconnect_attempts = 0  # Reset on successful connection
                    ten_env.log_info("Connected to emotion WebSocket")
                    
                    async for message in websocket:
                        if not self.is_running:
                            break
                            
                        try:
                            emotion_data = json.loads(message)
                            await self._process_emotion_data(ten_env, emotion_data)
                        except json.JSONDecodeError as e:
                            ten_env.log_warn(f"Invalid JSON from emotion WebSocket: {e}")
                        except Exception as e:
                            ten_env.log_error(f"Error processing emotion data: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                ten_env.log_warn("Emotion WebSocket connection closed")
            except Exception as e:
                ten_env.log_error(f"Emotion WebSocket error: {e}")
                
            if self.is_running:
                self.reconnect_attempts += 1
                ten_env.log_info(f"Reconnecting in {self.reconnect_interval}s (attempt {self.reconnect_attempts})")
                await asyncio.sleep(self.reconnect_interval)

    async def _process_emotion_data(self, ten_env: AsyncTenEnv, emotion_data: dict):
        """Process incoming emotion data and send to TEN framework."""
        current_time = time.time()
        
        # Filter stale data if enabled
        if self.enable_stale_filter:
            data_timestamp = emotion_data.get('timestamp', current_time)
            if isinstance(data_timestamp, str):
                # Parse timestamp if it's a string
                try:
                    data_timestamp = float(data_timestamp)
                except ValueError:
                    data_timestamp = current_time
                    
            if current_time - data_timestamp > 2.0:  # Skip data older than 2 seconds
                ten_env.log_debug("Skipping stale emotion data")
                return
        
        # Extract emotion metrics
        attention = emotion_data.get('attention', 0.0)
        engagement = emotion_data.get('engagement', 0.0)
        excitement = emotion_data.get('excitement', 0.0)
        stress = emotion_data.get('stress', 0.0)
        relaxation = emotion_data.get('relaxation', 0.0)
        
        # Determine emotional state
        emotional_state = self._determine_emotional_state(attention, engagement, excitement, stress, relaxation)
        
        # Create emotion context
        emotion_context = {
            "emotional_state": emotional_state,
            "attention": attention,
            "engagement": engagement,
            "excitement": excitement,
            "stress": stress,
            "relaxation": relaxation,
            "timestamp": str(current_time),
            "context_text": self._generate_context_text(emotional_state, attention, engagement, excitement, stress, relaxation)
        }
        
        # Send data to TEN framework
        data = Data.create("emotion_context")
        for key, value in emotion_context.items():
            if isinstance(value, str):
                data.set_property_string(key, value)
            elif isinstance(value, (int, float)):
                data.set_property_float(key, float(value))
                
        await ten_env.send_data(data)
        ten_env.log_debug(f"Sent emotion context: {emotional_state}")

    def _determine_emotional_state(self, attention: float, engagement: float, excitement: float, stress: float, relaxation: float) -> str:
        """Determine the primary emotional state based on metrics."""
        # Normalize values to 0-1 range if needed
        metrics = {
            'stressed': stress,
            'relaxed': relaxation,
            'engaged': engagement,
            'excited': excitement,
            'focused': attention
        }
        
        # Find the dominant emotional state
        dominant_state = max(metrics.items(), key=lambda x: x[1])
        
        # Apply threshold filtering
        if dominant_state[1] < self.emotion_threshold:
            return "neutral"
            
        return dominant_state[0]

    def _generate_context_text(self, emotional_state: str, attention: float, engagement: float, excitement: float, stress: float, relaxation: float) -> str:
        """Generate human-readable context text for the AI."""
        context_parts = []
        
        # Primary emotional state
        context_parts.append(f"The user is currently feeling {emotional_state}")
        
        # Add specific metrics that are notable
        if stress > 0.7:
            context_parts.append("showing high stress levels")
        elif stress < 0.3 and relaxation > 0.6:
            context_parts.append("in a calm and relaxed state")
            
        if attention > 0.7:
            context_parts.append("with high focus and attention")
        elif attention < 0.4:
            context_parts.append("with low attention levels")
            
        if engagement > 0.7:
            context_parts.append("and appears highly engaged")
        elif engagement < 0.4:
            context_parts.append("and seems disengaged")
            
        if excitement > 0.7:
            context_parts.append("showing elevated excitement")
            
        # Combine parts
        if len(context_parts) == 1:
            return context_parts[0] + "."
        else:
            return f"{context_parts[0]}, {', '.join(context_parts[1:])}.".replace(", and", " and")


def create_extension(name: str) -> EmotionBridgeExtension:
    """Create and return the extension instance."""
    return EmotionBridgeExtension(name)