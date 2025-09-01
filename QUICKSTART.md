# Risk Monitor Quick Start Guide

This guide provides a quick overview of how to get started with the Risk Monitor application.

## Installation

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

## Running the Application

### Web Application

Run the web application using one of the following methods:

- **Using convenience scripts**:
  ```bash
  # On macOS/Linux
  ./run_app.sh
  
  # On Windows
  run_app.bat
  ```

- **Using Python module**:
  ```bash
  python -m risk_monitor.scripts.run_app
  ```

Then open your web browser and navigate to:
- http://localhost:8501

### Data Refresh Scheduler

1. **Set up the scheduler**:
   ```bash
   python -m risk_monitor.scripts.run_data_refresh --setup
   ```

2. **Run the scheduler immediately**:
   ```bash
   python -m risk_monitor.scripts.run_data_refresh --run-now
   ```

3. **Start the scheduler daemon**:
   ```bash
   python -m risk_monitor.scripts.run_data_refresh
   ```

## Key Features

- **News Search**: Collect and analyze financial news articles
- **PDF Analysis**: Upload and analyze PDF documents for risk assessment
- **Risk Analysis**: Analyze articles for various risk categories
- **Sentiment Analysis**: Calculate sentiment scores for articles
- **Automated Data Refresh**: Schedule daily data collection and analysis

## For More Information

See the following documentation files:
- `USAGE.md`: Detailed usage instructions
- `README.md`: Project overview and features
- `BACKEND_OVERVIEW.md`: Technical details about the backend
