# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Code Behavior

In this repository, Claude Code is powered by [Kimi-K2](https://github.com/MoonshotAI/Kimi-K2), the latest superpowered open-source LLM from Moonshot AI.

## Project Overview

A BCI-connected AI therapist that uses EMOTIV Insight 2.0 EEG headset to collect brain data and provide therapeutic responses. Built at AdventureX 2025.

## Architecture

### Data Collection Layer
- **EMOTIV Cortex SDK**: WebSocket-based EEG data collection via `cortex.py`
- **Data Streams**: EEG, band power (Theta, Alpha, Beta, Gamma), performance metrics (Attention, Engagement, Excitement, Interest, Relaxation, Stress)
- **Python Scripts**: Located in `data_processing_py/` for real-time data processing

### Core Components

#### EEG Data Processing (`data_processing_py/`)
- `cortex.py`: Main Cortex SDK wrapper for EMOTIV API communication
- `main.py`: Entry point for EEG data subscription using EMOTIV credentials
- `live_emotion.py`: Real-time emotion detection from EEG streams
- `emotion_analyzer.py`: Processes EEG data into emotional states
- `visualizer.py`: Data visualization tools
- `record.py`: EEG session recording functionality

#### Training & ML Components
- `facial_expression_train.py`: Facial expression training
- `mental_command_train.py`: Mental command training
- `therapy_demo.py`: Demo script for therapy interactions

#### Data Utilities
- `csv_replay.py`: Replay recorded EEG sessions from CSV
- `replay_demo.py`: Demo for replay functionality
- `sub_data.py`: Data subscription management
- `marker.py`: Event marking in EEG streams

### Frontend
- **React.js**: Web interface (in `app/` directory)
- **WebSocket client**: Real-time emotional events display
- **UI Elements**: Audio impulse circle, emotional timeline with colored dots

### Backend
- **Next.js**: API backend for streaming LLM and speech services
- **Middleware**: AudioStream + EmotionStream → ContextStream → TherapistAI → ResponseStream

## Development Commands

### Python Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r data_processing_py/requirements.txt

# Or use uv
uv sync
```

### EEG Data Collection
```bash
# Set EMOTIV credentials in .env
EMOTIV_APP_CLIENT_ID=your_client_id
EMOTIV_APP_CLIENT_SECRET=your_client_secret

# Start EEG data collection
cd data_processing_py
python main.py

# Live emotion detection
python live_emotion.py

# Record EEG session
python record.py
```

### Data Processing
```bash
# Replay recorded session
python csv_replay.py path/to/recording.csv

# Visualize EEG data
python visualizer.py

# Run emotion analysis
python emotion_analyzer.py
```

### Training Components
```bash
# Train facial expressions
python facial_expression_train.py

# Train mental commands
python mental_command_train.py
```

## Key Files

- `data_processing_py/cortex.py`: Core Cortex SDK wrapper (line 81+)
- `data_processing_py/main.py`: EEG subscription entry point
- `data_processing_py/sub_data.py`: Data subscription manager
- `.env`: EMOTIV API credentials (create this file)

## Configuration

1. **EMOTIV Setup**: Requires EMOTIV Insight 2.0 headset and EMOTIV Launcher
2. **Certificates**: Uses `certificates/rootCA.pem` for SSL verification
3. **Credentials**: Store EMOTIV API keys in `.env` file

## Data Streams

The system subscribes to multiple data streams from EMOTIV:
- `dev`: Device status and battery
- `eq`: Emotional quotient metrics
- `pow`: Band power data (frequency analysis)
- `met`: Performance metrics
- `eeg`: Raw EEG data
- `com`: Mental commands
- `fac`: Facial expressions