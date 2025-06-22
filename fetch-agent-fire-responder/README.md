# AI-Powered Emergency Dispatch System

This project implements a sophisticated multi-agent system using [Fetch.ai's uAgents](https://fetch.ai/docs/uagent) to automate the dispatch of emergency services. The system receives emergency call data, uses Google's Gemini AI to analyze the situation, and intelligently dispatches the appropriate units (Police, Fire, and Ambulance/Hospital).

## System Architecture

The system is orchestrated by a central agent that delegates tasks to specialized agents. Each agent is responsible for a specific part of the dispatch process, from finding the nearest station to logging the incident with a backend service.

```mermaid
graph TD
    subgraph "External Services"
        Incoming_Request[External Request<br>(e.g., VAPI Webhook)]
        Backend_API[Backend API]
        Google_Services[Google APIs<br>(Maps, Gemini)]
        Supabase_DB[Supabase DB]
    end

    subgraph "Multi-Agent System"
        Orchestrator
        Police_Agent
        Fire_Agent
        Hospital_Agent
    end
    
    Incoming_Request --"1. Call Transcript"--> Orchestrator
    
    Orchestrator --"2. Analyze & Classify"--> Google_Services
    Google_Services --"Analysis Result"--> Orchestrator
    
    Orchestrator --"3. Dispatch Task"--> Police_Agent
    Orchestrator --"3. Dispatch Task"--> Fire_Agent
    Orchestrator --"3. Dispatch Task"--> Hospital_Agent
    
    Police_Agent --"4. Find Station"--> Google_Services
    Fire_Agent --"4. Find Station"--> Google_Services
    Hospital_Agent --"4. Classify & Find Hospital"--> Google_Services
    Hospital_Agent --"RAG for Medical Needs"--> Supabase_DB
    
    Police_Agent --"5. Log Dispatch"--> Backend_API
    Fire_Agent --"5. Log Dispatch"--> Backend_API
    Hospital_Agent --"5. Log Dispatch"--> Backend_API
```

## Features

- **Automated Incident Classification**: Uses Google Gemini to parse natural language from call transcripts and determine which emergency services are required.
- **Multi-Agent Architecture**: Built with Fetch.ai's uAgents, allowing for a modular, scalable, and resilient system where each agent has a specific role.
- **Intelligent Dispatch**:
    - **Police**: Locates the nearest police station and can be triggered via messages or a manual REST endpoint.
    - **Fire**: Locates the nearest fire station.
    - **Hospital/Ambulance**: Features a more complex sub-system that uses Retrieval-Augmented Generation (RAG) with a Supabase vector database to classify specific medical needs and find the most appropriate hospital.
- **Third-Party Integrations**:
    - **Google Maps API**: For geocoding, reverse geocoding, and finding nearby facilities.
    - **VAPI**: For making automated outbound notification calls.
    - **Supabase**: Used as a vector database for the RAG system.
- **Backend Logging**: Reports the final dispatched details to a central backend API for tracking and record-keeping.

## Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites

- Python 3.10+
- `pip` for package management
- An active internet connection

### 2. Installation

First, clone the repository to your local machine:
```bash
git clone <your-repository-url>
cd fetch-agent-fire-responder
```

Next, create a virtual environment and install the required Python packages:
```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

This project requires several API keys and environment variables to function correctly. Create a file named `.env` in the root of the project directory and populate it with the following keys.

```env
# Google Cloud Platform
GEMINI_API_KEY="your_google_gemini_api_key"
GOOGLE_API_KEY="your_google_maps_api_key"

# Supabase (for Hospital RAG)
SUPABASE_URL="your_supabase_project_url"
SUPABASE_KEY="your_supabase_anon_key"

# VAPI (for outbound calls)
VAPI_AUTH_TOKEN="your_vapi_auth_token"
VAPI_ASSISTANT_ID="your_vapi_assistant_id"
PHONE_NUMBER_ID="your_vapi_phone_number_id"
RECIPIENT_PHONE_NUMBER="the_number_to_call_for_notifications"

# Custom Backend
BACKEND_URL="http://your-backend-service.com/api/endpoint"

# Agent Addresses (Generated on first run)
# Run each agent once to get its address, then paste it here.
FIRE_DID="agent1q..."
POLICE_DID="agent1q..."
AMBULANCE_DID="agent1q..."
```

## Running the System

Each core agent runs in its own process. You will need to open a separate terminal for each one. Make sure your virtual environment is activated in each terminal.

1.  **Run the Orchestrator Agent**:
    ```bash
    python Orchestrator.py
    ```

2.  **Run the Police Agent**:
    ```bash
    python police_integration.py
    ```

3.  **Run the Fire Station Agent**:
    ```bash
    python firestation_lookup_agent.py
    ```

4.  **Run the Hospital Agent / Paramedic Bureau**:
    The hospital and paramedic agents are more complex and may be run as a `Bureau`.
    ```bash
    # Run the hospital agent
    python hospital_agent.py

    # Run the paramedic agent system
    python paramedic/main.py 
    ```

**Note:** When you run an agent for the first time, it will print its unique address (DID) to the console. You may need to copy these addresses into your `.env` file for the `Orchestrator` to find them.

## Key Files

- `Orchestrator.py`: The central agent that coordinates all dispatch activities.
- `police_integration.py`: Handles all police-related dispatch logic.
- `firestation_lookup_agent.py`: Handles all fire-station-related dispatch logic.
- `hospital_agent.py`: The main agent for the hospital sub-system.
- `rag_classifier.py`: Implements the RAG logic for classifying medical emergencies.
- `paramedic/`: Directory containing the ambulance dispatch sub-system.
- `requirements.txt`: A list of all Python dependencies.
- `.env.example`: A template for the required environment variables (you should create a `.env` file from this).

---

This README provides a comprehensive guide to understanding, setting up, and running your multi-agent system. 