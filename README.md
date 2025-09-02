# 🤖 AI Financial Risk Monitoring System

A comprehensive AI-powered financial risk monitoring system that automatically collects, analyzes, and reports on financial news and market sentiment. Built with Python, Streamlit, and OpenAI's GPT models for advanced sentiment analysis and risk assessment.

## 🚀 Features

### 📰 **Automated News Collection**
- **Real-time News Fetching**: Automatically collects financial news from multiple sources using SerpAPI
- **Company-Specific Monitoring**: Monitor specific companies (NASDAQ-100 support) for risk-related news
- **Keyword Filtering**: Advanced filtering based on risk keywords (financial, market, crisis, volatility, etc.)
- **Scheduled Collection**: Daily automated news collection at configurable times

### 🧠 **AI-Powered Analysis**
- **Dual Sentiment Analysis**: Combines lexicon-based and LLM (GPT-4) sentiment analysis
- **Risk Assessment**: Comprehensive risk analysis across multiple categories
- **AI Financial Assistant**: Interactive chat interface for querying financial data
- **Contextual Understanding**: Advanced NLP for financial context comprehension

### 📊 **Data Management**
- **Pinecone Vector Database**: Scalable vector storage for semantic search
- **Local Storage**: JSON-based local storage with indexing
- **Data Export**: Comprehensive data export in structured formats
- **Historical Analysis**: Track sentiment and risk trends over time

### 📧 **Automated Reporting**
- **Daily Email Reports**: Automated daily summaries sent via SMTP
- **Detailed Analysis**: Comprehensive risk summaries with article links
- **Top Risk Alerts**: Identification of most negative sentiment articles
- **Configurable Recipients**: Multiple email recipient support

### 🎛️ **Configuration & Control**
- **Web-based Configuration**: Interactive scheduler configuration UI
- **Real-time Status Monitoring**: Live scheduler status and process monitoring
- **Email Subscription Controls**: Enable/disable email notifications
- **Flexible Scheduling**: Configurable run times and timezones

## 🏗️ Architecture

```
RiskMonitoring/
├── risk_monitor/                 # Main application package
│   ├── api/                     # Web interface
│   │   └── streamlit_app.py     # Streamlit web application
│   ├── config/                  # Configuration management
│   │   └── settings.py          # Settings and environment config
│   ├── core/                    # Core business logic
│   │   ├── news_collector.py    # News collection engine
│   │   ├── risk_analyzer.py     # Risk and sentiment analysis
│   │   ├── rag_service.py       # AI Financial Assistant
│   │   └── scheduler.py         # Automated scheduling system
│   ├── scripts/                 # Entry point scripts
│   │   ├── run_app.py           # Web app launcher
│   │   └── run_data_refresh.py  # Scheduler launcher
│   └── utils/                   # Utility modules
│       ├── emailer.py           # Email reporting system
│       ├── local_storage.py     # Local data management
│       ├── pinecone_db.py       # Vector database operations
│       └── sentiment.py         # Sentiment analysis utilities
├── output/                      # Generated data files
├── logs/                        # Application logs
├── .streamlit/                  # Streamlit configuration
│   └── secrets.toml            # API keys and credentials
├── scheduler_config.json        # Scheduler configuration
├── requirements.txt             # Python dependencies
└── setup.py                     # Package setup
```

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Git
- API keys for:
  - OpenAI (for GPT-4 analysis)
  - SerpAPI (for news collection)
  - Pinecone (for vector storage)
  - Gmail App Password (for email reports)

### Quick Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd RiskMonitoring
   ```

2. **Run the installation script**:
   ```bash
   python install.py
   ```

3. **Configure API keys**:
   Create `.streamlit/secrets.toml` with your API keys:
   ```toml
   OPENAI_API_KEY = "sk-proj-your-openai-key"
   SERPAPI_KEY = "your-serpapi-key"
   PINECONE_API_KEY = "pcsk-your-pinecone-key"
   
   # Email Configuration
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASSWORD = "your-16-char-app-password"
   EMAIL_FROM = "your-email@gmail.com"
   EMAIL_RECIPIENTS = "recipient@example.com"
   EMAIL_SUBJECT_PREFIX = "Risk Monitor"
   ```

## 🚀 Usage

### Web Application

Launch the interactive web application:

```bash
# Using convenience script
./run_app.sh

# Using Python module
python -m risk_monitor.scripts.run_app

# Using Streamlit directly
streamlit run risk_monitor/api/streamlit_app.py
```

**Access the application at**: http://localhost:8501

### Web Interface Features

#### 📊 **Dashboard**
- Overview of analyzed articles
- Sentiment distribution charts
- Recent analysis results
- System status indicators

#### 📰 **News Analysis**
- **Counterparty-based Search**: Monitor specific companies
- **Custom Query Search**: Use custom search terms
- **Keyword Filtering**: Focus on risk-related content
- **Real-time Analysis**: Immediate sentiment and risk assessment

#### 📄 **PDF Analysis**
- Upload and analyze PDF documents
- Keyword-based content filtering
- Risk assessment for documents
- Export analysis results

#### 🤖 **AI Financial Assistant**
- Interactive chat interface
- Query your financial database
- Get insights about companies and market sentiment
- Access analyzed articles and trends

#### ⏰ **Scheduler Configuration**
- **Schedule Tab**: Configure run times and timezones
- **Companies Tab**: Manage monitored companies (NASDAQ-100 dropdown)
- **Analysis Tab**: Configure keywords and analysis options
- **Email Tab**: Manage email notifications and recipients
- **Monitoring Tab**: Real-time scheduler status and controls

### Automated Scheduler

Set up and run the automated data collection:

```bash
# Set up scheduler configuration
python -m risk_monitor.scripts.run_data_refresh --setup

# Run immediately
python -m risk_monitor.scripts.run_data_refresh --run-now

# Start background scheduler
./run_scheduler_with_email.sh

# Check scheduler status
pgrep -f "run_data_refresh.py"
```

### Email Reports

The system automatically sends daily email reports containing:
- Summary of collected articles
- Sentiment analysis results
- Top 10 most negative articles
- Risk assessment summaries
- Links to original articles

## ⚙️ Configuration

### Scheduler Configuration

Edit `scheduler_config.json` to customize:

```json
{
  "run_time": "08:00",
  "timezone": "US/Eastern",
  "articles_per_entity": 5,
  "entities": ["NVDA", "MSFT", "AAPL", "META", "AMZN"],
  "keywords": ["risk", "financial", "market", "crisis"],
  "use_openai": true,
  "email_enabled": true,
  "enable_pinecone_storage": true,
  "enable_dual_sentiment": true,
  "enable_detailed_email": true
}
```

### Environment Variables

Set these for command-line execution:

```bash
export OPENAI_API_KEY="your-key"
export SERPAPI_KEY="your-key"
export PINECONE_API_KEY="your-key"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

## 🔧 Troubleshooting

### Common Issues

1. **OpenAI API Errors**:
   - Ensure you're using the correct API key format
   - Check your OpenAI account has sufficient credits

2. **Email Not Sending**:
   - Verify Gmail App Password is 16 characters
   - Enable 2-Factor Authentication on Gmail
   - Check SMTP settings in secrets.toml

3. **Pinecone Connection Issues**:
   - Verify Pinecone API key is correct
   - Check your Pinecone index exists and is accessible

4. **Scheduler Not Running**:
   - Check if process is running: `pgrep -f "run_data_refresh.py"`
   - View logs: `tail -f logs/scheduler.log`
   - Restart scheduler: `./run_scheduler_with_email.sh`

### Log Files

- `logs/scheduler.log`: Scheduler activity logs
- `logs/news_collect_*.log`: News collection logs
- `scheduler_background.log`: Background process logs

## 📊 Data Output

### Generated Files

- `output/scheduled_news_*.json`: Collected and analyzed articles
- `output/scheduled_analysis_*.json`: Analysis results
- `output/master_news_articles.json`: Master article database
- `output/local_storage/`: Local article storage with indexing

### Data Structure

Each article contains:
```json
{
  "title": "Article Title",
  "text": "Full article content",
  "url": "Source URL",
  "source": "Source name",
  "publish_date": "2025-01-01T00:00:00",
  "sentiment_analysis": {
    "score": 0.75,
    "category": "Positive",
    "justification": "Analysis explanation"
  },
  "risk_analysis": {
    "risk_score": 0.3,
    "risk_categories": {
      "market": 0.4,
      "economic": 0.2
    }
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

© 2024 Er. Bibit Kunwar Chhetri. All rights reserved.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for errors
3. Ensure all API keys are properly configured
4. Verify system requirements are met

---

**Built with ❤️ for Financial Risk Management**