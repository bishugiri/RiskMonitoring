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
from datetime import datetime

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
                    dimension=3072,  # OpenAI text-embedding-3-large dimension
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

    async def store_articles_batch_async(self, articles: List[Dict], analysis_results: List[Dict], selected_entity: str = None) -> Dict[str, int]:
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
            batch_results = await self._process_batch_async(batch_articles, batch_analyses, selected_entity)
            
            success_count += batch_results['success_count']
            error_count += batch_results['error_count']
        
        logger.info(f"Database batch storage complete: {success_count} successful, {error_count} errors")
        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }

    async def _process_batch_async(self, articles: List[Dict], analysis_results: List[Dict], selected_entity: str = None) -> Dict[str, int]:
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
            task = self._store_single_article_async(article, analysis, selected_entity)
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

    async def _store_single_article_async(self, article: Dict, analysis_result: Dict, selected_entity: str = None) -> bool:
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
            metadata_task = self._prepare_metadata_async(article, analysis_result, selected_entity)
            
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
                        model="text-embedding-3-large",
                        input=text
                    )
                )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def _prepare_metadata_async(self, article: Dict, analysis_result: Dict, selected_entity: str = None) -> Dict[str, Any]:
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
            
            # Use selected entity if provided, otherwise determine using LLM logic
            if selected_entity and selected_entity != "All Companies":
                entity = selected_entity
            else:
                entity = self._determine_entity(article)
            
            # Get current system date for article_extracted_date
            article_extracted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Prepare metadata
            metadata = {
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'source': source,
                'publish_date': article.get('publish_date'),
                'entity': entity,  # Use selected entity or LLM-determined entity
                'article_extracted_date': article_extracted_date,  # System date when added to DB
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
            print(f"🔤 GENERATING NEW EMBEDDING: '{text[:50]}...' (model: text-embedding-3-large)")
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
            print(f"✅ New embedding generated successfully")
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
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
    
    def _determine_entity(self, article: Dict) -> str:
        """Determine the main entity/company from article content using LLM"""
        try:
            # Entity mapping dictionary
            entity_mappings = {
                "apple": "AAPL - Apple Inc",
                "microsoft": "MSFT - Microsoft Corporation", 
                "google": "GOOGL - Alphabet Inc",
                "alphabet": "GOOGL - Alphabet Inc",
                "amazon": "AMZN - Amazon.com Inc",
                "tesla": "TSLA - Tesla Inc",
                "meta": "META - Meta Platforms Inc",
                "facebook": "META - Meta Platforms Inc",
                "nvidia": "NVDA - NVIDIA Corporation",
                "netflix": "NFLX - Netflix Inc",
                "berkshire": "BRK.A - Berkshire Hathaway Inc",
                "jpmorgan": "JPM - JPMorgan Chase & Co",
                "bank of america": "BAC - Bank of America Corp",
                "wells fargo": "WFC - Wells Fargo & Co",
                "goldman sachs": "GS - Goldman Sachs Group Inc",
                "morgan stanley": "MS - Morgan Stanley",
                "visa": "V - Visa Inc",
                "mastercard": "MA - Mastercard Inc",
                "paypal": "PYPL - PayPal Holdings Inc",
                "salesforce": "CRM - Salesforce Inc",
                "oracle": "ORCL - Oracle Corporation",
                "adobe": "ADBE - Adobe Inc",
                "intel": "INTC - Intel Corporation",
                "amd": "AMD - Advanced Micro Devices Inc",
                "cisco": "CSCO - Cisco Systems Inc",
                "ibm": "IBM - International Business Machines Corp",
                "walmart": "WMT - Walmart Inc",
                "home depot": "HD - Home Depot Inc",
                "costco": "COST - Costco Wholesale Corp",
                "target": "TGT - Target Corporation",
                "nike": "NKE - Nike Inc",
                "coca cola": "KO - Coca-Cola Co",
                "pepsi": "PEP - PepsiCo Inc",
                "procter & gamble": "PG - Procter & Gamble Co",
                "johnson & johnson": "JNJ - Johnson & Johnson",
                "pfizer": "PFE - Pfizer Inc",
                "moderna": "MRNA - Moderna Inc",
                "boeing": "BA - Boeing Co",
                "general electric": "GE - General Electric Co",
                "disney": "DIS - Walt Disney Co",
                "comcast": "CMCSA - Comcast Corp",
                "verizon": "VZ - Verizon Communications Inc",
                "at&t": "T - AT&T Inc",
                "t-mobile": "TMUS - T-Mobile US Inc"
            }
            
            # Get article text and title for entity detection
            text = (article.get('title', '') + ' ' + article.get('text', '')).lower()
            
            # Check for entity matches in order of specificity
            for entity_key, entity_value in entity_mappings.items():
                if entity_key in text:
                    return entity_value
            
            # If no specific entity found, return empty string
            return ""
            
        except Exception as e:
            logger.error(f"Error determining entity: {e}")
            return ""

    def format_metadata(self, article: Dict, analysis_result: Dict, selected_entity: str = None) -> Dict[str, Any]:
        """Format simplified metadata for Pinecone storage with essential fields and LLM insights"""
        
        # Extract sentiment analysis from the proper structure
        sentiment_analysis = analysis_result.get('sentiment_analysis', {})
        sentiment_score = sentiment_analysis.get('score', 0) or sentiment_analysis.get('sentiment_score', 0)
        sentiment_category = sentiment_analysis.get('category', 'Neutral')
        # Try multiple possible field names for sentiment insight
        sentiment_insight = (
            sentiment_analysis.get('justification', '') or 
            sentiment_analysis.get('reasoning', '') or 
            sentiment_analysis.get('insight', '') or
            sentiment_analysis.get('summary', '')
        )
        
        # Extract risk analysis from the proper structure
        risk_analysis = analysis_result.get('risk_analysis', {})
        risk_score = (
            risk_analysis.get('overall_risk_score', 0) or 
            risk_analysis.get('risk_score', 0) or
            risk_analysis.get('score', 0)
        )
        # Try multiple possible field names for risk insight
        risk_insight = (
            risk_analysis.get('risk_summary', '') or 
            risk_analysis.get('reasoning', '') or 
            risk_analysis.get('insight', '') or
            risk_analysis.get('summary', '') or
            risk_analysis.get('risk_confidence', '')
        )
        
        # Extract summary from multiple possible locations
        summary = (
            analysis_result.get('summary', '') or 
            article.get('summary', '') or
            sentiment_analysis.get('summary', '') or
            risk_analysis.get('summary', '') or
            sentiment_analysis.get('justification', '') or  # Use sentiment justification as summary if no other summary
            risk_analysis.get('risk_summary', '')  # Use risk summary as fallback
        )
        
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
        
        # Use selected entity if provided, otherwise determine using LLM logic
        if selected_entity and selected_entity != "All Companies":
            entity = selected_entity
        else:
            entity = self._determine_entity(article)
        
        # Get current system date for article_extracted_date
        article_extracted_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create metadata with essential fields and LLM insights
        metadata = {
            # Essential article identification
            'id': self.create_article_id(article),
            'title': article.get('title', ''),
            'text': article.get('text', ''),
            'url': article.get('url', ''),
            'source': self.extract_clean_source(article),
            'publish_date': formatted_date,
            'authors': article.get('authors', []),
            
            # NEW FIELDS as requested
            'entity': entity,  # LLM-determined entity mapping
            'article_extracted_date': article_extracted_date,  # System date when added to DB
            
            # LLM-generated analysis fields
            'sentiment_score': sentiment_score,  # LLM-produced sentiment score
            'sentiment_category': sentiment_category,
            'sentiment_insight': sentiment_insight,  # LLM-generated sentiment insight
            
            'risk_score': risk_score,  # LLM-produced risk score
            'risk_insight': risk_insight,  # LLM-generated risk insight
            
            'summary': summary,  # LLM-generated article summary
            
            # Essential metadata
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict, selected_entity: str = None) -> bool:
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
            metadata = self.format_metadata(article, analysis_result, selected_entity)
            
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
    
    def store_articles_batch(self, articles: List[Dict], analysis_results: List[Dict], selected_entity: str = None) -> Dict[str, int]:
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
            
            if self.store_article(article, analysis_result, selected_entity):
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
        """Get all articles from the database without semantic search, including full metadata"""
        try:
            # Use a generic query to get all articles
            query_embedding = self.generate_embedding("article")
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=None,
                include_metadata=True,
                include_values=True  # Include the embedding vectors
            )
            
            # Format results with complete metadata
            articles = []
            articles_with_embeddings = 0
            for match in results.matches:
                metadata = match.metadata
                has_embedding = match.values is not None
                if has_embedding:
                    articles_with_embeddings += 1
                
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
                    'text': metadata.get('text', ''),  # Return full text, not truncated
                    'analysis_timestamp': metadata.get('analysis_timestamp', ''),
                    'entity': metadata.get('entity', ''),
                    'authors': metadata.get('authors', []),
                    'keywords': metadata.get('keywords', []),
                    'summary': metadata.get('summary', ''),
                    'meta_description': metadata.get('meta_description', ''),
                    'sentiment_justification': metadata.get('sentiment_justification', ''),
                    'risk_categories': metadata.get('risk_categories', ''),
                    'risk_indicators': metadata.get('risk_indicators', ''),
                    'extraction_time': metadata.get('extraction_time', ''),
                    'analysis_method': metadata.get('analysis_method', ''),
                    'sentiment_method': metadata.get('sentiment_method', ''),
                    'risk_method': metadata.get('risk_method', ''),
                    'storage_type': metadata.get('storage_type', ''),
                    'keywords_found': metadata.get('keywords_found', ''),
                    'full_analysis': metadata.get('full_analysis', ''),
                    'full_article_data': metadata.get('full_article_data', ''),
                    'embedding': match.values  # Include the pre-computed embedding
                })
            
            print(f"📊 ARTICLES RETRIEVED WITH EMBEDDINGS:")
            print(f"   Total articles: {len(articles)}")
            print(f"   Articles with embeddings: {articles_with_embeddings}")
            print(f"   Embedding availability: {articles_with_embeddings/len(articles)*100:.1f}%" if articles else "N/A")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting all articles: {e}")
            return []
    
    def get_articles_with_date_filter(self, date_filter: str, top_k: int = 1000) -> List[Dict]:
        """Get articles filtered by date at database level for better performance"""
        try:
            # Use a generic query to get articles
            query_embedding = self.generate_embedding("article")
            
            # Build Pinecone metadata filter for date
            pinecone_filter = self._build_date_filter(date_filter)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=pinecone_filter,
                include_metadata=True,
                include_values=True
            )
            
            # Format results with complete metadata
            articles = []
            articles_with_embeddings = 0
            for match in results.matches:
                metadata = match.metadata
                has_embedding = match.values is not None
                if has_embedding:
                    articles_with_embeddings += 1
                
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
                    'text': metadata.get('text', ''),
                    'analysis_timestamp': metadata.get('analysis_timestamp', ''),
                    'entity': metadata.get('entity', ''),
                    'authors': metadata.get('authors', []),
                    'keywords': metadata.get('keywords', []),
                    'summary': metadata.get('summary', ''),
                    'meta_description': metadata.get('meta_description', ''),
                    'sentiment_justification': metadata.get('sentiment_justification', ''),
                    'risk_categories': metadata.get('risk_categories', ''),
                    'risk_indicators': metadata.get('risk_indicators', ''),
                    'extraction_time': metadata.get('extraction_time', ''),
                    'analysis_method': metadata.get('analysis_method', ''),
                    'sentiment_method': metadata.get('sentiment_method', ''),
                    'risk_method': metadata.get('risk_method', ''),
                    'storage_type': metadata.get('storage_type', ''),
                    'keywords_found': metadata.get('keywords_found', ''),
                    'full_analysis': metadata.get('full_analysis', ''),
                    'embedding': match.values if has_embedding else None
                })
            
            print(f"📊 ARTICLES RETRIEVED WITH DATE FILTER:")
            print(f"   Total articles: {len(articles)}")
            print(f"   Articles with embeddings: {articles_with_embeddings}")
            print(f"   Embedding availability: {(articles_with_embeddings/len(articles)*100):.1f}%" if articles else "0%")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles with date filter: {e}")
            return []
    
    def get_articles_with_filters(self, date_filter: str = None, entity_filter: str = None, top_k: int = 1000) -> List[Dict]:
        """Get articles with both date and entity filters applied at database level"""
        try:
            # Use a generic query to get articles
            query_embedding = self.generate_embedding("article")
            
            # Build Pinecone metadata filter
            pinecone_filter = self._build_combined_filter(date_filter, entity_filter)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=pinecone_filter,
                include_metadata=True,
                include_values=True
            )
            
            # Format results with complete metadata
            articles = []
            articles_with_embeddings = 0
            for match in results.matches:
                metadata = match.metadata
                has_embedding = match.values is not None
                if has_embedding:
                    articles_with_embeddings += 1
                
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
                    'text': metadata.get('text', ''),
                    'analysis_timestamp': metadata.get('analysis_timestamp', ''),
                    'entity': metadata.get('entity', ''),
                    'authors': metadata.get('authors', []),
                    'keywords': metadata.get('keywords', []),
                    'summary': metadata.get('summary', ''),
                    'meta_description': metadata.get('meta_description', ''),
                    'sentiment_justification': metadata.get('sentiment_justification', ''),
                    'risk_categories': metadata.get('risk_categories', ''),
                    'risk_indicators': metadata.get('risk_indicators', ''),
                    'extraction_time': metadata.get('extraction_time', ''),
                    'analysis_method': metadata.get('analysis_method', ''),
                    'sentiment_method': metadata.get('sentiment_method', ''),
                    'risk_method': metadata.get('risk_method', ''),
                    'storage_type': metadata.get('storage_type', ''),
                    'keywords_found': metadata.get('keywords_found', ''),
                    'full_analysis': metadata.get('full_analysis', ''),
                    'embedding': match.values if has_embedding else None
                })
            
            print(f"📊 ARTICLES RETRIEVED WITH FILTERS:")
            print(f"   Date filter: {date_filter or 'None'}")
            print(f"   Entity filter: {entity_filter or 'None'}")
            print(f"   Total articles: {len(articles)}")
            print(f"   Articles with embeddings: {articles_with_embeddings}")
            print(f"   Embedding availability: {(articles_with_embeddings/len(articles)*100):.1f}%" if articles else "0%")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles with filters: {e}")
            return []
    
    def _build_date_filter(self, date_filter: str) -> Dict:
        """Build Pinecone metadata filter for date filtering"""
        if not date_filter or date_filter == "All Dates":
            return None
        
        try:
            from datetime import datetime, timedelta
            
            if date_filter == "Last 7 days":
                cutoff_date = datetime.now() - timedelta(days=7)
            elif date_filter == "Last 30 days":
                cutoff_date = datetime.now() - timedelta(days=30)
            else:
                # Specific date format: YYYY-MM-DD
                cutoff_date = datetime.strptime(date_filter, "%Y-%m-%d")
            
            # Convert to timestamp for Pinecone filtering
            cutoff_timestamp = cutoff_date.timestamp()
            
            return {
                "analysis_timestamp": {"$gte": cutoff_timestamp}
            }
            
        except Exception as e:
            logger.error(f"Error building date filter: {e}")
            return None
    
    def _build_combined_filter(self, date_filter: str = None, entity_filter: str = None) -> Dict:
        """Build Pinecone metadata filter combining date and entity filters"""
        filters = []
        
        # Add date filter
        if date_filter and date_filter != "All Dates":
            date_filter_dict = self._build_date_filter(date_filter)
            if date_filter_dict:
                filters.append(date_filter_dict)
        
        # Add entity filter (if entity field is populated)
        if entity_filter and entity_filter != "All Companies":
            # Note: Entity filtering at Pinecone level only works if entity field is properly populated
            # For now, we'll do entity filtering in memory after date filtering
            pass
        
        if not filters:
            return None
        elif len(filters) == 1:
            return filters[0]
        else:
            return {"$and": filters}
    
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
