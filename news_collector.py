import requests
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
import newspaper
from newspaper import Article
from config import Config

class NewsCollector:
    """Collects news articles using SerpAPI and extracts their content"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate_config()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def search_news(self, query: str = None, num_results: int = None) -> List[Dict]:
        """
        Search for news articles using SerpAPI
        
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
            'api_key': self.config.SERPAPI_KEY,
            'engine': 'google_news',
            'num': num_results,
            'tbm': 'nws'  # News search
        }
        
        try:
            response = requests.get(
                self.config.SERPAPI_BASE_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'news_results' in data:
                articles = data['news_results']
                self.logger.info(f"Found {len(articles)} news articles")
                return articles
            else:
                self.logger.warning("No news results found in API response")
                return []
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching news: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
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
    
    def collect_articles(self, query: str = None, num_articles: int = None) -> List[Dict]:
        """
        Main method to collect and extract content from news articles
        
        Args:
            query: Search query
            num_articles: Number of articles to process
            
        Returns:
            List of dictionaries containing article data
        """
        # Search for news articles
        articles = self.search_news(query, num_articles)
        
        if not articles:
            self.logger.error("No articles found from search")
            return []
        
        # Limit the number of articles to process
        if num_articles and len(articles) > num_articles:
            self.logger.info(f"Limiting articles from {len(articles)} to {num_articles}")
            articles = articles[:num_articles]
        
        extracted_articles = []
        
        for i, article in enumerate(articles, 1):
            self.logger.info(f"Processing article {i}/{len(articles)}")
            
            url = article.get('link')
            if not url:
                self.logger.warning(f"No URL found for article {i}")
                continue
            
            # Extract content from the article
            extracted_content = self.extract_article_content(url)
            
            if extracted_content:
                # Combine search metadata with extracted content
                full_article = {
                    **article,
                    **extracted_content
                }
                extracted_articles.append(full_article)
                self.logger.info(f"Successfully extracted article: {full_article.get('title', 'Unknown')}")
            else:
                self.logger.warning(f"Failed to extract content from article {i}")
            
            # Add delay to be respectful to servers
            time.sleep(1)
        
        self.logger.info(f"Successfully extracted {len(extracted_articles)} articles")
        return extracted_articles
    
    def save_articles(self, articles: List[Dict], filename: str = None) -> str:
        """
        Save extracted articles to a file
        
        Args:
            articles: List of article dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        import json
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finance_news_{timestamp}.json"
        
        filepath = f"{self.config.OUTPUT_DIR}/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved {len(articles)} articles to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving articles: {e}")
            raise 