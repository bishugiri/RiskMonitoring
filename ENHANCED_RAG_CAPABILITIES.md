# Enhanced RAG Service Capabilities

## Overview

The RAG (Retrieval-Augmented Generation) service has been significantly enhanced to handle a wide variety of query types with structured, data-driven responses. The system now intelligently classifies queries and provides appropriate response formats based on the user's specific needs.

## Query Type Classification

The system automatically classifies queries into the following categories:

### 1. Sentiment Trend Analysis
**Keywords:** "sentiment trend", "sentiment analysis", "how is sentiment", "overall sentiment"

**Example Queries:**
- "What's the overall sentiment trend for Apple?"
- "How is the sentiment for AAPL trending?"
- "Show me sentiment analysis for Tesla"

**Response Format:**
```
Sentiment Analysis for [Company]:
- Overall Sentiment: [Average Score] ([Category])
- Distribution: Positive: X, Neutral: Y, Negative: Z
- Trend Analysis: [Description of trend]
- Key Articles: [Reference specific articles with extreme scores]
```

### 2. Risk Score Analysis
**Keywords:** "highest risk", "risk scores", "high risk", "risk assessment"

**Example Queries:**
- "Which articles have the highest risk scores?"
- "Show me high-risk articles for Apple"
- "What's the risk assessment for Tesla?"

**Response Format:**
```
Risk Assessment for [Company]:
- Average Risk Score: [Score]
- High-Risk Articles (Score > [threshold]):
  [List articles with risk scores and categories]
- Risk Categories: [Breakdown by category]
- Key Risk Indicators: [List specific indicators found]
```

### 3. Comparative Analysis
**Keywords:** "compare", "comparison", "vs", "versus", "between"

**Example Queries:**
- "Compare the sentiment between different entities"
- "Compare Apple vs Tesla sentiment"
- "How do Apple and Microsoft compare?"

**Response Format:**
```
Comparison: [Company A] vs [Company B]
[Company A]:
- Average Sentiment: [Score] ([Category])
- Risk Profile: [Description]
- Key Articles: [References]

[Company B]:
- Average Sentiment: [Score] ([Category])
- Risk Profile: [Description]
- Key Articles: [References]

Key Differences: [Analysis]
```

### 4. Temporal Analysis
**Keywords:** "yesterday", "today", "date", "headlines from", "stories on"

**Example Queries:**
- "Show me all headlines from yesterday"
- "What were the main stories on 2025-09-02?"
- "Today's news for Apple"

**Response Format:**
```
Headlines from [Date]:
1. [Title] - [Source] ([Sentiment])
2. [Title] - [Source] ([Sentiment])
...
```

### 5. Risk Indicator Analysis
**Keywords:** "risk indicators", "risk factors", "main risks", "risk mentioned"

**Example Queries:**
- "What are the main risk indicators mentioned?"
- "Show me risk factors for Apple"
- "What risks are being discussed?"

**Response Format:**
```
Risk Indicators Analysis:
- Market Risks: [List and count]
- Regulatory Risks: [List and count]
- Geopolitical Risks: [List and count]
- Sector Risks: [List and count]
- Key Risk Articles: [Reference specific articles]
```

### 6. Specific Article Requests
**Keywords:** "full article", "complete article", "show me the article", "give me the article"

**Example Queries:**
- "Give me the full article about Apple's AI strategy"
- "Show me the complete article on iPhone 17"
- "I want to read the full article about [topic]"

**Response Format:**
```
Here is the complete article:

[FULL ARTICLE TEXT FROM 'text' FIELD]

Source: [Source Name]
Published: [Date]
Link: [URL]
```

### 7. Data Queries
**Keywords:** "how many", "count", "average", "statistics", "data"

**Example Queries:**
- "How many articles mention 'iPhone'?"
- "What's the average risk score for Apple?"
- "Show me articles with sentiment score above 0.5"

**Response Format:**
```
Data Analysis:
- Total Articles: [Count]
- Articles Matching Criteria: [Count]
- Average Score: [Value]
- Range: [Min] to [Max]
- Distribution: [Breakdown]
```

## Enhanced Features

### 1. Query Type Detection
The system automatically detects the type of query being asked and adjusts the response format accordingly.

### 2. Enhanced Context Formatting
- **Analytical Summary:** Provides pre-calculated statistics including average sentiment scores, risk scores, and entity information
- **Structured Data:** Organizes articles by sentiment categories for better analysis
- **Complete Metadata:** Includes all available article metadata for comprehensive responses

### 3. Improved Response Guidelines
- **Query-Specific Instructions:** Different response formats for different query types
- **Data-Driven Responses:** Emphasis on providing exact numbers, scores, and statistics
- **Structured Output:** Clear formatting for different types of analysis

### 4. Better Data Utilization
- **Complete Article Text:** Full access to article content for detailed responses
- **Metadata Analysis:** Comprehensive use of sentiment scores, risk scores, and other metadata
- **Source Diversity:** References multiple sources and time periods

## Technical Improvements

### 1. Query Classification System
```python
def _classify_query_type(self, query: str) -> str:
    """Classify the type of query to help with response formatting"""
    query_lower = query.lower()
    
    # Sentiment trend queries
    if any(phrase in query_lower for phrase in ['sentiment trend', 'sentiment analysis', 'how is sentiment', 'overall sentiment']):
        return 'sentiment_trend'
    
    # Risk score queries
    if any(phrase in query_lower for phrase in ['highest risk', 'risk scores', 'high risk', 'risk assessment']):
        return 'risk_analysis'
    
    # ... additional classifications
```

### 2. Enhanced Context Formatting
```python
# Calculate sentiment statistics
sentiment_groups = {}
risk_scores = []
entities = set()

for article in articles:
    # Group by sentiment
    sentiment = article.get('sentiment_category', 'Unknown')
    if sentiment not in sentiment_groups:
        sentiment_groups[sentiment] = []
    sentiment_groups[sentiment].append(article)
    
    # Collect risk scores
    risk_score = article.get('risk_score', 0)
    if risk_score > 0:
        risk_scores.append(risk_score)
    
    # Collect entities
    entity = article.get('entity', '')
    if entity:
        entities.add(entity)
```

### 3. Improved System Prompt
The system prompt now includes:
- Specific response formats for each query type
- Detailed instructions for data utilization
- Clear guidelines for different types of analysis
- Emphasis on providing structured, quantitative responses

## Usage Examples

### Testing the Enhanced Capabilities
```python
from risk_monitor.core.rag_service import RAGService

# Initialize the service
rag_service = RAGService()

# Test different query types
queries = [
    "What's the overall sentiment trend for Apple?",
    "Which articles have the highest risk scores?",
    "Show me all headlines from yesterday",
    "What are the main risk indicators mentioned?",
    "Give me the full article about Apple's AI strategy",
    "How many articles mention 'iPhone'?"
]

for query in queries:
    response = rag_service.chat_with_agent(
        user_query=query,
        entity_filter="AAPL",
        date_filter="2025-09-02"
    )
    print(f"Query Type: {response.get('query_type')}")
    print(f"Response: {response.get('response')[:200]}...")
```

## Benefits

1. **Structured Responses:** Each query type gets an appropriate response format
2. **Data-Driven Analysis:** Emphasis on providing exact numbers and statistics
3. **Comprehensive Coverage:** Uses all available data for complete analysis
4. **Flexible Query Handling:** Supports a wide variety of question types
5. **Professional Output:** Clear, well-formatted responses for different use cases

## Future Enhancements

1. **Advanced Query Understanding:** More sophisticated query classification
2. **Custom Response Templates:** User-configurable response formats
3. **Interactive Analysis:** Follow-up questions and drill-down capabilities
4. **Visual Data Presentation:** Charts and graphs for complex analysis
5. **Multi-Entity Comparison:** Enhanced comparative analysis across multiple companies

The enhanced RAG service now provides a comprehensive, intelligent solution for financial data analysis with structured, data-driven responses tailored to different types of queries.
