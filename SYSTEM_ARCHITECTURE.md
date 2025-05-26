# System Architecture & Project Structure: Spark Audio Notebook

This document explains the architecture and structure of the Spark Audio Notebook project.

---

## Overview
Spark Audio Notebook is a modern web application that generates engaging podcast conversations from URLs or news topics using AI. It features a React frontend, a Python (Flask + Socket.IO) backend, and supports real-time progress updates, API key management, and multiple text-to-speech providers.

---

## High-Level Architecture

```
+-------------------+        WebSocket/API         +-------------------+
|                   | <-------------------------> |                   |
|   React Frontend  |        (Vite, React)        |   Flask Backend   |
|                   |  /api/*, /socket.io, /audio | (Flask, SocketIO) |
+-------------------+                             +-------------------+
         |                                                 |
         |                                                 |
         |                File Storage                     |
         +-----------------------------------------------> |
         |                                                 |
         |<-----------------------------------------------+
         |           Audio/Transcript Files                |
         |                                                 |
         +-------------------+                             |
         |                   |                             |
         |  Text-to-Speech   |<----------------------------+
         |   Providers       |   (Google, ElevenLabs, etc.)|
         +-------------------+                             |
```

---

## Project Structure

```
.
├── src/                  # Frontend source code (React, Vite)
│   ├── components/       # React components (CustomPodcast, TopicPodcast, PodcastLibrary, etc.)
│   ├── lib/              # Utility functions
│   └── hooks/            # Custom React hooks
├── app.py                # Flask backend (API, Socket.IO, audio serving)
├── requirements.txt      # Python dependencies
├── static/               # Built frontend, audio, and transcript files
│   ├── audio/            # Generated podcast audio files
│   └── transcripts/      # Generated transcript files
├── data/                 # Additional audio/transcript storage
├── Dockerfile            # Containerization for deployment
├── DEPLOY_CLOUDFLARE.md  # Cloudflare deployment instructions
├── README.md             # Project overview and usage
└── ...                   # Other config and support files
```

---

## Key Components

- **Frontend (src/):**
  - Built with React and Vite for fast development and modern UI.
  - Handles user input, displays progress, and interacts with the backend via REST and WebSocket (Socket.IO).
  - Main components: `CustomPodcast`, `TopicPodcast`, `PodcastLibrary`, and UI utilities.

- **Backend (app.py):**
  - Flask app with REST endpoints and Socket.IO for real-time updates.
  - Handles podcast generation, text-to-speech, and file management.
  - Serves audio and transcript files to the frontend.

- **Audio/Transcript Storage:**
  - Audio and transcript files are stored in `static/audio/` and `static/transcripts/` for serving to the frontend.

- **Text-to-Speech Providers:**
  - Supports multiple TTS providers (Google, ElevenLabs, etc.) via API keys.

---

## Data Flow
1. User submits podcast generation request via frontend.
2. Frontend sends request to backend (REST or WebSocket).
3. Backend processes input, generates podcast audio/transcript, and stores files.
4. Backend emits progress and completion events via WebSocket.
5. Frontend updates UI in real-time and provides download links for audio/transcript.

---

## Extensibility
- Add new TTS providers by extending backend logic and updating API key management in the frontend.
- Add new UI features or endpoints as needed.

---

## See Also
- [DEPLOY_CLOUDFLARE.md](./DEPLOY_CLOUDFLARE.md) for deployment instructions.
- [README.md](./README.md) for getting started and usage.
