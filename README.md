# GENAI_ONLINEDESKTOPVOICEASSISTANT_TEAMAI
# 🤖 J.A.R.V.I.S. – Just A Rather Very Intelligent System

> **Your open-source, cross-platform, AI-powered desktop voice assistant.**  
> *"Sir, I'm always here to assist you."*

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

J.A.R.V.I.S. is a **locally-run Python voice assistant** that uses **Google’s Gemini AI**, real-time APIs, and system integrations to perform tasks like checking weather, monitoring system health, opening websites, playing music, navigating Disney+ Hotstar, and even showing your **exact location** on Google Maps — all through voice commands.

---

## 🌟 Features

- 🔊 **Voice Command Recognition** (via Google Speech API)
- ☁️ **AI-Powered Responses** using **Gemini 2.0 Flash**
- 🌤️ **Live Weather Updates** (via OpenWeatherMap)
- 💻 **System Monitoring**: CPU, RAM, Disk, Battery
- ⏱️ **Timers & Alarms** with audio alerts
- 🎬 **Movie Search on Disney+ Hotstar** (e.g., _“Play Baahubali on Hotstar”_)
- 📍 **Precise Location** via browser-based Google Maps geolocation
- 💾 **Save AI-generated code or text** directly to your Desktop
- 📜 **Command History** (last 24 hours) stored in SQLite
- 🛌 **System Control**: Sleep, Shutdown, Restart
- 🌐 **Open Websites**: YouTube, Wikipedia, Google, or any custom site
- 🎵 **Play Local Music Files**
- 🎙️ **Optional Wake Word** (“Jarvis”) using Porcupine (by Picovoice)

---

## 🚀 Demo

▶️ **Watch the full demo**: [YouTube Demo Link](https://www.youtube.com/your-jarvis-demo-video) *(replace with your video)*

![JARVIS Demo Screenshot](https://via.placeholder.com/800x400?text=J.A.R.V.I.S.+Console+with+Voice+Commands)  
*Example: Voice command → AI response → action executed*

---

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Internet connection (for AI and APIs)
- Microphone (built-in or external)

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/jarvis-ai-assistant.git
cd jarvis-ai-assistant
###Step 2: Install Dependencies
pip install -r requirements.txt
###Step 3: Set Up API Keys
Gemini API Key
Get it from: Google AI Studio
Replace in jarvis.py
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
OpenWeatherMap API Key (Optional)
Get it from: OpenWeatherMap API Keys
Replace in jarvis.py:
python jarvis.py
Step 4: Run J.A.R.V.I.S.
🎤 Usage Examples
“What’s the time?”
Speaks current time
“Weather in Mumbai”
Gives live weather
“Play Baahubali on Hotstar”
Opens exact movie page
“Where am I?”
Opens Google Maps with precise location prompt
“System info”
Reports CPU, RAM, battery
“Set a timer for 5 minutes”
Starts countdown with beep
“Show history”
Displays last 10 commands
“Jarvis quit”
Shuts down gracefully
jarvis-ai-assistant/
├── jarvis.py              # Main application
├── requirements.txt       # Python dependencies
├── jarvis_history.db      # Auto-generated command history
└── README.md
