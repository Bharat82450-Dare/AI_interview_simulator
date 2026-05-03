# IntervAI: AI Interview Simulator

IntervAI is a premium AI-powered interview simulator designed to help candidates master their interview skills. Powered by **Gemini Flash 2.0 Lite**, it provides a realistic, voice-enabled interview experience with constructive feedback and real-time transcription.

## ✨ Features

- **Gemini Powered**: Uses **Gemini Flash 2.0 Lite** for conversational intelligence, question generation, and audio transcription.
- **Tailored Sessions**: Analyzes your resume and the target job description to create a customized interview flow.
- **Voice Interaction**: Speak naturally with the AI interviewer; responses are synthesized using **Google Text-to-Speech**.
- **Real-time Feedback**: Receive instant coaching and scoring based on semantic similarity and keyword coverage.
- **Premium UI**: Modern, responsive dashboard focused on professional growth.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js & NPM (for asset compilation)
- Google AI Studio API Key (for Gemini)
- Google Cloud Service Account (for Text-to-Speech)

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
   # Edit .env with your GOOGLE_API_KEY and credentials
   ```

3. **Install Dependencies**:
   ```bash
   # Install Python packages
   pip install -r requirements.txt
   
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

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **AI Engine**: Gemini Flash 2.0 Lite (via Google Generative AI SDK)
- **Voice**: Google Cloud Text-to-Speech
- **Database**: SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Vanilla CSS, Webpack

---

Developed by [Bharat82450-Dare](https://github.com/Bharat82450-Dare)
