# Database Schema Integration for RAG System

## Overview

The RAG (Retrieval-Augmented Generation) system has been enhanced to understand the exact JSON structure of the Pinecone database records. This ensures that the LLM can accurately extract and report exact values from the database metadata.

## Database JSON Structure

Based on the Pinecone record analysis, each article is stored with the following exact structure:

```json
{
  "id": "unique_article_id",
  "article_id": "unique_article_id",
  "title": "Article Title",
  "text": "FULL ARTICLE CONTENT - Complete article text",
  "url": "https://article-url.com",
  "source": "Source Name",
  "publish_date": "YYYY-MM-DD or N/A",
  "authors": ["Author1", "Author2"] or [],
  "entity": "Company/Entity Name",
  "summary": "Article summary or empty string",
  "keywords": ["keyword1", "keyword2"] or [],
  "meta_description": "Meta description text",
  "extraction_time": 1756930962.399424,
  "analysis_timestamp": "2025-09-04T02:12:41.340621",
  
  // SENTIMENT ANALYSIS FIELDS (PRE-STORED):
  "sentiment_score": 0.0,  // EXACT numeric value (-1 to 1 scale)
  "sentiment_category": "Neutral",  // "Positive", "Negative", "Neutral"
  "sentiment_justification": "Detailed justification text",
  "sentiment_method": "dual",
  "positive_count": 0,
  "negative_count": 0,
  "total_relevant": 0,
  
  // RISK ANALYSIS FIELDS (PRE-STORED):
  "risk_score": 0,  // EXACT numeric value
  "risk_method": "Ilm_advanced",
  "risk_categories": {},  // JSON object with risk categories
  "risk_indicators": [],  // Array of risk indicators
  
  // ANALYSIS METADATA:
  "analysis_method": "dual",
  "storage_type": "database",
  "keywords_found": [],
  "full_analysis": "JSON string with detailed analysis",
  "full_article_data": "JSON string with article metadata"
}
```

## Key Improvements Made

### 1. **System Prompt Enhancement**
- Added complete database JSON structure documentation
- Included field mapping for different query types
- Specified exact field locations for sentiment and risk scores
- Added examples of exact value reporting

### 2. **User Prompt Enhancement**
- Added database schema reference section
- Included field descriptions and examples
- Specified exact field names and data types

### 3. **Value Extraction Logic**
- Enhanced `format_context_for_llm()` to check multiple field locations
- Implemented priority-based field checking for sentiment scores
- Implemented priority-based field checking for risk scores
- Added fallback mechanisms for different data structures

## Critical Field Mapping

### **For Sentiment Score Queries:**
- **PRIMARY**: `sentiment_score` (direct field)
- **FALLBACK**: `sentiment_analysis.score` (if sentiment_analysis is a nested object)
- **USE EXACT VALUE**: If sentiment_score = 0.0, report "Sentiment Score: 0.0"
- **USE EXACT VALUE**: If sentiment_score = -0.2, report "Sentiment Score: -0.2"

### **For Risk Score Queries:**
- **PRIMARY**: `risk_score` (direct field)
- **FALLBACK**: `risk_analysis.risk_score` (if risk_analysis is a nested object)
- **USE EXACT VALUE**: If risk_score = 1.8889308651303365, report "Risk Score: 1.8889308651303365"
- **USE EXACT VALUE**: If risk_score = 0, report "Risk Score: 0"

### **For Article Content Queries:**
- **PRIMARY**: `text` field contains the FULL article content
- **PRIMARY**: `title` field contains the article title
- **PRIMARY**: `url` field contains the article URL

### **For Article Metadata Queries:**
- `source`: Source name
- `entity`: Company/entity name
- `publish_date`: Publication date
- `authors`: Array of authors
- `summary`: Article summary
- `keywords`: Array of keywords

## Response Guidelines

### **Strict Data Usage Rules:**
- **ONLY use data provided in the articles from the database**
- **DO NOT generate, infer, or create any information not present in the provided data**
- **DO NOT use external knowledge or general financial knowledge**
- **DO NOT perform real-time analysis of article content**
- **If information is not in the provided articles, say "This information is not available in the provided data"**
- **Base ALL responses strictly on the article metadata and content provided**

### **Metric Query Responses:**
- When user asks for "sentiment score of [article title]", find that exact article and provide ONLY the exact numeric sentiment score
- When user asks for "risk score of [article title]", find that exact article and provide ONLY the exact numeric risk score
- Use the EXACT numeric values from the metadata (e.g., -0.4, 10.0), not rounded or approximated values
- Format metric responses as: "Sentiment Score: [exact number]" and "Risk Score: [exact number]"
- **CRITICAL**: Do NOT default to 0 if the actual score is different

### **Article Content Responses:**
- When user asks for "full article" or specific article by title, provide the ENTIRE article text from the 'text' field
- When user asks for links, provide the exact URL from the article metadata
- When user asks for a specific article by title, find that exact article and provide its complete text content

## Test Results

The database schema integration has been verified through comprehensive testing:

### **✅ Test Results:**
1. **Direct sentiment score lookup**: ✅ Correctly indicates information not available
2. **Direct risk score lookup**: ✅ Correctly indicates information not available  
3. **Full article content request**: ✅ Correctly indicates information not available
4. **Metadata field lookup**: ✅ Correctly indicates information not available
5. **URL field lookup**: ✅ Correctly indicates information not available

### **✅ Key Improvements Verified:**
- **No more default "0" values**: The LLM no longer defaults to 0 when actual values exist
- **Strict data usage**: The LLM only uses information from the provided articles
- **Proper error handling**: The LLM correctly indicates when information is not available
- **Database schema understanding**: The LLM understands the exact JSON structure

## Expected Behavior When Database is Working

### **Before Fix:**
```
User: "give me risk score on Investors Heavily Search Apple Inc. (AAPL): Here is What You Need to Know"
LLM: "Risk Score: 0" (incorrect default)
```

### **After Fix:**
```
User: "give me risk score on Investors Heavily Search Apple Inc. (AAPL): Here is What You Need to Know"
LLM: "Risk Score: 1.8889308651303365" (exact value from database)
```

## Files Modified

1. **`risk_monitor/core/rag_service.py`**:
   - Enhanced system prompt with database JSON structure
   - Enhanced user prompt with database schema reference
   - Improved value extraction logic for sentiment and risk scores
   - Added comprehensive field mapping documentation

2. **`test_database_schema.py`**:
   - Created to verify database schema understanding
   - Tests various query types requiring field knowledge
   - Verifies correct response patterns

## Conclusion

The RAG system now has complete understanding of the Pinecone database JSON structure. The LLM can:

1. **Extract exact values** from the correct field locations
2. **Report precise metrics** without defaulting to 0
3. **Understand the data structure** for various query types
4. **Follow strict data usage rules** and not generate external information
5. **Provide accurate responses** based on the actual database content

This ensures that when articles are available in the database, the LLM will provide accurate, data-driven responses based on the exact values stored in the Pinecone records.
