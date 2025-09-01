# Risk Monitor Usage Guide

This document provides detailed instructions on how to run and use the Risk Monitor application.

## Table of Contents
- [Installation](#installation)
- [Running the Web Application](#running-the-web-application)
- [Running the Data Refresh Scheduler](#running-the-data-refresh-scheduler)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation

### Quick Installation

The easiest way to install the Risk Monitor application is to use the provided installation script:

```bash
python install.py
```

This script will:
1. Check your Python version
2. Set up a virtual environment
3. Install all dependencies
4. Create necessary directories
5. Set up configuration files

### Manual Installation

If you prefer to install the application manually, follow these steps:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install system dependencies (if needed):
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install libxml2-dev libxslt-dev
   
   # On macOS with Homebrew
   brew install libxml2 libxslt
   ```

## Running the Web Application

There are several ways to run the Risk Monitor web application:

### 1. Using the Convenience Scripts

- **On macOS/Linux**:
  ```bash
  ./run_app.sh
  ```

- **On Windows**:
  ```bash
  run_app.bat
  ```

### 2. Using Python Module

```bash
# Activate your virtual environment first
python -m risk_monitor.scripts.run_app
```

### 3. Using Entry Points (if installed via pip)

```bash
risk-monitor-app
```

Once the application is running, open your web browser and navigate to:
- http://localhost:8501

## Running the Data Refresh Scheduler

The data refresh scheduler is responsible for automatically collecting and analyzing news articles on a regular schedule.

### Setting Up the Scheduler

Before running the scheduler, you should configure it:

```bash
python -m risk_monitor.scripts.run_data_refresh --setup
```

This will guide you through the setup process, allowing you to configure:
- Run time (default: 08:00 AM)
- Timezone (default: US/Eastern)
- Articles per entity
- Entities to monitor
- Keywords to filter
- Sentiment analysis method

### Running the Scheduler Immediately

To run the scheduler immediately (for testing):

```bash
python -m risk_monitor.scripts.run_data_refresh --run-now
```

### Starting the Scheduler Daemon

To start the scheduler as a background process:

```bash
python -m risk_monitor.scripts.run_data_refresh
```

This will run the scheduler continuously, collecting data at the configured time each day.

## Configuration

### API Keys

The application requires several API keys to function properly. These should be configured in the `.streamlit/secrets.toml` file:

```toml
# API Keys for Risk Monitoring Application
OPENAI_API_KEY = "your_openai_api_key_here"
SERPAPI_KEY = "your_serpapi_key_here"
PINECONE_API_KEY = "your_pinecone_api_key_here"
```

### Scheduler Configuration

The scheduler configuration is stored in `scheduler_config.json`:

```json
{
    "run_time": "08:00",
    "timezone": "US/Eastern",
    "articles_per_entity": 5,
    "entities": [
        "Apple Inc",
        "Microsoft Corporation",
        "Goldman Sachs",
        "JPMorgan Chase",
        "Bank of America"
    ],
    "keywords": [
        "risk",
        "financial",
        "market",
        "crisis",
        "volatility"
    ],
    "use_openai": true
}
```

You can edit this file directly or use the `--setup` option when running the scheduler.

## Troubleshooting

### Common Issues

1. **Missing Streamlit**

   Error: `ModuleNotFoundError: No module named 'streamlit'`
   
   Solution: Make sure you've installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**

   Error: `SerpAPI key is required`
   
   Solution: Set up your API keys in `.streamlit/secrets.toml`

3. **Permission Issues**

   Error: `Permission denied` when running shell scripts
   
   Solution: Make the scripts executable:
   ```bash
   chmod +x run_app.sh
   ```

### Getting Help

If you encounter any issues not covered here, please check:
- The logs in the `logs` directory
- The README.md file for additional information
- The BACKEND_OVERVIEW.md file for technical details
