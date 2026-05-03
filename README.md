# 🚀 InterviewFocus AI Prep Copilot

**InterviewFocus AI Prep Copilot** is a high-performance, NLP-powered workspace designed to transform raw job descriptions and recruiter notes into actionable interview preparation assets. It leverages state-of-the-art transformer models to provide intent-aware guidance, comparative summarization, and deep analytical insights.

---

## ✨ Core Features

### 🧠 Advanced NLP Engine
- **Intent-Aware Chat**: Built on a zero-shot classification pipeline (DistilRoBERTa) that detects user needs—from role clarification to general prep advice—and responds with context-specific guidance.
*   **Dual-Model Summarization**: Generate side-by-side summaries using:
    - **BART (sshleifer/distilbart-cnn-12-6)**: For detailed, high-retention role briefs.
    - **T5 (t5-small)**: For concise, scannable recruiter-style summaries.

### 📊 Evaluation & Analytics
- **ROUGE Metrics**: Real-time performance evaluation comparing summary coverage against source text (ROUGE-1, ROUGE-2, ROUGE-L).
- **Readability Scoring**: Automated Flesch Reading Ease analysis to ensure prep materials are accessible and clear.
- **Performance Benchmarking**: Comparative tracking of model response times and token retention rates.

### 🎙️ Interactive Simulation
- **Gemini Integration**: Dynamic generation of tailored interview questions based on job descriptions and candidate resumes.
- **Voice-to-Text Transcription**: Native support for transcribing practice answers using Gemini's multi-modal capabilities.
- **Neural TTS**: High-quality Google Cloud Text-to-Speech integration for a realistic interview experience.

---

## 🛠️ Technology Stack

- **Backend**: Python / Flask
- **AI/ML**: HuggingFace Transformers, Google Gemini 1.5/2.0
- **Database**: SQLAlchemy (SQLite for development)
- **Frontend**: Premium Vanilla CSS, Webpack, HTMX for dynamic interactions
- **Evaluation**: ROUGE-Score, Flesch-Kincaid Readability

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **Node.js 18+** & NPM
- **Google AI Studio API Key** (for Gemini features)
- **Google Cloud Service Account** (for Text-to-Speech)

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/Bharat82450-Dare/AI_interview_simulator.git
cd AI_interview_simulator

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies
npm install
```

### 2. Configuration
Copy the example environment file and add your API keys:
```bash
cp .env.example .env
# Open .env and fill in:
# GOOGLE_API_KEY=...
# GOOGLE_APPLICATION_CREDENTIALS=serviceAccountKey.json
```

### 3. Database Initialization
```bash
flask db upgrade
```

### 4. Running the Application
The easiest way to run the project in development mode (with hot-reloading for assets) is:
```bash
npm start
```
Alternatively, you can run the components separately:
```bash
# Build static assets
npm run build

# Start the Flask server
python -m flask run
```
Visit `http://localhost:5000` to begin your prep session.

---

## 📂 Project Structure
- `interview_simulator/user/nlp_lab_service.py`: Core logic for Transformers and summarization.
- `interview_simulator/user/services.py`: Gemini and Google Cloud integrations.
- `assets/`: Source JS and CSS (processed by Webpack).
- `interview_simulator/templates/`: Premium Jinja2 templates.

---

Developed with ❤️ by [Bharat82450-Dare](https://github.com/Bharat82450-Dare)

