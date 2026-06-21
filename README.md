# AI Health Triage System 🩺

AI-powered health triage decision support system built for Community Health Workers (CHWs). The system analyzes patient symptoms, processes medical documents, evaluates vitals against age-specific thresholds, and generates comprehensive triage reports with multi-lingual audio summaries and official PDF exports.

## 🌟 Key Features

- **Multi-Modal Intake**: Support for processing patient symptoms via text or voice audio.
- **Document OCR**: Upload medical documents or prescriptions to automatically extract key medical entities (NER) and context.
- **Vitals Anomalies**: Analyzes patient vitals (Blood Pressure, Heart Rate, Temperature, O2, Respiratory Rate) based on their specific age and flags life-threatening anomalies.
- **AI Triage Reasoning**: Leverages advanced LLMs (Gemini / OpenAI) to generate a triage priority score (RED, YELLOW, GREEN), differential diagnoses, first-aid steps, and critical red flags.
- **Multi-Lingual Audio**: Generates Text-to-Speech (TTS) audio summaries in multiple languages (e.g., English, Bengali) for accessibility.
- **PDF Export**: Dynamically generates a beautifully formatted official PDF report of the triage session.

## 🏗️ Architecture & Tech Stack

The application is fully containerized using Docker and is split into two primary microservices:

1. **Backend (`/backend`)**
   - **FastAPI**: A high-performance async REST API.
   - **SQLAlchemy / PostgreSQL**: For persistent storage of triage sessions and patient data.
   - **WeasyPrint**: For rendering HTML templates into high-quality PDF reports.
   - **gTTS**: For generating Text-to-Speech audio files.
   - **Google Generative AI (Gemini)**: For advanced medical reasoning and OCR.

2. **Frontend (`/frontend`)**
   - **Streamlit**: A responsive, custom-styled UI built entirely in Python.
   - Handles file uploads, audio playback, and PDF downloads natively using a proxy architecture.


## 🚀 Quick Start (Docker)

The absolute easiest way to run the system (whether locally, in GitHub Codespaces, or on a remote server) is via Docker Compose.

### 1. Setup Environment Variables

The backend relies on a PostgreSQL database and AI API keys. 

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the example `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Open `backend/.env` and fill in your secrets, particularly your `GEMINI_API_KEY` and your `DATABASE_URL`.

### 2. Run the System

Navigate back to the root directory of the project and run:

```bash
docker-compose up --build
```

This will:
- Build the backend image (installing system dependencies like Pango for PDF generation).
- Build the frontend Streamlit image.
- Start both services on a shared internal Docker network.

### 3. Access the Application

Once the containers are running, simply open your web browser and navigate to:

```text
http://localhost:8501
```

*(If running in GitHub Codespaces, use the forwarded address for port 8501 provided in your Ports tab).*

## 📁 Directory Structure

```text
health-triage-system/
├── docker-compose.yml       # Orchestrates the frontend and backend containers
├── backend/                 # FastAPI Application
│   ├── Dockerfile
│   ├── app/
│   │   ├── api/             # REST endpoints (intake, triage, reports, vitals)
│   │   ├── services/        # Business logic (LLM integrations, PDF generation)
│   │   └── db/              # Database models and session management
│   ├── report_templates/    # HTML/CSS templates for WeasyPrint PDFs
│   ├── uploads/             # Ephemeral storage for audio/PDF files
│   └── .env                 # Backend secrets (API keys, DB connection)
└── frontend/                # Streamlit UI
    ├── Dockerfile
    ├── app.py               # Main UI layout and logic
    ├── api_client.py        # Connects Streamlit to the FastAPI backend
    └── requirements.txt
```

## ⚠️ Disclaimer

> **IMPORTANT**: This application is a **decision support tool** designed demonstration purposes. It does not replace professional medical judgment. All triage recommendations should be verified by a qualified healthcare professional.