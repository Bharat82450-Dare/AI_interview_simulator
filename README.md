# IntervAI: AI Interview Simulator

IntervAI is a premium AI-powered interview simulator designed to help candidates master their interview skills. Using **ChatGPT** for conversational intelligence, **Whisper** for speech-to-text, and **Google Text-to-Speech**, it provides a realistic, voice-enabled interview experience with constructive feedback.

## ✨ Features

- **Tailored Sessions**: Analyzes your resume and the target job description to generate relevant questions.
- **Voice Interaction**: Speak naturally with the AI interviewer using your microphone.
- **Real-time Feedback**: Receive constructive coaching after each response to improve your performance.
- **Premium UI**: Modern, responsive dashboard built with a focus on user experience.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js & NPM (for asset compilation)
- OpenAI API Key
- Google Cloud Service Account (with TTS/STT enabled)

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Bharat82450-Dare/AI_interview_simulator.git
   cd AI_interview_simulator
   ```

2. **Configure Environment**:
   Copy the example environment file and fill in your API keys.
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI and Google credentials
   ```

3. **Install Dependencies**:
   ```bash
   # Install Python packages
   pip install -r requirements.txt  # Or use pipenv/venv
   
   # Install Frontend packages
   npm install
   ```

4. **Initialize Database**:
   ```bash
   flask db upgrade
   ```

5. **Run the Application**:
   ```bash
   # Build assets
   npm run build
   
   # Start the server
   python autoapp.py
   ```
   Visit `http://localhost:5000` to start your session.

## 🐳 Docker Setup

If you prefer using Docker:
```bash
docker-compose build
docker-compose up
```

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Vanilla CSS, Webpack
- **AI**: OpenAI API (GPT-4, Whisper), Google Cloud TTS

---

Developed by [Bharat82450-Dare](https://github.com/Bharat82450-Dare)
