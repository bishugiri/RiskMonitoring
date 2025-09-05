# Scheduler Documentation

## Overview
The Scheduler system is an automated news collection and analysis service that runs in the background to continuously monitor financial markets. It provides scheduled data collection, analysis, and email reporting for configured entities, ensuring users stay informed about market developments without manual intervention.

## Architecture

### Core Components
```
Scheduler System
├── Configuration Management
│   ├── Scheduler Config (JSON)
│   ├── Entity Management
│   └── Schedule Settings
├── Background Service
│   ├── Process Management
│   ├── Daily Execution
│   └── Error Handling
├── Data Collection
│   ├── News Collection (SerpAPI)
│   ├── Content Extraction
│   └── Data Validation
├── Analysis Engine
│   ├── LLM Analysis
│   ├── Sentiment Processing
│   └── Risk Assessment
├── Storage System
│   ├── Pinecone Database
│   ├── Metadata Storage
│   └── Vector Embeddings
└── Notification System
    ├── Email Reports
    ├── Log Management
    └── Status Monitoring
```

## Detailed Functionality

### 1. Configuration System

#### Scheduler Configuration File
- **Location**: `risk_monitor/scheduler_config.json`
- **Format**: JSON configuration
- **Purpose**: Centralized configuration management

#### Configuration Structure
```json
{
    "run_time": "08:00",
    "timezone": "US/Eastern",
    "articles_per_entity": 5,
    "entities": [
        "AAPL - Apple Inc",
        "MSFT - Microsoft Corporation",
        "NVDA - NVIDIA Corporation"
    ],
    "keywords": [
        "risk", "financial", "market", "crisis",
        "volatility", "earnings", "revenue", "stock"
    ],
    "use_openai": true,
    "email_enabled": true,
    "email_recipients": ["user@example.com"],
    "enable_pinecone_storage": true,
    "enable_dual_sentiment": true,
    "enable_detailed_email": true
}
```

#### Configuration Parameters
- **run_time**: Daily execution time (HH:MM format)
- **timezone**: Timezone for scheduling (US/Eastern)
- **articles_per_entity**: Number of articles to collect per entity
- **entities**: List of companies to monitor (92 NASDAQ-100 companies)
- **keywords**: Risk-related keywords for filtering
- **use_openai**: Enable OpenAI analysis
- **email_enabled**: Enable email notifications
- **email_recipients**: List of email addresses for reports
- **enable_pinecone_storage**: Enable vector database storage
- **enable_dual_sentiment**: Enable dual sentiment analysis
- **enable_detailed_email**: Include detailed analysis in emails

### 2. Background Service Management

#### Process Management
- **Script**: `risk_monitor/scripts/run_data_refresh.py`
- **Execution**: Background process with nohup
- **Logging**: Comprehensive logging system
- **Monitoring**: Process status tracking

#### Service Control Functions
```python
def start_scheduler():
    """Start the scheduler in background"""
    script_path = "risk_monitor/scripts/run_data_refresh.py"
    result = subprocess.run(
        f'nohup python3 {script_path} > scheduler_background.log 2>&1 &',
        shell=True
    )
    return result.returncode == 0

def stop_scheduler():
    """Stop the scheduler process"""
    result = subprocess.run(['pkill', '-f', 'run_data_refresh.py'])
    return result.returncode == 0

def restart_scheduler():
    """Restart the scheduler"""
    stop_scheduler()
    time.sleep(2)
    return start_scheduler()
```

#### Process Monitoring
- **Status Check**: `pgrep -f "run_data_refresh.py"`
- **Log Monitoring**: Real-time log file monitoring
- **Health Checks**: Process health validation
- **Auto-restart**: Automatic restart on failure

### 3. Scheduling System

#### Daily Execution
- **Schedule**: Daily at configured time
- **Timezone**: Configurable timezone support
- **Duration**: Complete data collection and analysis cycle
- **Recovery**: Automatic retry on failure

#### Schedule Implementation
```python
def schedule_daily_run():
    """Schedule daily news collection and analysis"""
    scheduler = BlockingScheduler(timezone=config.timezone)
    
    scheduler.add_job(
        func=run_daily_collection_and_analysis,
        trigger=CronTrigger(hour=config.run_hour, minute=config.run_minute),
        id='daily_news_collection',
        name='Daily News Collection and Analysis',
        replace_existing=True
    )
    
    scheduler.start()
```

#### Cron-like Scheduling
- **Trigger**: CronTrigger for precise timing
- **Timezone**: Full timezone support
- **Persistence**: Job persistence across restarts
- **Flexibility**: Configurable schedule patterns

### 4. Data Collection Pipeline

#### News Collection Process
```python
def run_daily_collection_and_analysis():
    """Main daily collection and analysis function"""
    logger.info("Starting daily news collection and analysis")
    
    # Collect articles for all entities
    all_articles = []
    for entity in config.entities:
        articles = collect_articles_for_entity(entity)
        all_articles.extend(articles)
    
    # Analyze articles
    analysis_results = analyzer.analyze_and_store_advanced(
        all_articles,
        sentiment_method='llm',
        selected_entity=None
    )
    
    # Send email report if enabled
    if config.email_enabled:
        send_email_report(analysis_results)
    
    logger.info("Daily collection and analysis completed")
```

#### Entity Processing
- **Parallel Processing**: Process multiple entities simultaneously
- **Error Handling**: Individual entity error handling
- **Progress Tracking**: Real-time progress monitoring
- **Data Validation**: Comprehensive data validation

#### Article Collection
```python
def collect_articles_for_entity(entity):
    """Collect articles for a specific entity"""
    try:
        # Build search query
        query = f"{entity} financial news risk"
        
        # Call SerpAPI
        articles = serpapi_client.search(query)
        
        # Extract content
        processed_articles = []
        for article in articles:
            extracted_article = extract_article_content(article)
            if extracted_article:
                processed_articles.append(extracted_article)
        
        return processed_articles[:config.articles_per_entity]
    
    except Exception as e:
        logger.error(f"Error collecting articles for {entity}: {e}")
        return []
```

### 5. Analysis Engine

#### LLM Analysis Integration
- **Model**: OpenAI GPT-4
- **Analysis Types**: Sentiment, Risk, Insights, Summary
- **Batch Processing**: Efficient batch analysis
- **Error Recovery**: Robust error handling

#### Analysis Pipeline
```python
def analyze_and_store_advanced(articles, sentiment_method='llm', selected_entity=None):
    """Advanced analysis and storage pipeline"""
    # Prepare articles for analysis
    prepared_articles = prepare_articles_for_analysis(articles)
    
    # Perform LLM analysis
    analysis_results = perform_llm_analysis(prepared_articles)
    
    # Store in Pinecone database
    if pinecone_db:
        pinecone_db.store_articles_batch_async(
            articles, 
            analysis_results, 
            selected_entity
        )
    
    return analysis_results
```

#### Analysis Results Structure
```python
analysis_result = {
    'sentiment_score': float,  # -1 to 1
    'risk_score': float,      # 0 to 1
    'sentiment_insight': str, # LLM reasoning
    'risk_insight': str,      # LLM reasoning
    'summary': str,           # Article summary
    'sentiment_category': str, # "Positive", "Negative", "Neutral"
    'risk_category': str      # "Low", "Medium", "High"
}
```

### 6. Storage System

#### Pinecone Database Integration
- **Index**: "sentiment-db"
- **Embeddings**: OpenAI text-embedding-3-large
- **Metadata**: Complete article and analysis data
- **Async Operations**: Non-blocking storage operations

#### Storage Implementation
```python
def store_articles_batch_async(articles, analysis_results, selected_entity=None):
    """Store articles asynchronously in Pinecone"""
    # Prepare batch operations
    batch_operations = []
    
    for article, analysis in zip(articles, analysis_results):
        # Format metadata
        metadata = format_metadata(article, analysis, selected_entity)
        
        # Create embedding
        embedding = create_embedding(article['title'] + ' ' + article['content'])
        
        # Prepare upsert operation
        operation = {
            'id': generate_unique_id(),
            'values': embedding,
            'metadata': metadata
        }
        batch_operations.append(operation)
    
    # Execute batch upsert
    pinecone_index.upsert(batch_operations)
```

#### Metadata Structure
```python
metadata = {
    'title': article.title,
    'url': article.url,
    'source': article.source,
    'published_date': article.published_date,
    'article_extracted_date': current_date,
    'entity': entity_name,  # Full entity name
    'sentiment_score': analysis.sentiment_score,
    'risk_score': analysis.risk_score,
    'sentiment_insight': analysis.sentiment_insight,
    'risk_insight': analysis.risk_insight,
    'summary': analysis.summary,
    'sentiment_category': analysis.sentiment_category,
    'risk_category': analysis.risk_category,
    'content_length': len(article.content)
}
```

### 7. Email Notification System

#### Email Report Generation
- **Format**: HTML email with analysis summary
- **Content**: Key insights, sentiment trends, risk alerts
- **Frequency**: Daily reports
- **Recipients**: Configurable email list

#### Email Implementation
```python
def send_email_report(analysis_results):
    """Send daily email report"""
    if not config.email_enabled:
        return
    
    # Generate report content
    report_content = generate_email_report(analysis_results)
    
    # Send email
    emailer.send_email(
        recipients=config.email_recipients,
        subject=f"Daily Risk Monitor Report - {current_date}",
        content=report_content,
        is_html=True
    )
```

#### Report Content Structure
```html
<html>
<body>
    <h2>Daily Risk Monitor Report</h2>
    <p>Date: {current_date}</p>
    
    <h3>Summary</h3>
    <p>Total articles analyzed: {total_articles}</p>
    <p>Entities monitored: {entity_count}</p>
    
    <h3>Sentiment Overview</h3>
    <p>Positive: {positive_count}</p>
    <p>Negative: {negative_count}</p>
    <p>Neutral: {neutral_count}</p>
    
    <h3>Risk Assessment</h3>
    <p>High Risk: {high_risk_count}</p>
    <p>Medium Risk: {medium_risk_count}</p>
    <p>Low Risk: {low_risk_count}</p>
    
    <h3>Key Insights</h3>
    {key_insights}
    
    <h3>Top Articles</h3>
    {top_articles}
</body>
</html>
```

### 8. Logging and Monitoring

#### Comprehensive Logging
- **Log Files**: `logs/scheduler.log`, `scheduler_background.log`
- **Log Levels**: INFO, WARNING, ERROR
- **Log Rotation**: Daily log rotation
- **Structured Logging**: JSON-formatted logs

#### Logging Implementation
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('scheduler')

# Log key events
logger.info("Starting daily news collection")
logger.info(f"Processing {len(entities)} entities")
logger.info(f"Collected {len(articles)} articles")
logger.info("Analysis completed successfully")
```

#### Monitoring Metrics
- **Execution Time**: Track daily execution duration
- **Article Count**: Monitor articles collected per entity
- **Analysis Success Rate**: Track analysis completion rate
- **Error Rate**: Monitor and track errors
- **Storage Performance**: Monitor database operations

### 9. Error Handling and Recovery

#### Robust Error Handling
- **Graceful Degradation**: Continue operation despite errors
- **Retry Logic**: Automatic retry with exponential backoff
- **Error Logging**: Comprehensive error logging
- **Recovery Mechanisms**: Automatic recovery from failures

#### Error Handling Implementation
```python
def safe_execution(func, *args, **kwargs):
    """Execute function with error handling"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                logger.error(f"Function failed after {max_retries} attempts")
                raise
```

#### Recovery Strategies
- **Process Recovery**: Automatic process restart
- **Data Recovery**: Retry failed operations
- **Configuration Recovery**: Fallback to default settings
- **Network Recovery**: Handle network failures

### 10. Configuration Management

#### Dynamic Configuration
- **Runtime Updates**: Update configuration without restart
- **Validation**: Validate configuration changes
- **Backup**: Automatic configuration backup
- **Rollback**: Rollback to previous configuration

#### Configuration Management
```python
class SchedulerConfig:
    def __init__(self, config_file=None):
        self.config_file = config_file or "risk_monitor/scheduler_config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.run_time = config.get('run_time', '08:00')
            self.timezone = config.get('timezone', 'US/Eastern')
            self.entities = config.get('entities', [])
            # ... load other settings
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.use_defaults()
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'run_time': self.run_time,
            'timezone': self.timezone,
            'entities': self.entities,
            # ... other settings
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
```

### 11. Performance Optimization

#### Efficiency Improvements
- **Async Operations**: Non-blocking database operations
- **Batch Processing**: Process multiple articles simultaneously
- **Connection Pooling**: Reuse database connections
- **Memory Management**: Efficient memory usage

#### Performance Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    
    return wrapper

@monitor_performance
def run_daily_collection_and_analysis():
    # ... implementation
```

### 12. Security Considerations

#### Security Measures
- **API Key Protection**: Secure API key storage
- **Input Validation**: Validate all inputs
- **Access Control**: Restrict access to sensitive operations
- **Audit Logging**: Log all security-relevant events

#### Security Implementation
```python
def validate_config(config):
    """Validate configuration for security"""
    # Validate email addresses
    for email in config.get('email_recipients', []):
        if not is_valid_email(email):
            raise ValueError(f"Invalid email address: {email}")
    
    # Validate timezone
    if config.get('timezone') not in pytz.all_timezones:
        raise ValueError(f"Invalid timezone: {config['timezone']}")
    
    # Validate run time format
    try:
        datetime.strptime(config.get('run_time', '08:00'), '%H:%M')
    except ValueError:
        raise ValueError("Invalid run_time format. Use HH:MM")
```

### 13. Deployment and Operations

#### Deployment Options
- **Local Deployment**: Run on local machine
- **Server Deployment**: Deploy on dedicated server
- **Cloud Deployment**: Deploy on cloud platforms
- **Container Deployment**: Docker container deployment

#### Operational Procedures
```bash
# Start scheduler
python3 risk_monitor/scripts/run_data_refresh.py

# Check status
pgrep -f "run_data_refresh.py"

# View logs
tail -f logs/scheduler.log

# Stop scheduler
pkill -f "run_data_refresh.py"
```

#### Maintenance Tasks
- **Log Rotation**: Daily log file rotation
- **Database Cleanup**: Periodic database maintenance
- **Configuration Backup**: Regular configuration backups
- **Performance Monitoring**: Regular performance checks

### 14. Troubleshooting

#### Common Issues
- **Process Not Starting**: Check Python path and dependencies
- **API Failures**: Verify API keys and rate limits
- **Database Errors**: Check Pinecone connection and permissions
- **Email Issues**: Verify email configuration and SMTP settings

#### Troubleshooting Steps
```python
def diagnose_scheduler_issues():
    """Diagnose common scheduler issues"""
    issues = []
    
    # Check process status
    if not is_scheduler_running():
        issues.append("Scheduler process not running")
    
    # Check configuration
    if not validate_config_file():
        issues.append("Configuration file issues")
    
    # Check API keys
    if not validate_api_keys():
        issues.append("API key issues")
    
    # Check database connection
    if not test_database_connection():
        issues.append("Database connection issues")
    
    return issues
```

### 15. Future Enhancements

#### Planned Features
- **Multi-timezone Support**: Support for multiple timezones
- **Advanced Scheduling**: More flexible scheduling options
- **Real-time Monitoring**: WebSocket-based monitoring
- **Custom Analysis**: User-defined analysis rules

#### Technical Improvements
- **Microservices Architecture**: Break into smaller services
- **Kubernetes Deployment**: Container orchestration
- **Advanced Monitoring**: Prometheus/Grafana integration
- **Machine Learning**: Custom ML models for analysis

## Code Examples

### Main Scheduler Implementation
```python
class NewsScheduler:
    def __init__(self, config_file=None):
        self.config = SchedulerConfig(config_file)
        self.collector = NewsCollector()
        self.analyzer = RiskAnalyzer()
        self.pinecone_db = PineconeDB()
        self.emailer = Emailer()
    
    def run_daily_collection_and_analysis(self):
        """Main daily execution function"""
        logger.info("Starting daily news collection and analysis")
        
        try:
            # Collect articles
            all_articles = self.collect_articles()
            
            # Analyze articles
            analysis_results = self.analyzer.analyze_and_store_advanced(
                all_articles,
                sentiment_method='llm'
            )
            
            # Send email report
            if self.config.email_enabled:
                self.send_email_report(analysis_results)
            
            logger.info("Daily collection and analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Daily collection failed: {e}")
            raise
    
    def schedule_daily_run(self):
        """Schedule daily execution"""
        scheduler = BlockingScheduler(timezone=self.config.timezone)
        
        scheduler.add_job(
            func=self.run_daily_collection_and_analysis,
            trigger=CronTrigger(
                hour=self.config.run_hour,
                minute=self.config.run_minute
            ),
            id='daily_news_collection',
            name='Daily News Collection and Analysis'
        )
        
        scheduler.start()
```

### Configuration Management
```python
def load_scheduler_config():
    """Load scheduler configuration"""
    config_file = "risk_monitor/scheduler_config.json"
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()

def save_scheduler_config(config):
    """Save scheduler configuration"""
    config_file = "risk_monitor/scheduler_config.json"
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return True, "Configuration saved successfully"
    except Exception as e:
        return False, f"Error saving configuration: {e}"
```

## Conclusion

The Scheduler system provides robust, automated financial news monitoring with comprehensive analysis and reporting capabilities. It ensures continuous market surveillance while maintaining high reliability and performance standards.

The system is designed for enterprise-grade deployment with comprehensive monitoring, error handling, and maintenance capabilities, making it suitable for both individual users and large-scale financial operations.
