# Risk Monitor - Financial Analysis Tool

A comprehensive AI-powered financial risk monitoring system that provides real-time news analysis, intelligent insights, and automated market surveillance.

## 🎯 Overview

Risk Monitor is an advanced financial analysis platform that combines:
- **Real-time News Collection** from multiple sources
- **AI-Powered Analysis** using OpenAI GPT-4
- **Vector Database Storage** with Pinecone
- **Automated Scheduling** for continuous monitoring
- **Intelligent Chat Assistant** for financial insights

## 🏗️ Architecture

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Risk Monitor System                      │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)                                       │
│  ├── News Analysis Page                                     │
│  ├── AI Financial Assistant                                 │
│  └── Scheduler Configuration                                │
├─────────────────────────────────────────────────────────────┤
│  Backend Services                                           │
│  ├── News Collector (SerpAPI)                               │
│  ├── Risk Analyzer (OpenAI GPT-4)                           │
│  ├── RAG Service (Vector Search)                            │
│  └── Email Notification System                              │
├─────────────────────────────────────────────────────────────┤
│  Data Storage                                               │
│  ├── Pinecone Vector Database                               │
│  ├── Article Embeddings (3072 dimensions)                   │
│  └── Metadata Storage                                       │
├─────────────────────────────────────────────────────────────┤
│  Background Services                                        │
│  ├── Automated Scheduler                                    │
│  ├── Daily News Collection                                  │
│  └── Email Report Generation                                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
```
1. User Input → Streamlit Interface
2. Entity Selection → Counterparties/Companies
3. News Collection → SerpAPI → Article Extraction
4. AI Analysis → OpenAI GPT-4 → Sentiment & Risk Analysis
5. Vector Storage → Pinecone → Embeddings + Metadata
6. User Query → RAG System → Context Retrieval → AI Response
7. Scheduled Tasks → Background Processing → Email Reports
```

## 🚀 Key Features

### 📊 News Analysis
- **Real-time Collection**: Automated news gathering from financial sources
- **AI Analysis**: Sentiment scoring, risk assessment, and insights generation
- **Entity Monitoring**: Track 92 NASDAQ-100 companies
- **Vector Storage**: Efficient similarity search and retrieval

### 🤖 AI Financial Assistant
- **Conversational AI**: Natural language financial queries
- **RAG Technology**: Retrieval-Augmented Generation for accurate responses
- **Context Awareness**: Understands financial terminology and relationships
- **Real-time Insights**: Access to latest market data and analysis

### ⏰ Automated Scheduler
- **Daily Execution**: Automated news collection and analysis
- **Email Reports**: Comprehensive daily summaries
- **Background Processing**: Continuous market monitoring
- **Configurable**: Flexible scheduling and entity selection

## 📋 Prerequisites

- **Python 3.11+**
- **OpenAI API Key**
- **SerpAPI Key**
- **Pinecone API Key**
- **Email SMTP Configuration** (optional)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/bishugiri/RiskMonitoring.git
cd RiskMonitoring
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** Common dependency issues have been resolved:
- `lxml.html.clean` ImportError: Fixed by including `lxml_html_clean>=0.4.2`
- Pinecone package error: Updated from `pinecone-client` to `pinecone>=7.0.0`
- Scheduler dependency: Added `schedule>=1.2.0` for automated scheduling

These dependencies are automatically installed when you run `pip install -r requirements.txt`.

### 4. Configure Environment
Create `.streamlit/secrets.toml`:
```toml
# OpenAI Configuration
OPENAI_API_KEY = "your_openai_api_key"

# SerpAPI Configuration
SERPAPI_KEY = "your_serpapi_key"

# Pinecone Configuration
PINECONE_API_KEY = "your_pinecone_api_key"
PINECONE_ENVIRONMENT = "us-east-1-aws"
PINECONE_INDEX_NAME = "sentiment-db"

# Email Configuration (Optional)
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
```

## 🚀 Running the Application

### Method 1: Using Shell Script (Recommended)
```bash
# Make script executable
chmod +x run_app.sh

# Run the application
./run_app.sh
```

### Method 2: Direct Python Execution
```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit application
streamlit run risk_monitor/scripts/run_app.py
```

### Method 3: Using Python Module
```bash
# From project root
python3 -m streamlit run risk_monitor/scripts/run_app.py
```

## 🌐 Accessing the Application

Once running, access the application at:
- **Local**: http://localhost:8501
- **Network**: http://your-ip:8501

## 📱 Application Pages

### 1. Dashboard
- **Overview**: System status and recent activity
- **Quick Stats**: Articles processed, entities monitored
- **Recent Articles**: Latest analyzed news

### 2. News Analysis
- **Entity Selection**: Choose from 92 NASDAQ-100 companies
- **Real-time Analysis**: Live sentiment and risk analysis
- **Results Display**: Filtered and categorized results
- **Export Options**: Download analysis results

### 3. AI Financial Assistant
- **Chat Interface**: Natural language financial queries
- **Context Awareness**: Understands financial terminology
- **Real-time Data**: Access to latest market analysis
- **Conversation History**: Persistent chat sessions

### 4. Scheduler Configuration
- **Schedule Settings**: Configure daily execution time
- **Entity Management**: Select companies to monitor
- **Email Configuration**: Set up notification recipients
- **Status Monitoring**: Real-time scheduler status

## ⚙️ Configuration

### Scheduler Configuration
Edit `risk_monitor/scheduler_config.json`:
```json
{
    "run_time": "08:00",
    "timezone": "US/Eastern",
    "articles_per_entity": 5,
    "entities": ["AAPL - Apple Inc", "MSFT - Microsoft Corporation"],
    "email_enabled": true,
    "email_recipients": ["user@example.com"]
}
```

### Application Settings
- **Articles per Entity**: 1-20 (default: 5)
- **Analysis Method**: LLM or Hybrid
- **Cache Duration**: Configurable caching
- **Retry Attempts**: 3 attempts with exponential backoff

## 🔧 Background Services

### Starting the Scheduler
```bash
# Start scheduler manually
python3 risk_monitor/scripts/run_data_refresh.py

# Start scheduler in background
nohup python3 risk_monitor/scripts/run_data_refresh.py > scheduler_background.log 2>&1 &
```

### Monitoring Scheduler Status
```bash
# Check if scheduler is running
pgrep -f "run_data_refresh.py"

# View scheduler logs
tail -f logs/scheduler.log

# View background logs
tail -f scheduler_background.log
```

### Stopping the Scheduler
```bash
# Stop scheduler
pkill -f "run_data_refresh.py"
```

## 📊 Data Structure

### Article Metadata
```json
{
    "title": "Article Title",
    "url": "https://example.com/article",
    "source": "Financial News",
    "published_date": "2025-01-01",
    "article_extracted_date": "2025-01-01",
    "entity": "AAPL - Apple Inc",
    "sentiment_score": 0.75,
    "risk_score": 0.25,
    "sentiment_insight": "Positive sentiment due to strong earnings",
    "risk_insight": "Low risk with stable market position",
    "summary": "Article summary here",
    "sentiment_category": "Positive",
    "risk_category": "Low"
}
```

### Vector Embeddings
- **Model**: OpenAI text-embedding-3-large
- **Dimensions**: 3072
- **Content**: Article title + content
- **Storage**: Pinecone vector database

## 🔍 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python3 --version

# Verify dependencies
pip list

# Check environment variables
echo $OPENAI_API_KEY
```

#### lxml.html.clean ImportError
If you encounter the following error:
```
ImportError: lxml.html.clean module is now a separate project lxml_html_clean.
Install lxml[html_clean] or lxml_html_clean directly.
```

**Solution:**
```bash
# Install the missing dependency
pip install lxml_html_clean

# Or install with lxml extras
pip install lxml[html_clean]
```

This error occurs because the `lxml.html.clean` module was separated into its own package. The `requirements.txt` file has been updated to include this dependency.

#### Pinecone Package Error
If you encounter the following error:
```
Exception: The official Pinecone python package has been renamed from `pinecone-client` to `pinecone`. Please remove `pinecone-client` from your project dependencies and add `pinecone` instead.
```

**Solution:**
```bash
# Uninstall the old package and install the new one
pip uninstall pinecone-client -y
pip install pinecone

# Or update requirements.txt and reinstall
pip install -r requirements.txt
```

This error occurs because Pinecone renamed their official Python package from `pinecone-client` to `pinecone`. The `requirements.txt` file has been updated to use the correct package name.

#### Scheduler Status Issues
If the scheduler shows as "ACTIVE" when it's not actually running, or buttons don't work:

**Solution:**
```bash
# Test the scheduler manually
source venv/bin/activate
python risk_monitor/scripts/run_data_refresh.py --test

# Check if scheduler is actually running
pgrep -f run_data_refresh.py

# Check scheduler logs
tail -f logs/scheduler.log
tail -f scheduler_background.log
```

The UI now includes better status detection and uses the virtual environment's Python for all scheduler operations.

#### Scheduler Not Running
```bash
# Check process status
pgrep -f "run_data_refresh.py"

# Check configuration
cat risk_monitor/scheduler_config.json

# View error logs
tail -f logs/scheduler.log
```

#### API Errors
- **OpenAI**: Verify API key and billing
- **SerpAPI**: Check API key and rate limits
- **Pinecone**: Verify API key and index name

### Log Files
- **Application**: `logs/risk_monitor.log`
- **Scheduler**: `logs/scheduler.log`
- **Background**: `scheduler_background.log`

## 📈 Performance

### Optimization Features
- **Caching**: 1-hour analysis cache, 30-minute sentiment cache
- **Async Processing**: Non-blocking operations
- **Batch Processing**: Efficient bulk operations
- **Connection Pooling**: Reuse database connections

### Monitoring
- **Response Times**: Track API performance
- **Memory Usage**: Monitor resource consumption
- **Error Rates**: Track and analyze failures
- **Cache Hit Rates**: Monitor caching effectiveness

## 🔒 Security

### Security Measures
- **API Key Protection**: Secure environment variable storage
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Respect API rate limits
- **Error Handling**: Don't expose sensitive information

### Privacy
- **No Personal Data**: System doesn't store personal information
- **Data Retention**: Configurable data retention policies
- **Access Control**: Implement user authentication
- **Compliance**: GDPR and data protection compliance

## 📚 Documentation

### Detailed Documentation
- **[News Analysis](NEWS_ANALYSIS_DOCUMENTATION.md)**: Complete news analysis system
- **[AI Financial Assistant](AI_FINANCIAL_ASSISTANT_DOCUMENTATION.md)**: RAG system and chat interface
- **[Scheduler](SCHEDULER_DOCUMENTATION.md)**: Automated background services

### API Documentation
- **OpenAI API**: GPT-4 integration for analysis
- **SerpAPI**: Google Search API for news collection
- **Pinecone API**: Vector database operations

## 🚀 Deployment

### Local Deployment
```bash
# Development
streamlit run risk_monitor/scripts/run_app.py

# Production
gunicorn --bind 0.0.0.0:8501 risk_monitor.scripts.run_app:app
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "risk_monitor/scripts/run_app.py"]
```

## 🤝 Contributing

### Development Setup
```bash
# Fork repository
git clone https://github.com/your-username/RiskMonitoring.git

# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
python3 -m pytest tests/

# Commit changes
git commit -m "Add new feature"

# Push to branch
git push origin feature/new-feature
```
---

**Risk Monitor** - Intelligent Financial Risk Analysis Platform 
