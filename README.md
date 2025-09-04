# AI Financial Risk Monitoring System

A comprehensive AI-powered financial risk monitoring system that automatically collects, analyzes, and reports on financial news and market sentiment. Built with Python, Streamlit, and OpenAI's GPT models for advanced sentiment analysis and risk assessment.

## 🚀 Features

### Automated News Collection
- **Real-time News Fetching**: Automatically collects financial news from multiple sources using SerpAPI
- **Company-Specific Monitoring**: Monitor specific companies (NASDAQ-100 support) for risk-related news
- **Keyword Filtering**: Advanced filtering based on risk keywords (financial, market, crisis, volatility, etc.)
- **Scheduled Collection**: Daily automated news collection at configurable times

### AI-Powered Analysis
- **Dual Sentiment Analysis**: Combines lexicon-based and LLM (GPT-4) sentiment analysis
- **Risk Assessment**: Comprehensive risk analysis across multiple categories
- **AI Financial Assistant**: Interactive chat interface with advanced filtering (Date → Entity → Query)
- **Contextual Understanding**: Advanced NLP for financial context comprehension

### Data Management
- **Pinecone Vector Database**: Scalable vector storage for semantic search
- **Local Storage**: JSON-based local storage with indexing
- **Data Export**: Comprehensive data export in structured formats
- **Historical Analysis**: Track sentiment and risk trends over time

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

## 🏗️ Architecture

### System Architecture Overview

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

### Project Structure

```
RiskMonitoring/
├── risk_monitor/                 # Main application package
│   ├── api/                     # Web interface layer
│   │   └── streamlit_app.py     # Streamlit web application
│   │                           # - Dashboard, News Analysis
│   │                           # - AI Financial Assistant, Scheduler Config
│   │
│   ├── config/                  # Configuration management layer
│   │   └── settings.py          # Settings and environment configuration
│   │                           # - API key management, environment variables
│   │
│   ├── core/                    # Core business logic layer
│   │   ├── news_collector.py    # News collection engine
│   │   │                       # - SerpAPI integration, article extraction
│   │   │                       # - Content parsing, metadata extraction
│   │   │
│   │   ├── risk_analyzer.py     # Risk and sentiment analysis engine
│   │   │                       # - Dual sentiment analysis (lexicon + LLM)
│   │   │                       # - Risk categorization, scoring algorithms
│   │   │
│   │   ├── rag_service.py       # RAG (Retrieval-Augmented Generation) service
│   │   │                       # - Semantic search, article retrieval
│   │   │                       # - AI Financial Assistant backend
│   │   │                       # - Advanced filtering: Date → Entity → Query
│   │   │
│   │   └── scheduler.py         # Automated scheduling engine
│   │                           # - Daily news collection and analysis
│   │                           # - Email reporting, status monitoring
│   │
│   ├── utils/                   # Utility and helper functions
│   │   ├── pinecone_db.py       # Pinecone vector database integration
│   │   │                       # - Vector storage, similarity search
│   │   │                       # - Metadata management, indexing
│   │   │
│   │   ├── sentiment.py         # Sentiment analysis utilities
│   │   │                       # - Lexicon-based sentiment analysis
│   │   │                       # - Text preprocessing, scoring algorithms
│   │   │
│   │   └── emailer.py           # Email system utilities
│   │                           # - SMTP integration, HTML email formatting
│   │                           # - Daily reports, risk alerts
│   │
│   ├── scripts/                 # Scripts and entry points
│   │   ├── run_app.py          # Web application entry point
│   │   └── run_data_refresh.py # Scheduler entry point
│   │
│   └── models/                  # Data models and schemas
│
├── logs/                        # Application logs
│   ├── risk_monitor.log        # Main application logs
│   └── scheduler.log           # Scheduler-specific logs
│
├── output/                      # Output and export files
├── venv/                        # Python virtual environment
├── .streamlit/                  # Streamlit configuration
├── .git/                        # Git version control
│
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── setup.py                     # Installation script
├── install.py                   # Automated setup script
├── run_app.sh                   # Web app startup script
├── run_scheduler_with_email.sh  # Scheduler startup script
├── scheduler_config.json        # Scheduler configuration
├── .gitignore                   # Git ignore rules
└── app.log                      # Application log file
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Git
- Required API keys (see Configuration section)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RiskMonitoring
   ```

2. **Run automated setup**
   ```bash
   python install.py
   ```

3. **Configure API keys** (see Configuration section)

4. **Start the web application**
   ```bash
   ./run_app.sh
   ```

### Manual Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (see Configuration section)

4. **Start the application**
   ```bash
   python -m risk_monitor.scripts.run_app
   ```

## ⚙️ Configuration

### Required API Keys

Set the following environment variables:

```bash
# News Collection
export SERPAPI_KEY="your_serpapi_key"

# AI Analysis
export OPENAI_API_KEY="your_openai_api_key"

# Vector Database
export PINECONE_API_KEY="your_pinecone_api_key"

# Email Notifications (Optional)
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"
export EMAIL_FROM="your_email@gmail.com"
export EMAIL_RECIPIENTS="recipient1@email.com,recipient2@email.com"
export EMAIL_SUBJECT_PREFIX="Risk Monitor"
```

### Configuration Files

- **`scheduler_config.json`**: Scheduler settings, email preferences, monitoring targets
- **`.streamlit/config.toml`**: Streamlit application configuration

## 🚀 Usage

### Web Interface

1. **Start the application**
   ```bash
   ./run_app.sh
   ```

2. **Access the web interface**
   - Open browser to `http://localhost:8501`
   - Navigate through Dashboard, News Analysis, AI Financial Assistant

### AI Financial Assistant

The AI Financial Assistant uses an advanced filtering system:

1. **Select Company/Entity**: Choose from available companies
2. **Select Date**: Choose specific date or "All Dates"
3. **Ask Questions**: Get AI-powered insights about financial data

**Filtering Flow**: Date → Entity → Query (optimized for speed and accuracy)

### Automated Scheduler

1. **Start the scheduler**
   ```bash
   ./run_scheduler_with_email.sh
   ```

2. **Configure via web interface**
   - Set monitoring targets
   - Configure email preferences
   - Set schedule times

## 📊 Key Components

### News Collector (`risk_monitor/core/news_collector.py`)
- SerpAPI integration for news fetching
- Article extraction and parsing
- Metadata management
- Content filtering

### Risk Analyzer (`risk_monitor/core/risk_analyzer.py`)
- Dual sentiment analysis (lexicon + LLM)
- Risk categorization and scoring
- Comprehensive risk assessment
- AI-powered analysis

### RAG Service (`risk_monitor/core/rag_service.py`)
- Semantic search capabilities
- AI Financial Assistant backend
- Advanced filtering system
- Context management

### Pinecone Integration (`risk_monitor/utils/pinecone_db.py`)
- Vector database management
- Similarity search
- Metadata storage
- Scalable data handling

## 🔍 Advanced Features

### Filtering System
- **Date Filtering**: Temporal relevance filtering
- **Entity Filtering**: Company-specific filtering
- **Query Filtering**: Semantic similarity search
- **Combined Approach**: Date → Entity → Query for optimal performance

### Email Reporting
- **Daily Summaries**: Automated daily reports
- **Risk Alerts**: Top negative sentiment articles
- **Detailed Analysis**: Comprehensive risk assessment
- **HTML Formatting**: Professional email formatting

### Data Management
- **Vector Storage**: Pinecone for semantic search
- **Local Storage**: JSON-based local storage
- **Data Export**: Structured data export
- **Historical Tracking**: Trend analysis over time

## 🛠️ Development

### Project Structure
- **Modular Design**: Clean separation of concerns
- **Configurable**: Environment-based configuration
- **Extensible**: Easy to add new features
- **Maintainable**: Well-documented code

### Adding New Features
1. **Core Logic**: Add to `risk_monitor/core/`
2. **Utilities**: Add to `risk_monitor/utils/`
3. **UI Components**: Add to `risk_monitor/api/`
4. **Configuration**: Update `risk_monitor/config/`

### Testing
- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

## 📈 Performance

### Optimizations
- **Efficient Filtering**: Date → Entity → Query reduces processing by 95%
- **Vector Search**: Pinecone for fast semantic search
- **Caching**: Intelligent caching of frequently accessed data
- **Batch Processing**: Efficient batch operations

### Scalability
- **Vector Database**: Pinecone scales with data growth
- **Modular Architecture**: Easy to scale individual components
- **Configuration-Driven**: Flexible configuration for different scales

## 🔒 Security

### API Key Management
- **Environment Variables**: Secure API key storage
- **No Hardcoding**: Keys never stored in code
- **Access Control**: Proper access controls

### Data Privacy
- **Local Processing**: Sensitive data processed locally
- **Secure Storage**: Encrypted storage where needed
- **Access Logging**: Comprehensive access logging

## 📝 Logging

### Log Files
- **`logs/risk_monitor.log`**: Main application logs
- **`logs/scheduler.log`**: Scheduler-specific logs
- **`app.log`**: Application-level logs

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests
5. Submit pull request

### Code Standards
- **PEP 8**: Python code style
- **Type Hints**: Use type annotations
- **Documentation**: Comprehensive docstrings
- **Testing**: Maintain test coverage

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues
- **API Key Errors**: Verify all API keys are set correctly
- **Import Errors**: Ensure virtual environment is activated
- **Database Errors**: Check Pinecone connection and credentials

### Getting Help
- **Documentation**: Check this README and code comments
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Version History

### Current Version
- **v2.0**: Advanced filtering system, improved performance
- **v1.0**: Initial release with basic functionality

### Roadmap
- **v2.1**: Enhanced AI capabilities
- **v2.2**: Additional data sources
- **v3.0**: Advanced analytics and reporting
