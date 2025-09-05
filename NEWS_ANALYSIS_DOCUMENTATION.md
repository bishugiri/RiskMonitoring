# News Analysis Documentation

## Overview
The News Analysis functionality is a comprehensive system that collects, analyzes, and stores financial news articles with sentiment and risk analysis. It provides real-time news monitoring for selected companies with advanced filtering and analysis capabilities.

## Architecture

### Core Components
```
News Analysis System
├── Frontend (Streamlit)
│   ├── Entity Selection (Hardcoded Dropdown)
│   ├── Analysis Configuration
│   └── Results Display
├── Backend Services
│   ├── News Collector (SerpAPI)
│   ├── Risk Analyzer (LLM)
│   ├── Pinecone Database
│   └── Sentiment Analysis
└── Data Flow
    ├── Article Collection
    ├── Content Extraction
    ├── LLM Analysis
    └── Vector Storage
```

## Detailed Functionality

### 1. Entity Selection System

#### Hardcoded Entity Dropdown
- **Location**: `risk_monitor/api/streamlit_app.py` (News Analysis page)
- **Function**: `get_nasdaq_100_companies()`
- **Format**: "SYMBOL - Company Name" (e.g., "AAPL - Apple Inc")
- **Total Entities**: 92 NASDAQ-100 companies

#### Selection Options
```python
# Available options in dropdown
- "All Companies" (analyzes all 92 companies)
- Individual company selection (e.g., "AAPL - Apple Inc")
- "➕ Enter Custom Company..." (for custom entities)
```

#### Entity Processing Logic
```python
def process_entity_selection():
    if "All Companies" selected:
        selected_entity = None  # Analyze all companies
    elif custom company entered:
        selected_entity = custom_company_name
    else:
        selected_entity = dropdown_selection  # Full entity name
```

### 2. News Collection System

#### SerpAPI Integration
- **Service**: Google Search API via SerpAPI
- **Query Format**: Uses full entity name (e.g., "AAPL - Apple Inc")
- **Articles per Entity**: Configurable (default: 5)
- **Search Keywords**: Risk-related terms

#### Article Collection Process
```python
def collect_articles(entity_name, articles_per_entity=5):
    # Build search query with entity name
    query = f"{entity_name} financial news risk"
    
    # Call SerpAPI
    articles = serpapi_client.search(query)
    
    # Extract article metadata
    for article in articles:
        extract_content(article)
        validate_article(article)
    
    return articles
```

#### Content Extraction
- **Tool**: Newspaper3k library
- **Extraction**: Title, content, URL, publication date
- **Validation**: Content length, relevance checks
- **Error Handling**: Fallback for extraction failures

### 3. Analysis System

#### LLM-Powered Analysis
- **Model**: OpenAI GPT-4
- **Analysis Types**:
  - Sentiment Analysis (Positive/Negative/Neutral)
  - Risk Assessment (Low/Medium/High)
  - Insight Generation
  - Article Summarization

#### Analysis Process
```python
def analyze_article(article):
    # Prepare content for LLM
    content = f"Title: {article['title']}\nContent: {article['content']}"
    
    # Generate analysis
    analysis = openai_client.analyze(content)
    
    return {
        'sentiment_score': analysis.sentiment_score,
        'risk_score': analysis.risk_score,
        'sentiment_insight': analysis.sentiment_reasoning,
        'risk_insight': analysis.risk_reasoning,
        'summary': analysis.summary
    }
```

#### Analysis Fields
- **sentiment_score**: Numerical score (-1 to 1)
- **risk_score**: Numerical score (0 to 1)
- **sentiment_insight**: LLM reasoning for sentiment
- **risk_insight**: LLM reasoning for risk assessment
- **summary**: Concise article summary

### 4. Database Storage System

#### Pinecone Vector Database
- **Index**: "sentiment-db"
- **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **Metadata**: Complete article and analysis data

#### Storage Structure
```python
metadata = {
    # Article Information
    'title': article.title,
    'url': article.url,
    'source': article.source,
    'published_date': article.published_date,
    'article_extracted_date': current_date,
    
    # Entity Information
    'entity': selected_entity,  # Full entity name
    
    # Analysis Results
    'sentiment_score': analysis.sentiment_score,
    'risk_score': analysis.risk_score,
    'sentiment_insight': analysis.sentiment_insight,
    'risk_insight': analysis.risk_insight,
    'summary': analysis.summary,
    
    # Technical Fields
    'sentiment_category': sentiment_category,
    'risk_category': risk_category,
    'content_length': len(article.content)
}
```

#### Vector Embedding
- **Content**: Article title + content
- **Model**: text-embedding-3-large
- **Dimensions**: 3072
- **Storage**: Pinecone index with metadata

### 5. User Interface

#### Streamlit Frontend
- **Page**: News Analysis
- **Layout**: Multi-column design
- **Components**:
  - Entity selection dropdown
  - Analysis configuration
  - Real-time progress indicators
  - Results display with filtering

#### Key UI Elements
```python
# Entity Selection
st.multiselect(
    "Counterparties",
    options=get_nasdaq_100_companies(),
    default=None,
    help="Select companies to analyze"
)

# Analysis Configuration
col1, col2 = st.columns(2)
with col1:
    articles_per_entity = st.number_input("Articles per entity", 1, 20, 5)
with col2:
    analysis_method = st.selectbox("Analysis method", ["LLM", "Hybrid"])

# Results Display
for article in results:
    display_article_card(article)
```

#### Caching System
- **Analysis Results**: 1 hour cache
- **Sentiment Distribution**: 30 minutes cache
- **Entity List**: Static cache
- **Performance**: Reduces API calls and processing time

### 6. Data Flow Architecture

#### Complete Workflow
```
1. User Selection
   ├── Select entities from dropdown
   ├── Configure analysis parameters
   └── Initiate analysis

2. Data Collection
   ├── Query SerpAPI for each entity
   ├── Extract article content
   └── Validate and filter articles

3. Analysis Processing
   ├── Send articles to LLM
   ├── Generate sentiment/risk scores
   ├── Create insights and summaries
   └── Categorize results

4. Storage
   ├── Create vector embeddings
   ├── Store in Pinecone database
   └── Update metadata

5. Display
   ├── Show analysis results
   ├── Provide filtering options
   └── Enable detailed views
```

### 7. Error Handling

#### Collection Errors
- **API Failures**: Retry with exponential backoff
- **Content Extraction**: Fallback to title-only analysis
- **Rate Limiting**: Implement delays between requests

#### Analysis Errors
- **LLM Failures**: Retry with different prompts
- **Timeout Issues**: Implement request timeouts
- **Invalid Responses**: Validate and sanitize outputs

#### Storage Errors
- **Database Connection**: Retry with connection pooling
- **Vector Dimension**: Validate embedding dimensions
- **Metadata Issues**: Sanitize and validate metadata

### 8. Performance Optimizations

#### Caching Strategy
- **Results Cache**: Store analysis results for 1 hour
- **Entity Cache**: Cache NASDAQ-100 list
- **Sentiment Cache**: Cache sentiment distributions

#### Batch Processing
- **Parallel Analysis**: Process multiple articles simultaneously
- **Async Operations**: Non-blocking API calls
- **Connection Pooling**: Reuse database connections

#### Memory Management
- **Streaming**: Process articles in batches
- **Cleanup**: Clear temporary data after processing
- **Monitoring**: Track memory usage and optimize

### 9. Configuration

#### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_key
SERPAPI_KEY=your_serpapi_key
PINECONE_API_KEY=your_pinecone_key

# Optional
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=sentiment-db
```

#### Runtime Configuration
- **Articles per Entity**: 1-20 (default: 5)
- **Analysis Method**: LLM or Hybrid
- **Cache Duration**: Configurable
- **Retry Attempts**: 3 attempts with backoff

### 10. Monitoring and Logging

#### Logging System
- **Levels**: INFO, WARNING, ERROR
- **Files**: `logs/risk_monitor.log`
- **Format**: Timestamp, Level, Message
- **Rotation**: Daily log rotation

#### Key Metrics
- **Articles Processed**: Count per session
- **Analysis Success Rate**: Percentage of successful analyses
- **API Response Times**: SerpAPI and OpenAI response times
- **Storage Performance**: Pinecone operation times

#### Error Tracking
- **Failed Collections**: Track SerpAPI failures
- **Analysis Errors**: Monitor LLM failures
- **Storage Issues**: Track database errors
- **Performance Issues**: Monitor slow operations

### 11. Security Considerations

#### API Security
- **Key Management**: Secure storage of API keys
- **Rate Limiting**: Respect API rate limits
- **Input Validation**: Sanitize all user inputs
- **Error Handling**: Don't expose sensitive information

#### Data Privacy
- **Content Filtering**: Remove sensitive information
- **Access Control**: Implement user authentication
- **Data Retention**: Configurable data retention policies
- **Compliance**: GDPR and data protection compliance

### 12. Future Enhancements

#### Planned Features
- **Real-time Monitoring**: WebSocket-based live updates
- **Advanced Filtering**: Date range, source, sentiment filters
- **Export Functionality**: CSV, JSON, PDF exports
- **Alert System**: Email/SMS notifications for critical news

#### Technical Improvements
- **Multi-language Support**: Support for non-English articles
- **Image Analysis**: Analyze charts and graphs in articles
- **Social Media Integration**: Include Twitter, Reddit sentiment
- **Machine Learning**: Custom sentiment models

## Code Examples

### Entity Selection Implementation
```python
def get_nasdaq_100_companies():
    """Get NASDAQ-100 companies in 'SYMBOL - Company Name' format"""
    companies = [
        ("AAPL", "Apple Inc"),
        ("MSFT", "Microsoft Corporation"),
        ("NVDA", "NVIDIA Corporation"),
        # ... 92 companies total
    ]
    return [(f"{symbol} - {name}", f"{symbol} - {name}") for symbol, name in companies]
```

### Analysis Implementation
```python
def analyze_and_store_in_pinecone(articles, selected_entity=None):
    """Analyze articles and store in Pinecone database"""
    # Collect articles if not provided
    if not articles:
        articles = collect_articles(selected_entity)
    
    # Analyze articles
    analysis_results = analyzer.analyze_and_store_advanced(
        articles, 
        sentiment_method='llm',
        selected_entity=selected_entity
    )
    
    return analysis_results
```

### Storage Implementation
```python
def store_article(article, analysis_result, selected_entity=None):
    """Store article with analysis in Pinecone database"""
    metadata = format_metadata(article, analysis_result, selected_entity)
    embedding = create_embedding(article['title'] + ' ' + article['content'])
    
    pinecone_index.upsert([{
        'id': generate_id(),
        'values': embedding,
        'metadata': metadata
    }])
```

## Conclusion

The News Analysis system provides comprehensive financial news monitoring with advanced AI-powered analysis. It combines real-time data collection, sophisticated analysis, and efficient storage to deliver actionable insights for financial risk assessment.

The system is designed for scalability, reliability, and user-friendliness, making it suitable for both individual users and enterprise applications.
