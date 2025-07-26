#!/usr/bin/env python3
"""
Simple WebSocket client to test emotion streaming.
"""

import asyncio
import json
import websockets

async def test_emotion_websocket():
    """Test connection to emotion WebSocket server."""
    uri = "ws://localhost:8765"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected! Listening for emotion events...")
            print("Press Ctrl+C to stop\n")
            
            while True:
                try:
                    message = await websocket.recv()
                    emotion_data = json.loads(message)
                    
                    # Pretty print emotion event
                    timestamp = emotion_data.get('timestamp', 0)
                    emotion = emotion_data.get('emotion', 'unknown')
                    confidence = emotion_data.get('confidence', 0)
                    metrics = emotion_data.get('metrics', {})
                    
                    print(f"[{timestamp:.2f}] Emotion: {emotion} (confidence: {confidence:.2f})")
                    print(f"  Metrics: {json.dumps(metrics, indent=2)}")
                    print("-" * 50)
                    
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                except Exception as e:
                    print(f"Error: {e}")
                    
    except ConnectionRefusedError:
        print("Could not connect to WebSocket server.")
        print("Make sure the emotion streaming server is running:")
        print("  python live_emotion.py websocket")
    except KeyboardInterrupt:
        print("\nDisconnected.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_emotion_websocket())