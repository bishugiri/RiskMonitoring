# Structured Sentiment Analysis Implementation

## Overview

The Risk Monitoring project now includes an enhanced **structured sentiment analysis** system that follows a comprehensive approach for tracking reputation risk for financial entities. This implementation provides much more detailed and actionable insights compared to the original basic sentiment analysis.

## Key Features

### 1. **Entity Identification**
- Automatically identifies the main financial entity mentioned in news articles
- Supports major financial institutions (Goldman Sachs, Blackstone, Vanguard, etc.)
- Uses pattern matching and keyword detection for entity extraction

### 2. **Event Classification**
- Categorizes news events into specific types:
  - `regulatory` - SEC, FCC, compliance issues
  - `legal` - lawsuits, litigation, settlements
  - `product_launch` - new products, announcements
  - `product_closure` - fund closures, discontinuations
  - `performance` - earnings, revenue, financial results
  - `inflows_outflows` - investment flows, AUM changes
  - `ratings` - credit ratings, upgrades, downgrades
  - `operations` - strategic changes, restructuring
  - `donations` - charitable giving, philanthropy
  - `other` - general news, commentary

### 3. **Enhanced Sentiment Scoring**
- **Scale**: -1.0 to +1.0 with detailed breakdown:
  - **-1.0**: Severe negative (legal/ethical crises, large fines, flagship fund closure)
  - **-0.8 to -0.6**: Significant negative (major losses, regulatory issues, significant downgrades)
  - **-0.5 to -0.2**: Moderate negative (minor setbacks, underperformance, small fines)
  - **-0.1 to 0.1**: Neutral (mixed news, no clear impact, routine announcements)
  - **0.2 to 0.5**: Moderate positive (good performance, minor upgrades, positive developments)
  - **0.6 to 0.8**: Significant positive (strong performance, major upgrades, successful launches)
  - **1.0**: Exceptional positive (transformational deals, record inflows, major upgrades, significant donations)

### 4. **Detailed Reasoning**
- Provides comprehensive explanations for sentiment scores
- References specific text and evidence from articles
- Balances positive and negative factors
- Considers financial impact and materiality

### 5. **Evidence Extraction**
- Extracts key quotes and numbers from articles
- Identifies important financial figures and statements
- Provides supporting evidence for analysis

## Implementation Details

### Core Functions

#### `analyze_sentiment_structured(text, title, openai_api_key)`
- **Primary function** for LLM-based structured analysis
- Uses GPT-4o with specialized financial prompts
- Returns comprehensive analysis with all structured fields

#### `analyze_sentiment_lexicon_structured(text, title)`
- **Fallback function** for rule-based structured analysis
- Uses enhanced financial lexicon with entity detection
- Provides structured output even without LLM access

### Output Format

```json
{
  "entity": "string - main financial entity mentioned",
  "headline": "string - article headline", 
  "event_type": "string - one of predefined event types",
  "sentiment_score": "number between -1 and 1",
  "reasoning": "string - detailed explanation of sentiment score",
  "confidence": "number between 0 and 1",
  "key_quotes": ["quote1", "quote2", "quote3"],
  "summary": "string - 1-2 sentence summary of key event"
}
```

## Comparison with Original Implementation

### Original Approach
- **Basic sentiment**: Simple positive/negative/neutral classification
- **Limited context**: No entity identification or event classification
- **Generic reasoning**: Basic justification without financial context
- **Single method**: Primarily lexicon-based with basic LLM support

### Enhanced Approach
- **Structured analysis**: Comprehensive entity and event identification
- **Financial focus**: Specialized for financial news and institutions
- **Detailed reasoning**: Context-aware explanations with evidence
- **Dual methods**: Both lexicon and LLM with structured output
- **Evidence extraction**: Key quotes and supporting data
- **Materiality assessment**: Considers financial impact and significance

## Integration Points

### Risk Analyzer (`risk_monitor/core/risk_analyzer.py`)
- Updated to use structured sentiment analysis
- Maintains backward compatibility with legacy format
- Enhanced correlation analysis between sentiment and risk

### Streamlit Interface (`risk_monitor/api/streamlit_app.py`)
- Displays structured analysis results
- Shows entity, event type, and detailed reasoning
- Enhanced article cards with comprehensive information

### Database Storage
- Stores structured analysis in Pinecone database
- Maintains compatibility with existing queries
- Enables advanced filtering and analysis

## Usage Examples

### Example 1: Fund Closure
```python
# Input
title = "Goldman Sachs Asset Management closes small Europe HY fund due to limited demand"
text = "Goldman Sachs Asset Management (GSAM) has announced the closure..."

# Output
{
  "entity": "Goldman Sachs Asset Management",
  "event_type": "product_closure", 
  "sentiment_score": -0.3,
  "reasoning": "The closure of the European high-yield fund is a moderate negative event...",
  "key_quotes": ["$50 million in assets under management", "strategic realignment"],
  "summary": "GSAM closing small European high-yield fund due to limited demand"
}
```

### Example 2: Legal Investigation
```python
# Input  
title = "Blackstone faces DOJ investigation over RealPage price-fixing allegations"
text = "Blackstone Group is under investigation by the Department of Justice..."

# Output
{
  "entity": "Blackstone Group",
  "event_type": "legal",
  "sentiment_score": -0.8,
  "reasoning": "The investigation by the Department of Justice is a significant legal issue...",
  "key_quotes": ["DOJ investigation", "significant fines", "regulatory scrutiny"],
  "summary": "Blackstone under DOJ investigation for potential price-fixing"
}
```

## Benefits

1. **Actionable Insights**: Provides specific entity and event context
2. **Risk Assessment**: Better correlation with risk analysis
3. **Evidence-Based**: Extracts supporting quotes and numbers
4. **Financial Focus**: Specialized for financial institutions
5. **Comprehensive Analysis**: Covers multiple dimensions of sentiment
6. **Reliability**: Multiple fallback mechanisms ensure availability

## Testing

Run the test script to see the enhanced analysis in action:

```bash
python test_structured_sentiment.py
```

This will demonstrate:
- Entity identification accuracy
- Event classification performance  
- Sentiment scoring with detailed reasoning
- Evidence extraction capabilities
- Both lexicon and LLM analysis methods

## Future Enhancements

1. **Entity Database**: Expand list of financial institutions
2. **Event Patterns**: Improve event classification accuracy
3. **Context Awareness**: Consider market conditions and sector trends
4. **Historical Analysis**: Track sentiment changes over time
5. **Alert System**: Notify on significant sentiment changes

## Conclusion

The structured sentiment analysis provides a significant improvement over the original implementation, offering much more detailed and actionable insights for financial risk monitoring. It follows the comprehensive approach you specified while maintaining compatibility with existing systems.
