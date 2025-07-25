# therapist

A BCI-connected AI therapist.

## Hardware

- EMOTIV Insight 2.0 EEG headset for brain-computer interface (BCI) data collection.

## Architecture

### Data Collection

- EMOTIV Cortex SDK for EEG data collection.
- Python scripts fetch data from the Cortex API WebSocket Interface.

### Data Processing

- Extract:
	- Frequencies and band power: Theta, Alpha, Beta, Gamma.
	- Performance metrics: Attention, Engagement, Excitement, Intrest, Relaxation, Stress.
- Process:
	- TBD: Implement data processing algorithms to map performance metrics and frequency-power's to emotional states.
	- Turn continuous data into discrete emotional "events" on a timeline.
- Stream:
	- Stream the converted emotional events realtime at local websocket server.

### Middleware

#### Input

- `AudioStream` User voice input
- `EmotionStream` Emotional events from local websocket server

#### Workflow

1. Receive `AudioStream` and `EmotionStream` as input.
2. `AudioStream` to `TranscriptionStream`, where audio is transcribed to text, and embedding timecode and emotional context (with certain speech-to-text APIs capable of this).
3. `TranscriptionStream` combined with `EmotionStream` to `ContextStream`, where the context of the conversation is built:
	- Use timecodes embedded in the transcription to align with emotional events.
	- After a sentence is transcribed, check for emotional events that occurred during that time.
	- Append emotional context to the transcription like: "Hi there, I'm John. \[Voice:Happy\] \[Emotion: Happy\]".
4. `ContextStream` sent to `TherapistAI`, where the AI therapist processes the context and generates a response.
5. `TherapistAI` response sent to `ResponseStream`, which formats the response for output.
6. `ResponseStream` sent to `Output`, which can be a text-to-speech engine or other output methods.

#### Output

- `ResponseStream` for formatted AI responses.
- `AudioStream` for text-to-speech output.

### Frontend

- React.js for the web interface.
- WebSocket client to connect to the local websocket server for real-time emotional events.
- Display a mimalist interface with:
	- A circle on the center, showing audio impulses
	- A timeline at the bottom, showing emotional events as colored dots (but don't let the users know what the colors mean since we want them not to focus on the emotions but on the conversation)

### Backend

- Next.js for the backend API.
- Streaming LLM and speech service requests and responses.

## Acknowledgements

This project was built at AdventureX 2025, China's largest hackathon held in Hangzhou. Special thanks to the EMOTIV team for providing the EEG headset and Cortex SDK, to the AdventureX organizers for the opportunity to build this innovative AI therapist, and to the Moonshot AI team for building Kimi-K2, the LLM powering this project.