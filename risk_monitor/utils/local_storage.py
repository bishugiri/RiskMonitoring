"""
Local Storage Fallback for Risk Monitor
Stores article analysis results locally when Pinecone is not available
"""

import json
import os
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from risk_monitor.config.settings import Config

logger = logging.getLogger(__name__)

class LocalStorage:
    """Local storage for article analysis results when Pinecone is not available"""
    
    def __init__(self):
        self.config = Config()
        self.storage_dir = os.path.join(self.config.OUTPUT_DIR, "local_storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create subdirectories
        self.articles_dir = os.path.join(self.storage_dir, "articles")
        self.index_dir = os.path.join(self.storage_dir, "index")
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Index file to track all stored articles
        self.index_file = os.path.join(self.index_dir, "articles_index.json")
        self._load_index()
    
    def _load_index(self):
        """Load the articles index"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.articles_index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self.articles_index = {}
        else:
            self.articles_index = {}
    
    def _save_index(self):
        """Save the articles index"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles_index, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
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
        """Format comprehensive metadata for local storage"""
        
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
            'risk_categories': risk_categories,
            'risk_indicators': risk_indicators,
            'keywords_found': risk_analysis.get('keywords_found', []),
            
            # Processing metadata
            'extraction_time': article.get('extraction_time', ''),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': analysis_result.get('analysis_method', 'lexicon'),
            
            # Full analysis result (for complete data preservation)
            'full_analysis': analysis_result,
            'full_article_data': article
        }
        
        return metadata
    
    def store_article(self, article: Dict, analysis_result: Dict) -> bool:
        """Store article with analysis results locally"""
        try:
            # Create unique ID
            article_id = self.create_article_id(article)
            
            # Format metadata
            metadata = self.format_metadata(article, analysis_result)
            
            # Save to file
            filename = f"{article_id}.json"
            filepath = os.path.join(self.articles_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            # Update index
            self.articles_index[article_id] = {
                'filename': filename,
                'title': article.get('title', ''),
                'source': metadata['source'],
                'publish_date': metadata['publish_date'],
                'sentiment_category': metadata['sentiment_category'],
                'sentiment_score': metadata['sentiment_score'],
                'risk_score': metadata['risk_score'],
                'stored_at': datetime.now().isoformat()
            }
            self._save_index()
            
            logger.info(f"Successfully stored article locally: {article.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing article locally: {e}")
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
        
        logger.info(f"Local batch storage complete: {success_count} successful, {error_count} errors")
        return result
    
    def search_articles(self, query: str = None, sentiment_category: str = None, 
                       source: str = None, limit: int = 10) -> List[Dict]:
        """Search articles by various criteria"""
        results = []
        
        for article_id, article_info in self.articles_index.items():
            # Apply filters
            if sentiment_category and article_info['sentiment_category'] != sentiment_category:
                continue
            if source and source.lower() not in article_info['source'].lower():
                continue
            
            # Load full article data
            try:
                filename = article_info['filename']
                filepath = os.path.join(self.articles_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                
                results.append({
                    'id': article_id,
                    'title': full_data['title'],
                    'source': full_data['source'],
                    'publish_date': full_data['publish_date'],
                    'sentiment_category': full_data['sentiment_category'],
                    'sentiment_score': full_data['sentiment_score'],
                    'risk_score': full_data['risk_score'],
                    'url': full_data['url'],
                    'summary': full_data['summary'],
                    'full_analysis': full_data['full_analysis']
                })
                
                if len(results) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error loading article {article_id}: {e}")
                continue
        
        # Sort by publish date (newest first)
        results.sort(key=lambda x: x['publish_date'], reverse=True)
        return results
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get local storage statistics"""
        try:
            total_files = len([f for f in os.listdir(self.articles_dir) if f.endswith('.json')])
            
            # Calculate sentiment distribution
            sentiment_counts = {}
            for article_info in self.articles_index.values():
                category = article_info['sentiment_category']
                sentiment_counts[category] = sentiment_counts.get(category, 0) + 1
            
            return {
                'total_articles': total_files,
                'index_entries': len(self.articles_index),
                'sentiment_distribution': sentiment_counts,
                'storage_path': self.storage_dir
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
