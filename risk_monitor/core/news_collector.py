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
from concurrent.futures import ThreadPoolExecutor

from risk_monitor.config.settings import Config

class NewsCollector:
    """Collects news articles using SerpAPI and extracts their content"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate_config()
        self.setup_logging()
    
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
        
        params = {
            'q': query,
            'api_key': Config.get_serpapi_key(),
            'engine': 'google_news',
            'num': num_results,
            'tbm': 'nws'  # News search
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config.SERPAPI_BASE_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if 'news_results' in data:
                        articles = data['news_results']
                        self.logger.info(f"Found {len(articles)} news articles")
                        return articles
                    else:
                        self.logger.warning("No news results found in API response")
                        return []
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Error searching news: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
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
        # Run the async function in a synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.search_news_async(query, num_results))
        finally:
            loop.close()
    
    def extract_article_content(self, url: str) -> Optional[Dict]:
        """
        Extract content from a news article URL
        
        Args:
            url: URL of the article to extract
            
        Returns:
            Dictionary containing extracted article data or None if failed
        """
        try:
            self.logger.info(f"Extracting content from: {url}")
            
            # Use newspaper3k to extract article content
            article = Article(url)
            article.download()
            article.parse()
            
            # Extract text content
            text = article.text.strip()
            
            if not text:
                self.logger.warning(f"No text content extracted from {url}")
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
        Asynchronously collect and extract content from news articles
        
        Args:
            query: Search query
            num_articles: Number of articles to process
            
        Returns:
            List of dictionaries containing article data
        """
        # Search for news articles
        articles = await self.search_news_async(query, num_articles)
        
        if not articles:
            self.logger.error("No articles found from search")
            return []
        
        # Limit the number of articles to process
        if num_articles and len(articles) > num_articles:
            self.logger.info(f"Limiting articles from {len(articles)} to {num_articles}")
            articles = articles[:num_articles]
        
        extracted_articles = []
        tasks = []
        
        # Create tasks for all articles
        for i, article in enumerate(articles, 1):
            url = article.get('link')
            if not url:
                self.logger.warning(f"No URL found for article {i}")
                continue
                
            # Create a task for each article
            task = asyncio.create_task(self._process_article(article, i, len(articles)))
            tasks.append(task)
        
        # Process all articles concurrently
        if tasks:
            results = await asyncio.gather(*tasks)
            extracted_articles = [result for result in results if result]
        
        self.logger.info(f"Successfully extracted {len(extracted_articles)} articles")
        return extracted_articles
        
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
        # Run the async function in a synchronous context
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
