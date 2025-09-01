# Risk Monitoring Tool

A comprehensive tool for monitoring financial risks by collecting and analyzing news articles from various sources using SerpAPI, with support for counterparty-based monitoring, keyword filtering, and PDF document analysis.

## Features

- 🔍 **News Collection**: Automatically searches and collects finance news articles using SerpAPI
- 🏢 **Counterparty Monitoring**: Monitor specific companies/organizations for risk-related news
- 🔍 **Keyword Filtering**: Filter articles based on custom keywords to focus on relevant content
- 📄 **PDF Analysis**: Upload and analyze PDF documents for risk assessment
- 🧭 **Dual Data Sources**: Navigate between news search and PDF analysis modes
- 📊 **Risk Analysis**: Analyzes articles for various risk categories (market, economic, geopolitical, sector)
- 📈 **Sentiment Analysis**: Calculates sentiment scores to gauge market mood
- 💾 **Data Export**: Saves collected articles and analysis results in JSON format
- 📋 **Detailed Reporting**: Provides comprehensive risk summaries and top risk identification
- 🔧 **Configurable**: Customizable search queries, article counts, and analysis parameters
- 🌐 **Web Interface**: Interactive Streamlit web application with navigation
- ⏱️ **Automated Data Refresh**: Daily scheduled data collection and analysis

## Project Structure

```
risk_monitor/
├── api/                    # API and web interface
│   └── streamlit_app.py    # Web application interface
├── config/                 # Configuration settings
│   └── settings.py         # Main configuration module
├── core/                   # Core functionality
│   ├── news_collector.py   # News collection module
│   ├── risk_analyzer.py    # Risk analysis module
│   └── scheduler.py        # Automated data refresh scheduler
├── data/                   # Data storage and management
├── models/                 # Data models and schemas
├── scripts/                # Entry point scripts
│   ├── run_data_refresh.py # Script to run the data refresh scheduler
│   └── run_app.py          # Script to run the web application
└── utils/                  # Utility functions
    └── sentiment.py        # Sentiment analysis utilities
```

## Installation

See [QUICKSTART.md](QUICKSTART.md) for a quick installation guide or [USAGE.md](USAGE.md) for detailed instructions.

### Quick Install

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
   - Edit `.streamlit/secrets.toml` with your API keys:
     ```toml
     OPENAI_API_KEY = "your_openai_api_key_here"
     SERPAPI_KEY = "your_serpapi_key_here"
     PINECONE_API_KEY = "your_pinecone_api_key_here"
     ```

## Usage

### Web Interface

Launch the interactive web application:

```bash
# Using the convenience scripts
./run_app.sh  # On macOS/Linux
run_app.bat   # On Windows

# Using the Python module
python -m risk_monitor.scripts.run_app
```

### Data Refresh Scheduler

Set up and run the automated data collection scheduler:

```bash
# Set up the scheduler configuration
python -m risk_monitor.scripts.run_data_refresh --setup

# Run the scheduler immediately
python -m risk_monitor.scripts.run_data_refresh --run-now

# Start the scheduler daemon
python -m risk_monitor.scripts.run_data_refresh
```

For more detailed usage instructions, see [USAGE.md](USAGE.md).

## Automated Daily Data Refresh

The scheduler runs daily at 8:00 AM ET (configurable) and performs the following tasks:

1. Fetches articles for each entity via SerpAPI
2. Uses OpenAI API for sentiment analysis with reasoning
3. Assigns sentiment labels (Positive, Neutral, Negative) and numerical scores
4. Saves results to JSON files in the output directory

## Configuration

The tool uses multiple configuration files:

- **`.streamlit/secrets.toml`**: API keys and secrets
- **`scheduler_config.json`**: Scheduler configuration
- **`risk_monitor/config/settings.py`**: General application settings

## Output

The tool generates different types of output files in the `output/` directory:

- **News Articles**: `finance_news_YYYYMMDD_HHMMSS.json`
- **Risk Analysis**: `risk_analysis_YYYYMMDD_HHMMSS.json`
- **PDF Analysis**: `pdf_analysis_YYYYMMDD_HHMMSS.json`
- **Scheduled Data**: `scheduled_news_YYYYMMDD_HHMMSS.json`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. The risk analysis provided should not be considered as financial advice. Always conduct your own research and consult with financial professionals before making investment decisions.