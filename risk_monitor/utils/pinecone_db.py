"""
Pinecone Database Integration for Risk Monitor
Stores article analysis results with OpenAI embeddings and comprehensive metadata
"""

from pinecone import Pinecone
import openai
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from risk_monitor.config.settings import Config

logger = logging.getLogger(__name__)

class PineconeDB:
    """Pinecone database integration for storing article analysis results"""
    
    def __init__(self, index_name: str = None):
        self.config = Config()
        self.index_name = index_name or self.config.PINECONE_INDEX_NAME
        self.dimension = 3072  # OpenAI large embeddings dimension
        self.pinecone_api_key = self.config.get_pinecone_api_key()
        self.openai_api_key = self.config.get_openai_api_key()
        
        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key not found in configuration")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in configuration")
        
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize OpenAI API key (not needed for new API, but keeping for compatibility)
        self.openai_api_key = self.openai_api_key
        
        # Get or create index
        self.index = self._get_or_create_index()
        
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        try:
            # Check if index exists
            index_list = self.pc.list_indexes().names()
            if self.index_name in index_list:
                logger.info(f"Using existing Pinecone index: {self.index_name}")
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                try:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine"
                    )
                    return self.pc.Index(self.index_name)
                except Exception as create_error:
                    if "pod quota" in str(create_error).lower() or "quota" in str(create_error).lower():
                        logger.error("Pinecone pod quota exceeded. Please upgrade your Pinecone plan.")
                        raise ValueError("Pinecone quota exceeded - please upgrade your plan")
                    else:
                        raise create_error
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text,
                dimensions=self.dimension
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def create_article_id(self, article: Dict) -> str:
        """Create unique ID for article based on URL and title"""
        url = article.get('url', '')
        title = article.get('title', '')
        content = f"{url}{title}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_clean_source(self, article: Dict) -> str:
        """Extract clean source name from article"""
        # Try to get source from article_analysis if available
        if 'article_analysis' in article and article['article_analysis'].get('source'):
            return article['article_analysis']['source']
        
        # Try to get source from source field
        if 'source' in article:
            source = article['source']
            if isinstance(source, dict) and 'name' in source:
                return source['name']
            elif isinstance(source, str):
                return source
        
        # Extract from URL
        url = article.get('url', '')
        if url:
            try:
                parsed = urlparse(url)
                return parsed.netloc
            except:
                pass
        
        return "Unknown"
    
    def format_metadata(self, article: Dict, analysis_result: Dict) -> Dict[str, Any]:
        """Format comprehensive metadata for Pinecone storage"""
        
        # Extract sentiment analysis
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        sentiment_score = sentiment_analysis.get('score', 0)
        sentiment_category = sentiment_analysis.get('category', 'Neutral')
        sentiment_justification = sentiment_analysis.get('justification', '')
        
        # Extract risk analysis
        risk_analysis = analysis_result.get('risk_analysis', {})
        risk_score = risk_analysis.get('risk_score', 0)
        risk_categories = risk_analysis.get('risk_categories', {})
        risk_indicators = risk_analysis.get('risk_indicators', [])
        
        # Extract article metadata
        publish_date = article.get('publish_date')
        if isinstance(publish_date, str):
            try:
                # Parse ISO format date
                parsed_date = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_date = publish_date
        elif isinstance(publish_date, datetime):
            formatted_date = publish_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            formatted_date = 'N/A'
        
        # Create comprehensive metadata
        metadata = {
            # Article identification
            'article_id': self.create_article_id(article),
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'source': self.extract_clean_source(article),
            'publish_date': formatted_date,
            'authors': article.get('authors', []),
            
            # Content
            'text': article.get('text', ''),
            'summary': article.get('summary', ''),
            'keywords': article.get('keywords', []),
            'meta_description': article.get('meta_description', ''),
            
            # Sentiment analysis
            'sentiment_score': sentiment_score,
            'sentiment_category': sentiment_category,
            'sentiment_justification': sentiment_justification,
            'positive_count': sentiment_analysis.get('positive_count', 0),
            'negative_count': sentiment_analysis.get('negative_count', 0),
            'total_relevant': sentiment_analysis.get('total_relevant', 0),
            
            # Risk analysis
            'risk_score': risk_score,
            'risk_categories': json.dumps(risk_categories),
            'risk_indicators': json.dumps(risk_indicators),
            'keywords_found': json.dumps(risk_analysis.get('keywords_found', [])),
            
            # Processing metadata
            'extraction_time': article.get('extraction_time', ''),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': analysis_result.get('analysis_method', 'lexicon'),
            
            # Full analysis result (for complete data preservation)
            'full_analysis': json.dumps(analysis_result),
            'full_article_data': json.dumps(article)
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Store article with analysis results in Pinecone"""
        try:
            # Generate embedding from article text
            text = article.get('text', '')
            if not text:
                logger.warning(f"No text content for article: {article.get('title', 'Unknown')}")
                return False
            
            # Create embedding
            embedding = self.generate_embedding(text)
            
            # Create unique ID
            article_id = self.create_article_id(article)
            
            # Format metadata
            metadata = self.format_metadata(article, analysis_result)
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    'id': article_id,
                    'values': embedding,
                    'metadata': metadata
                }]
            )
            
            logger.info(f"Successfully stored article in Pinecone: {article.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article in Pinecone: {e}")
            return False
    
    def store_articles_batch(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """Store multiple articles in batch"""
        success_count = 0
        error_count = 0
        
        for article, analysis_result in zip(articles, analysis_results):
            if self.store_article(article, analysis_result):
                success_count += 1
            else:
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }
        
        logger.info(f"Batch storage complete: {success_count} successful, {error_count} errors")
        return result
    
    def search_similar_articles(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search for similar articles using text query"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results['matches']:
                metadata = match['metadata']
                formatted_results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'title': metadata.get('title', ''),
                    'source': metadata.get('source', ''),
                    'publish_date': metadata.get('publish_date', ''),
                    'sentiment_category': metadata.get('sentiment_category', ''),
                    'sentiment_score': metadata.get('sentiment_score', 0),
                    'risk_score': metadata.get('risk_score', 0),
                    'url': metadata.get('url', ''),
                    'summary': metadata.get('summary', ''),
                    'full_analysis': json.loads(metadata.get('full_analysis', '{}'))
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar articles: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats['total_vector_count'],
                'dimension': stats['dimension'],
                'index_fullness': stats['index_fullness'],
                'namespaces': stats['namespaces']
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
