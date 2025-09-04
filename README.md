# AI Financial Risk Monitoring System

A comprehensive AI-powered financial risk monitoring system that automatically collects, analyzes, and reports on financial news and market sentiment. Built with Python, Streamlit, and OpenAI's GPT models for advanced sentiment analysis and risk assessment.

## Features

### AI-Powered Analysis
- **Dual Sentiment Analysis**: Combines lexicon-based and LLM (GPT-4) sentiment analysis
- **Intelligent RAG System**: Advanced query classification for diverse question types
- **Risk Assessment**: Comprehensive risk analysis across multiple categories
- **AI Financial Assistant**: Interactive chat interface with specialized response handling

### Automated News Collection
- **Real-time News Fetching**: Automatically collects financial news from multiple sources
- **Company-Specific Monitoring**: Monitor specific companies
- **Keyword Filtering**: Advanced filtering based on risk keywords
- **Scheduled Collection**: Daily automated news collection at configurable times

### Data Management
- **Pinecone Vector Database**: Scalable vector storage for semantic search
- **Local Storage**: JSON-based local storage with indexing
- **Historical Analysis**: Track sentiment and risk trends over time
- **Rich Metadata**: Complete article data with sentiment scores, risk analysis, and timestamps

### Automated Reporting
- **Daily Email Reports**: Automated daily summaries sent via SMTP
- **Detailed Analysis**: Comprehensive risk summaries with article links
- **Top Risk Alerts**: Identification of most negative sentiment articles
- **Configurable Recipients**: Multiple email recipient support

### Configuration & Control
- **Web-based Configuration**: Interactive scheduler configuration UI
- **Real-time Status Monitoring**: Live scheduler status and process monitoring
- **Email Subscription Controls**: Enable/disable email notifications
- **Flexible Scheduling**: Configurable run times and timezones

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI Financial Risk Monitoring System                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐           │
│   │  Web Interface  │   │    Scheduler    │   │ AI Financial    │           │
│   │   (Streamlit)   │   │  (Background)   │   │   Assistant     │           │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘           │
│            │                  │                     │                       │
│            └──────────────────┼─────────────────────┘                       │
│                                │                                            │
│   ┌────────────────────────────┼─────────────────────────────────────────┐  │
│   │                   Core Business Logic Layer                          │  │
│   │   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────┐│  │
│   │   │ News Collector│ │ Risk Analyzer │ │   RAG Service │ │ Scheduler ││  │
│   │   └───────────────┘ └───────────────┘ └───────────────┘ └───────────┘│  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│   ┌────────────────────────────┼─────────────────────────────────────────┐  │
│   │                   Data Management Layer                              │  │
│   │   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────┐│  │
│   │   │ Local Storage │ │  Pinecone DB  │ │  Email System │ │ File Sys. ││  │
│   │   └───────────────┘ └───────────────┘ └───────────────┘ └───────────┘│  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│   ┌────────────────────────────┼─────────────────────────────────────────┐  │
│   │                   External Services Layer                            │  │
│   │   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────┐│  │
│   │   │    SerpAPI    │ │    OpenAI     │ │   Pinecone    │ │   Gmail   ││  │
│   │   │  (News Data)  │ │ (GPT Models)  │ │  (Vector DB)  │ │  (SMTP)   ││  │
│   │   └───────────────┘ └───────────────┘ └───────────────┘ └───────────┘│  │
│   └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.11.13
- OpenAI API key
- Pinecone API key
- SerpAPI key
- Gmail account (App Password)

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd RiskMonitoring

# Install dependencies
pip install -r requirements.txt

# Run the installation script
python install.py

# Start the application
./run_app.sh
```

### Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-key"
export PINECONE_API_KEY="your-pinecone-key"
export SERPAPI_KEY="your-serpapi-key"

# Run the application
streamlit run risk_monitor/api/streamlit_app.py
```

## Usage

### Web Interface
```bash
# Start the Streamlit application
streamlit run risk_monitor/api/streamlit_app.py
```

The web interface provides:
- **Dashboard**: Overview of collected data and analysis
- **News Analysis**: Browse and analyze collected articles
- **AI Financial Assistant**: Interactive chat with specialized query handling
- **Scheduler Config**: Configure automated news collection

### AI Financial Assistant

Ask questions in natural language:

```python
# Sentiment Analysis
"What's the overall sentiment trend for Apple?"

# Risk Analysis  
"Which articles have the highest risk scores?"

# Article Retrieval
"Give me the full article about Apple's AI strategy"

# Comparison
"Compare Apple vs Microsoft sentiment"

# Data Queries
"How many articles do we have about Tesla?"
```

### Automated Scheduler
```bash
# Start the background scheduler
./run_scheduler_with_email.sh

# Or run manually
python risk_monitor/scripts/run_data_refresh.py
```

## Project Structure

```
RiskMonitoring/
├── risk_monitor/                 # Main application package
│   ├── api/                     # Web interface layer
│   │   └── streamlit_app.py     # Streamlit web application
│   ├── config/                  # Configuration management
│   │   └── settings.py          # Settings and environment configuration
│   ├── core/                    # Core business logic
│   │   ├── news_collector.py    # News collection engine
│   │   ├── risk_analyzer.py     # Risk and sentiment analysis
│   │   ├── rag_service.py       # RAG service with query classification
│   │   └── scheduler.py         # Automated scheduling
│   ├── utils/                   # Utility modules
│   │   ├── emailer.py          # Email notification system
│   │   ├── pinecone_db.py      # Pinecone database interface
│   │   └── sentiment.py         # Sentiment analysis utilities
│   ├── scripts/                 # Utility scripts
│   │   ├── run_app.py          # Application entry point
│   │   ├── run_data_refresh.py # Data refresh script
│   │   └── performance_monitor.py # Performance monitoring
│   ├── data/                    # Data storage
│   └── models/                  # Data models
├── logs/                        # Application logs
├── output/                      # Data output directory
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
└── README.md                    # This file
```

## Configuration

### Environment Variables
Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-openai-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
SERPAPI_KEY = "your-serpapi-key"
GMAIL_USER = "your-gmail@gmail.com"
GMAIL_PASSWORD = "your-app-password"
```

### Scheduler Configuration
Configure automated news collection through the web interface or edit `scheduler_config.json`:

```json
{
  "enabled": true,
  "run_time": "09:00",
  "timezone": "UTC",
  "email_notifications": true,
  "companies": ["AAPL", "MSFT", "GOOGL"]
}
```

## Testing

```bash
# Test the improved RAG system
python test_improved_rag.py

# Test performance optimizations
python test_performance.py

# Test structured sentiment analysis
python test_structured_sentiment.py
```

