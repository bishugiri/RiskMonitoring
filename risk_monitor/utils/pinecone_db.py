"""
Pinecone database utilities for storing and retrieving article embeddings and metadata.
"""

import logging
import hashlib
import json
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Try to import Pinecone, but handle gracefully if not available
try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

logger = logging.getLogger(__name__)

class PineconeDB:
    """
    Pinecone database interface for storing article embeddings and metadata.
    Optimized for batch operations and concurrent processing.
    """
    
    def __init__(self, index_name: str = "sentiment-db"):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.index_name = index_name
        self.index = None
        self._init_pinecone()
    
    def _init_pinecone(self):
        """Initialize Pinecone client and index"""
        if not PINECONE_AVAILABLE:
            logger.warning("Pinecone not available - database operations will be disabled")
            return
        
        try:
            # Get API key from environment
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                logger.error("PINECONE_API_KEY not found in environment")
                return
            
            # Initialize Pinecone
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            self.pc = pc
            
            # Get or create index
            self._get_or_create_index()
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
    
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        try:
            # Check if index exists
            if self.index_name in self.pc.list_indexes().names():
                self.index = self.pc.Index(self.index_name)
                logger.info(f"Using existing Pinecone index: {self.index_name}")
            else:
                # Create new index
                from pinecone import ServerlessSpec
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI text-embedding-3-small dimension
                    metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
                )
                self.index = self.pc.Index(self.index_name)
                logger.info(f"Created new Pinecone index: {self.index_name}")
                
        except Exception as e:
            logger.error(f"Error getting/creating index: {e}")

    async def store_articles_batch_async(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """
        Store multiple articles in batch with concurrent processing
        
        Args:
            articles: List of articles to store
            analysis_results: List of analysis results
            
        Returns:
            Dictionary with success/error counts
        """
        if not self.index:
            logger.error("Pinecone index not available")
            return {'success_count': 0, 'error_count': len(articles), 'total_count': len(articles)}
        
        success_count = 0
        error_count = 0
        
        # Process articles in batches for better performance
        batch_size = 10
        for i in range(0, len(articles), batch_size):
            batch_articles = articles[i:i + batch_size]
            batch_analyses = analysis_results[i:i + batch_size]
            
            # Process batch concurrently
            batch_results = await self._process_batch_async(batch_articles, batch_analyses)
            
            success_count += batch_results['success_count']
            error_count += batch_results['error_count']
        
        logger.info(f"Database batch storage complete: {success_count} successful, {error_count} errors")
        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }

    async def _process_batch_async(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """
        Process a batch of articles asynchronously
        
        Args:
            articles: Batch of articles
            analysis_results: Batch of analysis results
            
        Returns:
            Dictionary with success/error counts
        """
        success_count = 0
        error_count = 0
        
        # Create tasks for concurrent processing
        tasks = []
        for article, analysis in zip(articles, analysis_results):
            task = self._store_single_article_async(article, analysis)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Error storing article: {result}")
            elif result:
                success_count += 1
        
        return {
            'success_count': success_count,
            'error_count': error_count
        }

    async def _store_single_article_async(self, article: Dict, analysis_result: Dict) -> bool:
        """
        Store a single article asynchronously
        
        Args:
            article: Article to store
            analysis_result: Analysis result
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embeddings concurrently
            embedding_task = self._generate_embedding_async(article)
            metadata_task = self._prepare_metadata_async(article, analysis_result)
            
            # Wait for both tasks to complete
            embedding, metadata = await asyncio.gather(embedding_task, metadata_task)
            
            if not embedding:
                return False
            
            # Store in database
            article_id = hashlib.md5(article['url'].encode()).hexdigest()
            
            # Use ThreadPoolExecutor for synchronous Pinecone operations
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    lambda: self.index.upsert(
                        vectors=[(article_id, embedding, metadata)],
                        namespace="articles"
                    )
                )
            
            logger.info(f"Successfully stored article in database: {article.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article: {e}")
            return False

    async def _generate_embedding_async(self, article: Dict) -> Optional[List[float]]:
        """
        Generate embedding for article text asynchronously
        
        Args:
            article: Article to generate embedding for
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            from openai import OpenAI
            import httpx
            import os
            
            # Get OpenAI API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found")
                return None
            
            # Create OpenAI client
            client = OpenAI(api_key=api_key, http_client=httpx.Client(timeout=30.0))
            
            # Prepare text for embedding
            text = article.get('text', '')
            if not text:
                return None
            
            # Truncate text if too long (OpenAI limit is 8191 tokens)
            if len(text) > 8000:
                text = text[:8000]
            
            # Generate embedding asynchronously
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor,
                    lambda: client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text
                    )
                )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def _prepare_metadata_async(self, article: Dict, analysis_result: Dict) -> Dict[str, Any]:
        """
        Prepare metadata for article storage asynchronously
        
        Args:
            article: Article data
            analysis_result: Analysis result
            
        Returns:
            Metadata dictionary
        """
        try:
            # Extract source
            source = self.extract_clean_source(article)
            
            # Prepare metadata
            metadata = {
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'source': source,
                'publish_date': article.get('publish_date'),
                'sentiment_score': analysis_result.get('sentiment_analysis', {}).get('score', 0),
                'sentiment_category': analysis_result.get('sentiment_analysis', {}).get('category', 'Neutral'),
                'risk_score': analysis_result.get('risk_analysis', {}).get('overall_risk_score', 0),
                'risk_confidence': analysis_result.get('risk_analysis', {}).get('risk_confidence', 0),
                'analysis_timestamp': analysis_result.get('analysis_timestamp', ''),
                'text_length': len(article.get('text', '')),
                'keywords': article.get('keywords', []),
                'authors': article.get('authors', [])
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error preparing metadata: {e}")
            return {}
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            from openai import OpenAI
            import httpx
            import httpx
            client = OpenAI(api_key=self.openai_api_key, http_client=httpx.Client(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True
            ))
            
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def create_article_id(self, article: Dict) -> str:
        """Create unique ID for article based on URL only with backward compatibility"""
        url = article.get('url', '')
        if not url:
            # Fallback to title hash if no URL available
            title = article.get('title', '')
            return hashlib.md5(title.encode()).hexdigest()
        
        # Use URL hash as the primary key for better deduplication
        return hashlib.md5(url.encode()).hexdigest()
    
    def article_exists(self, url: str) -> bool:
        """Check if an article with the given URL already exists in the database"""
        try:
            if not url:
                return False
            
            # Create the same ID that would be used for storage
            article_id = hashlib.md5(url.encode()).hexdigest()
            
            # Check if the ID exists in the index
            # Use fetch to check for existence
            fetch_result = self.index.fetch(ids=[article_id])
            
            # If the ID exists in the result, the article exists
            return article_id in fetch_result.vectors
            
        except Exception as e:
            logger.error(f"Error checking if article exists: {e}")
            return False
    
    def article_exists_backward_compatible(self, url: str, title: str = None) -> bool:
        """Check if an article exists using both new (URL-only) and old (URL+title) methods"""
        try:
            if not url:
                return False
            
            # Check with new URL-only method
            new_id = hashlib.md5(url.encode()).hexdigest()
            
            # Check with old URL+title method if title is provided
            old_id = None
            if title:
                old_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()
            
            # Fetch both IDs
            ids_to_check = [new_id]
            if old_id:
                ids_to_check.append(old_id)
            
            fetch_result = self.index.fetch(ids=ids_to_check)
            
            # Check if either ID exists
            return any(article_id in fetch_result.vectors for article_id in ids_to_check)
            
        except Exception as e:
            logger.error(f"Error checking if article exists (backward compatible): {e}")
            return False
    
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
        
        # Extract sentiment analysis from the proper structure
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        sentiment_score = sentiment_analysis.get('score', 0)
        sentiment_category = sentiment_analysis.get('category', 'Neutral')
        sentiment_justification = sentiment_analysis.get('justification', '')
        
        # Extract risk analysis from the proper structure
        risk_analysis = analysis_result.get('risk_analysis', {})
        risk_score = risk_analysis.get('overall_risk_score', 0)
        risk_categories = risk_analysis.get('risk_categories', {})
        risk_indicators = risk_analysis.get('key_risk_indicators', [])
        
        # Extract analysis method from the proper structure
        analysis_method = analysis_result.get('analysis_method', 'unknown')
        
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
            'analysis_method': analysis_method,
            'sentiment_method': analysis_method,
            'risk_method': 'llm_advanced',
            'storage_type': 'database',
            
            # Full analysis result
            'full_analysis': json.dumps(analysis_result),
            'full_article_data': json.dumps(article)
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Store article with analysis results in Pinecone database"""
        try:
            # Check if article already exists using backward compatible method
            url = article.get('url', '')
            title = article.get('title', '')
            if url and self.article_exists_backward_compatible(url, title):
                logger.info(f"Article already exists in database, skipping: {article.get('title', 'Unknown')} ({url})")
                return True  # Return True since we're not treating this as an error
            
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
            
            # Upsert to Pinecone database
            self.index.upsert(
                vectors=[{
                    'id': article_id,
                    'values': embedding,
                    'metadata': metadata
                }]
            )
            
            logger.info(f"Successfully stored article in database: {article.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article in database: {e}")
            return False
    
    def store_articles_batch(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict[str, int]:
        """Store multiple articles in batch to database"""
        success_count = 0
        error_count = 0
        duplicate_count = 0
        
        for article, analysis_result in zip(articles, analysis_results):
            # Check if article already exists using backward compatible method
            url = article.get('url', '')
            title = article.get('title', '')
            if url and self.article_exists_backward_compatible(url, title):
                duplicate_count += 1
                logger.info(f"Article already exists in database, skipping: {article.get('title', 'Unknown')} ({url})")
                continue
            
            if self.store_article(article, analysis_result):
                success_count += 1
            else:
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'duplicate_count': duplicate_count,
            'total_count': len(articles)
        }
        
        logger.info(f"Database batch storage complete: {success_count} successful, {error_count} errors, {duplicate_count} duplicates")
        return result
    
    def search_similar_articles(self, query: str, top_k: int = 10, entity_filter: str = None, date_filter: str = None) -> List[Dict]:
        """Search for similar articles in the database"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Don't apply entity filter at Pinecone level - will be done in RAG service
            # This is because entity field is often empty, but articles contain entity info in title/text
            
            # Search without filters (filtering will be done in RAG service)
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=None,  # No Pinecone-level filtering
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
                    'text': metadata.get('text', '')[:500] + '...' if len(metadata.get('text', '')) > 500 else metadata.get('text', ''),
                    'analysis_timestamp': metadata.get('analysis_timestamp', ''),  # Required for date filtering
                    'entity': metadata.get('entity', '')  # Required for entity filtering
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching database: {e}")
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
    
    def get_all_articles(self, top_k: int = 1000) -> List[Dict]:
        """Get all articles from the database without semantic search"""
        try:
            # Use a generic query to get all articles
            query_embedding = self.generate_embedding("article")
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=None,
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
                    'text': metadata.get('text', '')[:500] + '...' if len(metadata.get('text', '')) > 500 else metadata.get('text', ''),
                    'analysis_timestamp': metadata.get('analysis_timestamp', ''),
                    'entity': metadata.get('entity', '')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting all articles: {e}")
            return []
    
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
