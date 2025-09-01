"""
RAG (Retrieval-Augmented Generation) Service for Risk Monitor
Enables conversational AI that can query and analyze stored articles
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from risk_monitor.utils.pinecone_db import PineconeDB
from risk_monitor.config.settings import Config

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for conversational AI with Pinecone database"""
    
    def __init__(self):
        self.config = Config()
        self.pinecone_db = PineconeDB()
        # Use legacy OpenAI API
        openai.api_key = self.config.get_openai_api_key()
        
    def search_articles(self, query: str, top_k: int = 50) -> List[Dict]:
        """Search for relevant articles in Pinecone database - fetch all relevant articles"""
        try:
            # Get total number of articles in database
            stats = self.pinecone_db.get_index_stats()
            total_articles = stats.get('total_vector_count', 0)
            
            # Use a high top_k to get all relevant articles, but cap at reasonable limit
            # This ensures we get comprehensive coverage of the topic
            search_limit = min(total_articles, 100)  # Cap at 100 to avoid overwhelming
            
            results = self.pinecone_db.search_similar_articles(query, top_k=search_limit)
            logger.info(f"Found {len(results)} relevant articles for query: {query} (searched up to {search_limit} articles)")
            return results
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def format_context_for_llm(self, articles: List[Dict]) -> str:
        """Format retrieved articles into context for LLM using raw metadata"""
        if not articles:
            return "No relevant articles found."
        
        context_parts = []
        
        # Add comprehensive dataset overview
        total_articles = len(articles)
        context_parts.append(f"""
DATASET OVERVIEW:
Total relevant articles found: {total_articles}
Query coverage: Comprehensive analysis of all available data
""")
        
        # Group articles by sentiment for better analysis
        sentiment_groups = {}
        for article in articles:
            sentiment = article.get('sentiment_category', 'Unknown')
            if sentiment not in sentiment_groups:
                sentiment_groups[sentiment] = []
            sentiment_groups[sentiment].append(article)
        
        # Add sentiment distribution
        sentiment_summary = []
        for sentiment, articles_list in sentiment_groups.items():
            sentiment_summary.append(f"{sentiment}: {len(articles_list)} articles")
        
        context_parts.append(f"""
SENTIMENT DISTRIBUTION:
{', '.join(sentiment_summary)}

DETAILED ARTICLE DATA:
""")
        
        # Format each article with raw metadata
        for i, article in enumerate(articles, 1):
            # Extract ALL raw metadata fields
            title = article.get('title', 'Unknown Title')
            source = article.get('source', 'Unknown Source')
            publish_date = article.get('publish_date', 'Unknown Date')
            sentiment_category = article.get('sentiment_category', 'Unknown')
            sentiment_score = article.get('sentiment_score', 0)
            risk_score = article.get('risk_score', 0)
            summary = article.get('summary', '')
            url = article.get('url', '')
            authors = article.get('authors', [])
            keywords = article.get('keywords', [])
            text = article.get('text', 'No text available')
            
            # Include ALL raw metadata fields
            article_context = f"""
[REFERENCE {i}]
RAW METADATA:
- Title: {title}
- Source: {source}
- URL: {url}
- Published Date: {publish_date}
- Authors: {', '.join(authors) if authors else 'Unknown'}
- Keywords: {', '.join(keywords) if keywords else 'None'}

ANALYSIS DATA:
- Sentiment Category: {sentiment_category}
- Sentiment Score: {sentiment_score}
- Risk Score: {risk_score}

CONTENT:
- Summary: {summary}
- Full Text: {text[:1500]}...
"""
            context_parts.append(article_context)
        
        # Add comprehensive analysis instructions
        context_parts.append(f"""
ANALYSIS INSTRUCTIONS:
- You have access to {total_articles} relevant articles
- Use ALL references when making claims
- Provide comprehensive analysis covering all sentiment categories
- Include specific data points from multiple sources
- Reference article numbers [REFERENCE X] when citing information
- Consider the full spectrum of opinions and data
""")
        
        return "\n".join(context_parts)
    
    def generate_response(self, user_query: str, articles: List[Dict]) -> Dict[str, Any]:
        """Generate AI response based on retrieved articles"""
        try:
            # Format context
            context = self.format_context_for_llm(articles)
            
            # Create system prompt
            system_prompt = """You are a comprehensive financial analyst AI assistant with access to a complete database of analyzed news articles and financial documents. You provide thorough, data-driven insights based on ALL available relevant data.

IMPORTANT INSTRUCTIONS:
1. **Use ALL available data**: You have access to comprehensive datasets - use every relevant article
2. **Reference multiple sources**: Cite multiple reference numbers (e.g., [REFERENCE 1], [REFERENCE 5], [REFERENCE 12]) to show comprehensive analysis
3. **Raw data analysis**: Base responses on the complete raw metadata from the database
4. **Comprehensive coverage**: Cover all sentiment categories and viewpoints found in the data
5. **Specific data points**: Include exact sentiment scores, risk scores, and specific content details
6. **Source diversity**: Reference articles from different sources and time periods
7. **Complete picture**: Provide analysis that reflects the full spectrum of available information
8. **Conversational tone**: Maintain natural, helpful communication while being thorough

Your responses should be:
- Comprehensive and data-rich
- Well-structured with clear sections
- Rich with specific references and data points
- Professional yet accessible
- Focused on complete analysis
- Based on raw metadata from the database

Remember: You have access to ALL relevant articles in the database. Provide analysis that reflects the complete dataset, not just a subset. Use the raw metadata to give the most accurate and comprehensive insights possible."""

            # Create user prompt with context
            user_prompt = f"""User Question: {user_query}

Here is the COMPLETE relevant data from your financial database:

{context}

Please provide a comprehensive, data-driven response that:
- Analyzes ALL available articles and data points
- References multiple articles using [REFERENCE X] format to show comprehensive coverage
- Includes specific sentiment scores, risk scores, and raw metadata details
- Provides complete analysis covering all sentiment categories found
- Uses exact data from the raw metadata in the database
- Gives a complete picture based on the full dataset
- Maintains conversational tone while being thorough

Make sure to:
- Reference multiple sources to show comprehensive analysis
- Include specific data points from the raw metadata
- Cover all viewpoints and sentiment categories found
- Provide analysis that reflects the complete dataset"""

            # Generate response using OpenAI (legacy API)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            return {
                'response': response_text,
                'articles_used': len(articles),
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': articles
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'articles_used': 0,
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': []
            }
    
    def chat_with_agent(self, user_query: str, top_k: int = None) -> Dict[str, Any]:
        """Main method to chat with the RAG agent using raw query format"""
        try:
            # Use raw query format - no preprocessing
            raw_query = user_query.strip()
            logger.info(f"Processing raw query: {raw_query}")
            
            # Search for ALL relevant articles (no fixed limit)
            articles = self.search_articles(raw_query)
            
            # Store ALL articles for display (no limit)
            self.last_articles = articles
            logger.info(f"Stored {len(articles)} articles for display")
            
            # Generate response based on comprehensive dataset
            response = self.generate_response(raw_query, articles)
            
            # Update response with actual article count
            response['articles_used'] = len(articles)
            response['total_articles_available'] = len(articles)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat_with_agent: {e}")
            return {
                'response': f"I apologize, but I encountered an error: {str(e)}",
                'articles_used': 0,
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'articles': []
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        try:
            stats = self.pinecone_db.get_index_stats()
            return {
                'total_articles': stats.get('total_vector_count', 0),
                'index_dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict]:
        """Get recent articles from the database"""
        try:
            # For now, we'll get articles by searching with a general query
            # In a production system, you might want to add timestamp-based filtering
            results = self.pinecone_db.search_similar_articles("recent news", top_k=limit)
            return results
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
