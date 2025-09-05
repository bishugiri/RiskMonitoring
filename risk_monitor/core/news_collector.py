"""
News collection module for the Risk Monitor application.
Collects news articles using SerpAPI and extracts their content.
Uses asynchronous requests for improved performance.
"""

import requests
import aiohttp
import asyncio
import time
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from urllib.parse import urlparse
import newspaper
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from risk_monitor.config.settings import Config

# Try to import streamlit to check if we're in a Streamlit context
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

class NewsCollector:
    """Collects news articles using SerpAPI and extracts their content"""
    
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        # Performance optimization: Use a session for HTTP requests
        self.session = httpx.Client(timeout=10.0)
        # Blocked domains that frequently return 403
        self.blocked_domains = {
            'bloomberg.com', 'seekingalpha.com', 'wsj.com', 'ft.com',
            'nytimes.com', 'washingtonpost.com', 'latimes.com', 'chicagotribune.com', 'thestreet.com'
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config.LOG_FILE), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _is_blocked_domain(self, url: str) -> bool:
        """Check if URL is from a blocked domain"""
        try:
            domain = urlparse(url).netloc.lower()
            return any(blocked in domain for blocked in self.blocked_domains)
        except:
            return False
    
    def _run_without_streamlit_context(self, func, *args, **kwargs):
        """Run a function without Streamlit context to avoid ScriptRunContext errors"""
        if STREAMLIT_AVAILABLE:
            try:
                # Clear any existing Streamlit context
                import streamlit.runtime.scriptrunner as sr
                if hasattr(sr, 'get_script_run_ctx'):
                    ctx = sr.get_script_run_ctx()
                    if ctx is not None:
                        # We're in a Streamlit context, run in isolation
                        import threading
                        result = [None]
                        exception = [None]
                        
                        def run_in_thread():
                            try:
                                result[0] = func(*args, **kwargs)
                            except Exception as e:
                                exception[0] = e
                        
                        thread = threading.Thread(target=run_in_thread)
                        thread.start()
                        thread.join()
                        
                        if exception[0]:
                            raise exception[0]
                        return result[0]
            except Exception:
                # If context isolation fails, run normally
                pass
        
        # Run normally if not in Streamlit context or isolation failed
        return func(*args, **kwargs)

    async def search_news_async(self, query: str = None, num_results: int = None) -> List[Dict]:
        """
        Asynchronously search for news articles using SerpAPI
        
        Args:
            query: Search query (defaults to config query)
            num_results: Number of results to return (defaults to config value)
            
        Returns:
            List of article metadata dictionaries
        """
        query = query or self.config.SEARCH_QUERY
        num_results = num_results or self.config.NUM_ARTICLES
        
        self.logger.info(f"Searching for news with query: {query}, requesting {num_results} results")
        
        # Check if API key is available
        api_key = Config.get_serpapi_key()
        if not api_key:
            self.logger.error("❌ SerpAPI key not found in configuration")
            self.logger.error("   Please set SERPAPI_KEY in environment or Streamlit secrets")
            # Try to validate config to see if we can get more information
            try:
                self.config.validate_config()
            except Exception as e:
                self.logger.error(f"Configuration validation failed: {e}")
            return []
        
        self.logger.info(f"✅ SerpAPI key found (length: {len(api_key)}), making request...")
        
        params = {
            'q': query,
            'api_key': api_key,
            'engine': 'google_news',
            'num': num_results,
            'tbm': 'nws'  # News search
        }
        
        self.logger.info(f"🔧 Request URL: {self.config.SERPAPI_BASE_URL}")
        self.logger.info(f"🔧 Request params: {dict(params, api_key='***HIDDEN***')}")
        
        # Use synchronous requests instead of aiohttp for better compatibility
        return self._search_news_sync(params)
    
    def _search_news_sync(self, params: dict) -> List[Dict]:
        """Fast synchronous implementation with optimized parameters"""
        import requests
        
        # Fast retry logic - reduced attempts and timeout
        max_retries = 2  # Reduced from 3
        timeout = 30     # Reduced from 60 seconds
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries} - Making SerpAPI request...")
                
                # Add optimized parameters for faster response
                optimized_params = {
                    **params,
                    'safe': 'active',     # Safe search might be faster
                    'gl': 'us',           # Specific country
                    'hl': 'en',           # Specific language
                    'filter': '0'         # No filtering
                }
                
                response = requests.get(
                    self.config.SERPAPI_BASE_URL,
                    params=optimized_params,
                    timeout=timeout
                )
                
                self.logger.info(f"✅ SerpAPI response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                
                if 'news_results' in data:
                    articles = data['news_results']
                    self.logger.info(f"Found {len(articles)} news articles")
                    return articles
                else:
                    self.logger.warning("No news results found in API response")
                    return []
                    
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in 1 second...")
                    import time
                    time.sleep(1)  # Faster retry
                else:
                    self.logger.error("SerpAPI timeout - trying fallback")
                    return self._search_news_fallback(params)
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return self._search_news_fallback(params)
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return []
    
    def _search_news_fallback(self, params: dict) -> List[Dict]:
        """Fallback method with basic parameters only"""
        import requests
        try:
            self.logger.info("🔄 Trying fallback with basic parameters...")
            response = requests.get(
                self.config.SERPAPI_BASE_URL,
                params=params,  # Original parameters only
                timeout=45  # Slightly longer timeout for fallback
            )
            data = response.json()
            if 'news_results' in data:
                articles = data['news_results']
                self.logger.info(f"Fallback successful: {len(articles)} articles")
                return articles
        except Exception as e:
            self.logger.error(f"Fallback also failed: {e}")
        return []
            
    def search_news(self, query: str = None, num_results: int = None) -> List[Dict]:
        """
        Synchronous wrapper for search_news_async
        
        Args:
            query: Search query (defaults to config query)
            num_results: Number of results to return (defaults to config value)
            
        Returns:
            List of article metadata dictionaries
        """
        # Add debugging information
        self.logger.info(f"🔍 search_news called - checking event loop status...")
        
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            self.logger.info(f"🔍 Event loop already running: {loop}")
            # If we're in an async context, we need to run this differently
            import concurrent.futures
            self.logger.info(f"🔍 Using ThreadPoolExecutor for async execution...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_search_sync, query, num_results)
                try:
                    result = future.result(timeout=120)  # 2 minute timeout
                    self.logger.info(f"🔍 ThreadPoolExecutor completed successfully")
                    return result
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"🔍 ThreadPoolExecutor timed out after 120 seconds")
                    return []
        except RuntimeError:
            self.logger.info(f"🔍 No event loop running, creating new one...")
            # No event loop running, we can create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.search_news_async(query, num_results))
                self.logger.info(f"🔍 New event loop completed successfully")
                return result
            finally:
                loop.close()
                self.logger.info(f"🔍 Event loop closed")
    
    def _run_search_sync(self, query: str = None, num_results: int = None) -> List[Dict]:
        """Helper method to run search in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.search_news_async(query, num_results))
        finally:
            loop.close()
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_article_content(self, url: str) -> Optional[Dict]:
        """
        Extract content from a news article URL with retry logic and timeout
        
        Args:
            url: URL of the article to extract
            
        Returns:
            Dictionary containing extracted article data or None if failed
        """
        try:
            # Skip blocked domains to avoid wasting time
            if self._is_blocked_domain(url):
                self.logger.info(f"Skipping blocked domain: {url}")
                return None
            
            self.logger.info(f"Extracting content from: {url}")
            
            # Use newspaper3k with timeout and custom configuration
            article = Article(url)
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            article.config.request_timeout = 10
            article.config.number_threads = 1
            article.config.verbose = False
            
            # Set timeout for download
            article.download()
            article.parse()
            
            # Extract text content
            text = article.text.strip()
            
            if not text or len(text) < 50:  # Minimum content threshold
                self.logger.warning(f"Insufficient text content extracted from {url}")
                return None
            
            return {
                'url': url,
                'title': article.title,
                'text': text,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'authors': article.authors,
                'summary': article.summary,
                'keywords': article.keywords,
                'meta_description': article.meta_description,
                'extraction_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return None

    def extract_articles_concurrent(self, urls: List[str], max_workers: int = 5) -> List[Dict]:
        """
        Extract articles concurrently using ThreadPoolExecutor for better performance
        
        Args:
            urls: List of URLs to extract
            max_workers: Maximum number of concurrent workers
            
        Returns:
            List of extracted articles
        """
        # Check if we should use sequential processing to avoid Streamlit context issues
        if STREAMLIT_AVAILABLE and len(urls) <= 5:  # Use sequential for small batches
            self.logger.info("Using sequential processing to avoid Streamlit context issues")
            return self._extract_articles_sequential(urls)
        
        # Use context isolation to avoid Streamlit ScriptRunContext errors
        try:
            return self._run_without_streamlit_context(self._extract_articles_concurrent_isolated, urls, max_workers)
        except Exception as e:
            self.logger.warning(f"Concurrent extraction failed, falling back to sequential: {e}")
            return self._extract_articles_sequential(urls)
    
    def _extract_articles_concurrent_isolated(self, urls: List[str], max_workers: int = 5) -> List[Dict]:
        """Internal method that runs without Streamlit context"""
        extracted_articles = []
        
        # Create a standalone extraction function to avoid Streamlit context issues
        def extract_single_article(url: str) -> Optional[Dict]:
            """Extract a single article without Streamlit context dependencies"""
            try:
                # Skip blocked domains to avoid wasting time
                if self._is_blocked_domain(url):
                    self.logger.info(f"Skipping blocked domain: {url}")
                    return None
                
                self.logger.info(f"Extracting content from: {url}")
                
                # Use newspaper3k with timeout and custom configuration
                article = Article(url)
                article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                article.config.request_timeout = 10
                article.config.number_threads = 1
                article.config.verbose = False
                
                # Set timeout for download
                article.download()
                article.parse()
                
                # Extract text content
                text = article.text.strip()
                
                if not text or len(text) < 50:  # Minimum content threshold
                    self.logger.warning(f"Insufficient text content extracted from {url}")
                    return None
                
                return {
                    'url': url,
                    'title': article.title,
                    'text': text,
                    'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                    'authors': article.authors,
                    'summary': article.summary,
                    'keywords': article.keywords,
                    'meta_description': article.meta_description,
                    'extraction_time': time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Error extracting content from {url}: {e}")
                return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(extract_single_article, url): url for url in urls}
            
            # Process completed tasks
            for future in as_completed(future_to_url, timeout=30):  # 30 second timeout
                url = future_to_url[future]
                try:
                    result = future.result(timeout=5)  # 5 second timeout per article
                    if result:
                        extracted_articles.append(result)
                        self.logger.info(f"Successfully extracted: {result.get('title', 'Unknown')}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract {url}: {e}")
        
        return extracted_articles
    
    def _extract_articles_sequential(self, urls: List[str]) -> List[Dict]:
        """Extract articles sequentially to avoid Streamlit context issues"""
        extracted_articles = []
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Sequentially extracting article {i}/{len(urls)}: {url}")
            try:
                result = self.extract_article_content(url)
                if result:
                    extracted_articles.append(result)
                    self.logger.info(f"Successfully extracted: {result.get('title', 'Unknown')}")
            except Exception as e:
                self.logger.warning(f"Failed to extract {url}: {e}")
        
        return extracted_articles

    async def extract_article_content_async(self, url: str) -> Optional[Dict]:
        """
        Asynchronously extract content from a news article URL
        
        Args:
            url: URL of the article to extract
            
        Returns:
            Dictionary containing extracted article data or None if failed
        """
        # Since newspaper3k doesn't support async, we'll use a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.extract_article_content, url)
    
    async def collect_articles_async(self, query: str = None, num_articles: int = None) -> List[Dict]:
        """
        Fast collection: Request exactly N articles, filter blocked domains, extract content
        
        Args:
            query: Search query
            num_articles: Number of articles to process (N)
            
        Returns:
            List of dictionaries containing article data
        """
        # N = exact number of articles requested
        N = num_articles or self.config.NUM_ARTICLES
        
        self.logger.info(f"🚀 Fast Collection Strategy:")
        self.logger.info(f"   Requesting exactly {N} articles from SerpAPI")
        
        # Search for news articles - request exactly N
        articles = self._search_news_sync({
            'q': query or self.config.SEARCH_QUERY,
            'api_key': Config.get_serpapi_key(),
            'engine': 'google_news',
            'num': N,  # Request exactly N articles
            'tbm': 'nws'
        })
        
        if not articles:
            self.logger.error("No articles found from search")
            return []
        
        self.logger.info(f"✅ SerpAPI returned {len(articles)} articles")
        
        # FORCE LIMITING: SerpAPI often ignores num parameter, so we limit manually
        if len(articles) > N:
            self.logger.info(f"🔧 SerpAPI ignored num parameter - limiting from {len(articles)} to {N}")
            articles = articles[:N]  # Take first N articles (most relevant)
        
        # Filter out blocked domains and take available articles
        filtered_articles = []
        blocked_count = 0
        
        for article in articles:
            url = article.get('link')
            if url and not self._is_blocked_domain(url):
                filtered_articles.append(article)
            else:
                blocked_count += 1
        
        self.logger.info(f"🔍 Filtering Results:")
        self.logger.info(f"   Blocked domains skipped: {blocked_count}")
        self.logger.info(f"   Available articles: {len(filtered_articles)}")
        
        if not filtered_articles:
            self.logger.warning("All articles were from blocked domains")
            return []
        
        # Extract URLs for content extraction
        urls = [article.get('link') for article in filtered_articles]
        
        self.logger.info(f"⚡ Extracting content from {len(urls)} articles...")
        
        # Extract articles concurrently with reduced workers for speed
        extracted_articles = self.extract_articles_concurrent(urls, max_workers=10)
        
        # Combine search metadata with extracted content
        final_articles = []
        for extracted in extracted_articles:
            # Find matching article metadata
            matching_article = next((a for a in filtered_articles if a.get('link') == extracted['url']), {})
            full_article = {**matching_article, **extracted}
            final_articles.append(full_article)
        
        self.logger.info(f"✅ Successfully processed {len(final_articles)} articles")
        return final_articles
        
    async def _process_article(self, article: Dict, index: int, total: int) -> Optional[Dict]:
        """
        Process a single article asynchronously
        
        Args:
            article: Article metadata
            index: Article index (for logging)
            total: Total number of articles (for logging)
            
        Returns:
            Processed article or None if failed
        """
        self.logger.info(f"Processing article {index}/{total}")
        
        url = article.get('link')
        if not url:
            return None
            
        # Extract content from the article
        extracted_content = await self.extract_article_content_async(url)
        
        if extracted_content:
            # Combine search metadata with extracted content
            full_article = {
                **article,
                **extracted_content
            }
            self.logger.info(f"Successfully extracted article: {full_article.get('title', 'Unknown')}")
            return full_article
        else:
            self.logger.warning(f"Failed to extract content from article {index}")
            return None
    
    def collect_articles(self, query: str = None, num_articles: int = None) -> List[Dict]:
        """
        Synchronous wrapper for collect_articles_async
        
        Args:
            query: Search query
            num_articles: Number of articles to process
            
        Returns:
            List of dictionaries containing article data
        """
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to run this differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._run_collect_sync, query, num_articles)
                return future.result()
        except RuntimeError:
            # No event loop running, we can create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.collect_articles_async(query, num_articles))
            finally:
                loop.close()
    
    def _run_collect_sync(self, query: str = None, num_articles: int = None) -> List[Dict]:
        """Helper method to run collection in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.collect_articles_async(query, num_articles))
        finally:
            loop.close()
    
    def save_articles(self, articles: List[Dict], filename: str = None) -> str:
        """
        Save extracted articles to a file
        
        Args:
            articles: List of article dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finance_news_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved {len(articles)} articles to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving articles: {e}")
            raise
            
    async def save_articles_async(self, articles: List[Dict], filename: str = None) -> str:
        """
        Asynchronously save extracted articles to a file
        
        Args:
            articles: List of article dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        # Since file operations are blocking, we'll use a thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.save_articles, articles, filename)
