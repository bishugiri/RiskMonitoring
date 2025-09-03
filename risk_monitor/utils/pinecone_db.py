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

class AnalysisPineconeDB:
    """Pinecone database integration specifically for News Analysis using 'analysis-db' index"""
    
    def __init__(self):
        print(f"\n🔧 ANALYSIS PINECONE DB INITIALIZATION:")
        self.config = Config()
        self.index_name = "analysis-db"  # Specific index for News Analysis
        self.dimension = 3072  # OpenAI large embeddings dimension
        self.pinecone_api_key = self.config.get_pinecone_api_key()
        self.openai_api_key = self.config.get_openai_api_key()
        
        print(f"   Index name: {self.index_name}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Pinecone API key: {'✅ Set' if self.pinecone_api_key else '❌ Not set'}")
        print(f"   OpenAI API key: {'✅ Set' if self.openai_api_key else '❌ Not set'}")
        
        if not self.pinecone_api_key:
            print(f"   ❌ ERROR: Pinecone API key not found in configuration")
            raise ValueError("Pinecone API key not found in configuration")
        if not self.openai_api_key:
            print(f"   ❌ ERROR: OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key not found in configuration")
        
        # Initialize Pinecone with new API
        print(f"   🔧 Initializing Pinecone client...")
        try:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            print(f"   ✅ Pinecone client initialized")
        except Exception as e:
            print(f"   ❌ ERROR initializing Pinecone client: {e}")
            raise
        
        # Get or create index
        print(f"   🔧 Getting or creating analysis index...")
        try:
            self.index = self._get_or_create_index()
            print(f"   ✅ Analysis index ready: {self.index_name}")
        except Exception as e:
            print(f"   ❌ ERROR getting/creating analysis index: {e}")
            raise
        
        print("=" * 80)
        
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        print(f"   📋 Getting or creating analysis index: {self.index_name}")
        try:
            # Check if index exists
            print(f"   🔍 Checking existing indexes...")
            index_list = self.pc.list_indexes().names()
            print(f"   📋 Available indexes: {index_list}")
            
            if self.index_name in index_list:
                print(f"   ✅ Using existing Pinecone analysis index: {self.index_name}")
                logger.info(f"Using existing Pinecone analysis index: {self.index_name}")
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                print(f"   🔧 Creating new Pinecone analysis index: {self.index_name}")
                logger.info(f"Creating new Pinecone analysis index: {self.index_name}")
                try:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine"
                    )
                    print(f"   ✅ Analysis index created successfully")
                    return self.pc.Index(self.index_name)
                except Exception as create_error:
                    print(f"   ❌ Error creating analysis index: {create_error}")
                    if "pod quota" in str(create_error).lower() or "quota" in str(create_error).lower():
                        logger.error("Pinecone pod quota exceeded. Please upgrade your Pinecone plan.")
                        raise ValueError("Pinecone quota exceeded - please upgrade your plan")
                    else:
                        raise create_error
        except Exception as e:
            print(f"   ❌ Error initializing Pinecone analysis index: {e}")
            logger.error(f"Error initializing Pinecone analysis index: {e}")
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
            'entity': article.get('entity', ''),
            
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
            'storage_type': 'analysis_db',  # Mark as analysis database
            
            # Full analysis result (for complete data preservation)
            'full_analysis': json.dumps(analysis_result),
            'full_article_data': json.dumps(article)
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Store article with analysis results in Pinecone analysis index - FORCED INSERTION"""
        article_title = article.get('title', 'Unknown')
        try:
            logger.info(f"🔥 STARTING FORCED INSERTION for article: {article_title}")
            
            # Generate embedding from article text
            text = article.get('text', '')
            if not text:
                logger.warning(f"No text content for article: {article_title}")
                return False
            
            logger.info(f"🔥 Generating embedding for article: {article_title}")
            # Create embedding
            embedding = self.generate_embedding(text)
            logger.info(f"✅ Embedding generated successfully for: {article_title}")
            
            # Create unique ID
            article_id = self.create_article_id(article)
            logger.info(f"🔥 Article ID created: {article_id} for: {article_title}")
            
            # Format metadata
            metadata = self.format_metadata(article, analysis_result)
            logger.info(f"🔥 Metadata formatted for: {article_title}")
            
            # FORCED INSERTION - Use upsert to ensure data gets stored
            print(f"   🔥 FORCING INSERTION into analysis-db: {article_title}")
            logger.info(f"🔥 EXECUTING FORCED INSERTION into analysis-db: {article_title}")
            
            self.index.upsert(
                vectors=[{
                    'id': article_id,
                    'values': embedding,
                    'metadata': metadata
                }]
            )
            
            logger.info(f"✅ SUCCESSFULLY FORCED article into analysis-db: {article_title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR storing article in analysis-db: {article_title} - {e}")
            # Try one more time with different approach
            try:
                print(f"   🔄 RETRYING INSERTION with different approach...")
                logger.info(f"🔄 RETRYING INSERTION with different approach for: {article_title}")
                # Force refresh and retry
                self.index.upsert(
                    vectors=[{
                        'id': f"{article_id}_retry",
                        'values': embedding,
                        'metadata': metadata
                    }]
                )
                logger.info(f"✅ RETRY SUCCESSFUL for article: {article_title}")
                return True
            except Exception as retry_error:
                logger.error(f"❌ RETRY FAILED for article {article_title}: {retry_error}")
                return False
    
    def store_articles_batch(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """Store multiple articles in batch to analysis-db - FORCED INSERTION"""
        success_count = 0
        error_count = 0
        
        print(f"🔥 FORCING BATCH INSERTION into analysis-db: {len(articles)} articles")
        logger.info(f"🔥 STARTING FORCED BATCH INSERTION into analysis-db: {len(articles)} articles")
        
        for i, (article, analysis_result) in enumerate(zip(articles, analysis_results), 1):
            article_title = article.get('title', 'Unknown')[:50]
            print(f"   📝 Processing article {i}/{len(articles)}: {article_title}...")
            logger.info(f"🔥 Processing article {i}/{len(articles)}: {article_title}")
            
            if self.store_article(article, analysis_result):
                success_count += 1
                print(f"   ✅ Article {i} successfully forced into analysis-db")
                logger.info(f"✅ Article {i} successfully forced into analysis-db: {article_title}")
            else:
                error_count += 1
                print(f"   ❌ Article {i} failed to insert into analysis-db")
                logger.error(f"❌ Article {i} failed to insert into analysis-db: {article_title}")
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }
        
        print(f"🔥 ANALYSIS-DB BATCH INSERTION COMPLETE: {success_count} successful, {error_count} errors")
        logger.info(f"🔥 ANALYSIS-DB BATCH INSERTION COMPLETE: {success_count} successful, {error_count} errors")
        return result
    
    def search_similar_articles(self, query: str, top_k: int = 10, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Search for similar articles in the analysis-db index"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Build filter
            filter_dict = {}
            if entity_filter:
                filter_dict['entity'] = entity_filter
            if date_filter:
                filter_dict['publish_date'] = date_filter
            
            # Search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            # Format results
            articles = []
            for match in results.matches:
                metadata = match.metadata
                articles.append({
                    'id': match.id,
                    'score': match.score,
                    'title': metadata.get('title', ''),
                    'url': metadata.get('url', ''),
                    'source': metadata.get('source', ''),
                    'publish_date': metadata.get('publish_date', ''),
                    'sentiment_score': metadata.get('sentiment_score', 0),
                    'sentiment_category': metadata.get('sentiment_category', 'Neutral'),
                    'risk_score': metadata.get('risk_score', 0),
                    'text': metadata.get('text', '')[:500] + '...' if len(metadata.get('text', '')) > 500 else metadata.get('text', '')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching analysis-db index: {e}")
            return []

class PineconeDB:
    """Pinecone database integration for storing article analysis results"""
    
    def __init__(self, index_name: str = None):
        print(f"\n🔧 PINECONE DB INITIALIZATION:")
        self.config = Config()
        self.index_name = index_name or self.config.PINECONE_INDEX_NAME
        self.dimension = 3072  # OpenAI large embeddings dimension
        self.pinecone_api_key = self.config.get_pinecone_api_key()
        self.openai_api_key = self.config.get_openai_api_key()
        
        print(f"   Index name: {self.index_name}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Pinecone API key: {'✅ Set' if self.pinecone_api_key else '❌ Not set'}")
        print(f"   OpenAI API key: {'✅ Set' if self.openai_api_key else '❌ Not set'}")
        
        if not self.pinecone_api_key:
            print(f"   ❌ ERROR: Pinecone API key not found in configuration")
            raise ValueError("Pinecone API key not found in configuration")
        if not self.openai_api_key:
            print(f"   ❌ ERROR: OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key not found in configuration")
        
        # Initialize Pinecone with new API
        print(f"   🔧 Initializing Pinecone client...")
        try:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            print(f"   ✅ Pinecone client initialized")
        except Exception as e:
            print(f"   ❌ ERROR initializing Pinecone client: {e}")
            raise
        
        # Initialize OpenAI API key (not needed for new API, but keeping for compatibility)
        self.openai_api_key = self.openai_api_key
        
        # Get or create index
        print(f"   🔧 Getting or creating index...")
        try:
            self.index = self._get_or_create_index()
            print(f"   ✅ Index ready: {self.index_name}")
        except Exception as e:
            print(f"   ❌ ERROR getting/creating index: {e}")
            raise
        
        print("=" * 80)
        
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        print(f"   📋 Getting or creating index: {self.index_name}")
        try:
            # Check if index exists
            print(f"   🔍 Checking existing indexes...")
            index_list = self.pc.list_indexes().names()
            print(f"   📋 Available indexes: {index_list}")
            
            if self.index_name in index_list:
                print(f"   ✅ Using existing Pinecone index: {self.index_name}")
                logger.info(f"Using existing Pinecone index: {self.index_name}")
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                print(f"   🔧 Creating new Pinecone index: {self.index_name}")
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                try:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine"
                    )
                    print(f"   ✅ Index created successfully")
                    return self.pc.Index(self.index_name)
                except Exception as create_error:
                    print(f"   ❌ Error creating index: {create_error}")
                    if "pod quota" in str(create_error).lower() or "quota" in str(create_error).lower():
                        logger.error("Pinecone pod quota exceeded. Please upgrade your Pinecone plan.")
                        raise ValueError("Pinecone quota exceeded - please upgrade your plan")
                    else:
                        raise create_error
        except Exception as e:
            print(f"   ❌ Error initializing Pinecone index: {e}")
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
            'entity': article.get('entity', ''),
            
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
            'storage_type': 'database',  # Mark as database storage
            
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
    
    def search_similar_articles(self, query: str, top_k: int = 10, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Search for similar articles"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Build filter
            filter_dict = {}
            if entity_filter:
                filter_dict['entity'] = entity_filter
            if date_filter:
                filter_dict['publish_date'] = date_filter
            
            # Search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            # Format results
            articles = []
            for match in results.matches:
                metadata = match.metadata
                articles.append({
                    'id': match.id,
                    'score': match.score,
                    'title': metadata.get('title', ''),
                    'url': metadata.get('url', ''),
                    'source': metadata.get('source', ''),
                    'publish_date': metadata.get('publish_date', ''),
                    'sentiment_score': metadata.get('sentiment_score', 0),
                    'sentiment_category': metadata.get('sentiment_category', 'Neutral'),
                    'risk_score': metadata.get('risk_score', 0),
                    'text': metadata.get('text', '')[:500] + '...' if len(metadata.get('text', '')) > 500 else metadata.get('text', '')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0)
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
    
    def delete_article(self, article_id: str) -> bool:
        """Delete an article from the index"""
        try:
            self.index.delete(ids=[article_id])
            logger.info(f"Successfully deleted article: {article_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting article: {e}")
            return False
    
    def update_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Update an existing article"""
        return self.store_article(article, analysis_result)  # Upsert handles updates
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict]:
        """Get article by ID"""
        try:
            results = self.index.fetch(ids=[article_id])
            if results.vectors:
                metadata = results.vectors[article_id].metadata
                return {
                    'id': article_id,
                    'title': metadata.get('title', ''),
                    'url': metadata.get('url', ''),
                    'source': metadata.get('source', ''),
                    'publish_date': metadata.get('publish_date', ''),
                    'sentiment_score': metadata.get('sentiment_score', 0),
                    'sentiment_category': metadata.get('sentiment_category', 'Neutral'),
                    'risk_score': metadata.get('risk_score', 0),
                    'text': metadata.get('text', '')
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching article: {e}")
            return None
