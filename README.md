# AlphaRescue 🚨

> **"First to know, First to act!"**

An AI-powered emergency dispatch system designed to rapidly respond to distress calls by intelligently coordinating with emergency authorities.

**🏆 Winner: Fetch AI Best Use of Fetch AI - UC Berkeley AI Hackathon 2025**

## 🌟 Overview

AlphaRescue revolutionizes emergency response by combining cutting-edge AI technologies with autonomous agent networks to create a faster, more intelligent dispatch system. Our platform processes emergency calls in real-time, automatically assesses situations, and coordinates with the appropriate emergency services.

## ✨ Key Features

- **🎙️ Voice-based AI Assistant**: Powered by VAPI for natural emergency call handling
- **📝 Real-time Call Transcription**: Automatic summarization using Gemini AI
- **🤖 Autonomous Agent Network**: Intelligent situation assessment and resource allocation
- **🏥 Smart Facility Selection**: Geolocation-based hospital and emergency service matching
- **📊 Real-time Dashboard**: Live incident monitoring and tracking
- **🚑 Intelligent Ambulance Dispatch**: Automated selection of appropriate ambulance types


## 🛠️ Technologies Used

### Frontend
- **React.js** with TypeScript
- **Tailwind CSS** for styling
- **Mapbox GL** for mapping
- **Lucide React** for icons

### Backend
- **Node.js** with Express
- **Python** for AI agents
- **Fetch.ai uAgents** for autonomous agents
- **Supabase** for database and real-time features

### AI & ML
- **Gemini AI** for transcription and summarization
- **Groq LLM** for fast inference
- **OpenAI** for additional AI capabilities

### Infrastructure
- **Vercel** for deployment
- **VAPI** for voice integration

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python 3.8+
- Supabase account
- API keys for Gemini, Groq, and VAPI

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Alpha-Rescue.git
   cd Alpha-Rescue
   ```

2. **Setup Frontend Dashboard**
   ```bash
   cd Dashboard/dashboard-frontend
   npm install
   npm start
   ```

3. **Setup Backend Dashboard**
   ```bash
   cd Dashboard/dashboard-backend
   npm install
   npm start
   ```

4. **Setup Python Agents**
   ```bash
   cd fetch-agent-fire-responder
   pip install -r requirements.txt
   python Orchestrator.py
   ```

### Environment Variables

Create `.env` files in the respective directories with:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# AI Services
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key

# VAPI
VAPI_API_KEY=your_vapi_key

# Mapbox
MAPBOX_ACCESS_TOKEN=your_mapbox_token
```

## 📁 Project Structure

```
Alpha-Rescue/
├── Dashboard/
│   ├── dashboard-frontend/     # React frontend application
│   │   ├── src/
│   │   │   ├── components/     # React components
│   │   │   └── types.ts        # TypeScript definitions
│   │   └── package.json
│   └── dashboard-backend/      # Express.js backend
│       ├── server.js           # Main server file
│       └── package.json
└── fetch-agent-fire-responder/ # Python agents
    ├── Orchestrator.py         # Main orchestrator agent
    ├── paramedic/              # Paramedic agents
    │   ├── ambulance_agent.py  # Ambulance dispatch logic
    │   └── groq_classifier.py  # AI classification
    ├── hospital_agent.py       # Hospital matching agent
    ├── firestation_lookup_agent.py # Fire station agent
    ├── police_integration.py   # Police coordination
    └── requirements.txt        # Python dependencies
```

## 🎯 How It Works

1. **Emergency Call Received**: VAPI processes incoming voice calls
2. **Real-time Transcription**: Gemini AI transcribes and summarizes the call
3. **Agent Network Activation**: Fetch.ai agents assess the situation
4. **Resource Allocation**: System identifies optimal emergency services
5. **Dispatch Coordination**: Automated coordination with hospitals, fire stations, or police
6. **Real-time Monitoring**: Dashboard provides live updates on incident status

## 🏆 Achievements

- **UC Berkeley AI Hackathon 2025 Winner**: Fetch AI Best Use of Fetch AI
- Successfully demonstrated end-to-end emergency response automation
- Integrated multiple AI technologies into a cohesive system
- Built scalable microservice architecture

## 🚧 Challenges Overcome

- **Multi-agent Communication**: Synchronized communication between distributed agents
- **Agent Registration Management**: Efficient handling of agent lifecycle
- **Spam Call Detection**: AI-powered filtering of non-emergency calls
- **LLM Edge Cases**: Robust handling of AI classification uncertainties

## 🔮 What's Next

- **Trust & Reputation Layer**: Add reliability scoring for emergency services
- **Multi-modal Support**: Voice, text, and image-based emergency reporting
- **Extended Coverage**: Support for fire department and police emergencies
- **Mobile-first Frontend**: Dedicated mobile application
- **Custom Model Training**: Train internal models with incident data
- **Real-world Deployment**: Partner with emergency services for pilot programs


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please feel free to submit a Pull Request.

## 📞 Contact

For questions or support, please reach out to the team through our [GitHub repository](https://github.com/yourusername/Alpha-Rescue).

---

**AlphaRescue** - Transforming emergency response through AI innovation. 🚑✨