"""
Scheduler Module for Risk Monitoring Tool
Handles automated daily data refresh and scheduled news collection
Uses asynchronous operations for improved performance
"""

import schedule
import time
import logging
import os
import json
import datetime
import pytz
import re
import asyncio
from typing import Dict, List, Optional, Any
import argparse
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

from risk_monitor.core.news_collector import NewsCollector
from risk_monitor.core.risk_analyzer import RiskAnalyzer
from risk_monitor.config.settings import Config
from risk_monitor.utils.sentiment import analyze_sentiment_lexicon, analyze_sentiment_structured, analyze_sentiment_lexicon_structured
from risk_monitor.utils.emailer import send_html_email, format_daily_summary_html, format_detailed_email_html

# Try to import PineconeDB, but handle gracefully if not available
try:
    from risk_monitor.utils.pinecone_db import PineconeDB
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PineconeDB not available - Pinecone storage will be disabled")

# Configure logging
logger = logging.getLogger("scheduler")

class SchedulerConfig:
    """Configuration for the scheduler"""
    DEFAULT_RUN_TIME = "08:00"  # 8:00 AM
    DEFAULT_TIMEZONE = "US/Eastern"  # Eastern Time
    DEFAULT_ARTICLES_PER_ENTITY = 5
    
    def __init__(self, config_file: str = None):
        """Initialize scheduler configuration"""
        self.config = Config()
        
        if config_file is None:
            self.config_file = self.config.SCHEDULER_CONFIG_FILE
        else:
            self.config_file = config_file
            
        self.run_time = self.DEFAULT_RUN_TIME
        self.timezone = self.DEFAULT_TIMEZONE
        self.articles_per_entity = self.DEFAULT_ARTICLES_PER_ENTITY
        self.entities = []
        self.keywords = []
        self.use_openai = True
        # Email settings
        self.email_enabled = True
        self.email_recipients = []
        # Enhanced automation features
        self.enable_pinecone_storage = PINECONE_AVAILABLE
        self.enable_dual_sentiment = True
        self.enable_detailed_email = True
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.run_time = config.get('run_time', self.DEFAULT_RUN_TIME)
                self.timezone = config.get('timezone', self.DEFAULT_TIMEZONE)
                self.articles_per_entity = config.get('articles_per_entity', self.DEFAULT_ARTICLES_PER_ENTITY)
                self.entities = config.get('entities', [])
                self.keywords = config.get('keywords', [])
                self.use_openai = config.get('use_openai', True)
                self.email_enabled = config.get('email_enabled', True)
                self.email_recipients = config.get('email_recipients', [])
                self.enable_pinecone_storage = config.get('enable_pinecone_storage', PINECONE_AVAILABLE) and PINECONE_AVAILABLE
                self.enable_dual_sentiment = config.get('enable_dual_sentiment', True)
                self.enable_detailed_email = config.get('enable_detailed_email', True)
                
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(f"Configuration file {self.config_file} not found. Using defaults.")
                self.save_config()  # Create default config file
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Use defaults
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'run_time': self.run_time,
            'timezone': self.timezone,
            'articles_per_entity': self.articles_per_entity,
            'entities': self.entities,
            'keywords': self.keywords,
            'use_openai': self.use_openai,
            'email_enabled': self.email_enabled,
            'email_recipients': self.email_recipients,
            'enable_pinecone_storage': self.enable_pinecone_storage,
            'enable_dual_sentiment': self.enable_dual_sentiment,
            'enable_detailed_email': self.enable_detailed_email
        }
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

class NewsScheduler:
    """Scheduler for automated news collection and analysis"""
    
    def __init__(self, config_file: str = None):
        """Initialize the scheduler with configuration"""
        # Set up logging
        self.setup_logging()
        
        # Initialize configuration
        self.config = SchedulerConfig(config_file)
        self.collector = NewsCollector()
        self.analyzer = RiskAnalyzer()
        self.pinecone_db = PineconeDB() if self.config.enable_pinecone_storage and PINECONE_AVAILABLE else None
        logger.info("NewsScheduler initialized with enhanced automation features")
    
    def setup_logging(self):
        """Set up logging configuration"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "scheduler.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def collect_entity_news(self, entity: str, num_articles: int) -> List[Dict]:
        """Collect news for a specific entity (synchronous version)"""
        logger.info(f"Collecting news for entity: {entity}")
        try:
            articles = self.collector.collect_articles(
                query=entity,
                num_articles=num_articles
            )
            
            # Add entity information to each article
            for article in articles:
                article['entity'] = entity
            
            logger.info(f"Collected {len(articles)} articles for {entity}")
            return articles
        except Exception as e:
            logger.error(f"Error collecting news for {entity}: {e}")
            return []
            
    async def collect_entity_news_async(self, entity: str, num_articles: int) -> List[Dict]:
        """Collect news for a specific entity asynchronously with optimized performance"""
        logger.info(f"Collecting news for entity: {entity}")
        try:
            # Use the optimized async collection method
            articles = await self.collector.collect_articles_async(
                query=entity,
                num_articles=num_articles
            )
            
            # Add entity information to each article
            for article in articles:
                article['entity'] = entity
            
            logger.info(f"Collected {len(articles)} articles for {entity}")
            return articles
        except Exception as e:
            logger.error(f"Error collecting news for {entity}: {e}")
            return []
    
    async def analyze_sentiment_dual_async(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment using both LLM and lexicon methods with structured approach"""
        logger.info(f"Performing dual structured sentiment analysis for {len(articles)} articles")
        
        # Create tasks for both LLM and lexicon analysis
        llm_task = self.analyze_sentiment_with_openai_structured_async(articles) if self.config.use_openai else None
        lexicon_task = self.analyze_sentiment_with_lexicon_structured_async(articles)
        
        # Run both analyses concurrently
        tasks = [lexicon_task]
        if llm_task:
            tasks.append(llm_task)
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        lexicon_results = results[0]
        if len(results) > 1:
            llm_results = results[1]
            # Merge LLM results into lexicon results
            for i, article in enumerate(lexicon_results):
                if i < len(llm_results):
                    article['llm_sentiment'] = llm_results[i].get('sentiment_analysis', {})
                    article['sentiment_method'] = 'dual_structured'
                else:
                    article['sentiment_method'] = 'lexicon_structured_only'
        else:
            for article in lexicon_results:
                article['sentiment_method'] = 'lexicon_structured_only'
        
        return lexicon_results
    
    async def analyze_sentiment_with_lexicon_structured_async(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment using lexicon-based structured method asynchronously"""
        logger.info(f"Analyzing sentiment for {len(articles)} articles using structured lexicon (async)")
        
        # Use thread pool for CPU-bound lexicon analysis
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            processed_articles = await loop.run_in_executor(
                executor,
                self._analyze_with_lexicon_structured,
                articles
            )
        
        return processed_articles
    
    async def analyze_sentiment_with_openai_structured_async(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment of articles using OpenAI API with structured approach asynchronously"""
        from openai import OpenAI
        
        # Get OpenAI API key from config
        import httpx
        client = OpenAI(api_key=Config.get_openai_api_key(), http_client=httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        ))
        
        logger.info(f"Analyzing sentiment for {len(articles)} articles using OpenAI structured (async)")
        
        # Create a list to store tasks
        tasks = []
        
        # Create a task for each article
        for i, article in enumerate(articles):
            task = asyncio.create_task(self._analyze_article_sentiment_structured(article, i, len(articles), client))
            tasks.append(task)
        
        # Process all articles concurrently (with rate limiting)
        processed_articles = await asyncio.gather(*tasks)
        
        # Return the processed articles
        return processed_articles
        
    async def _analyze_article_sentiment_structured(self, article: Dict, index: int, total: int, client: OpenAI) -> Dict:
        """Analyze sentiment for a single article using structured approach asynchronously"""
        
        try:
            # Get title and text
            title = article.get('title', '')
            text = article.get('text', '')
            
            # Use the new structured sentiment analysis
            result = await analyze_sentiment_structured(text, title, Config.get_openai_api_key())
            
            # Convert structured result to legacy format for compatibility
            sentiment = {
                'score': result.get('sentiment_score', 0),
                'category': self._convert_score_to_category(result.get('sentiment_score', 0)),
                'justification': result.get('reasoning', ''),
                'entity': result.get('entity', 'Unknown'),
                'event_type': result.get('event_type', 'other'),
                'key_quotes': result.get('key_quotes', []),
                'summary': result.get('summary', '')
            }
            
            # Add sentiment analysis to article
            article['sentiment_analysis'] = sentiment
            article['sentiment_method'] = 'llm_structured'
            
            logger.info(f"Analyzed article {index+1}/{total}: {sentiment['category']} ({sentiment['score']}) - Entity: {sentiment['entity']}, Event: {sentiment['event_type']}")
            
            # Add a small delay to avoid rate limits (but allow other tasks to run)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for article {index+1}: {e}")
            # Add default sentiment
            article['sentiment_analysis'] = {
                'score': 0.0,
                'category': 'Neutral',
                'justification': f'Error analyzing sentiment: {str(e)}',
                'entity': 'Unknown',
                'event_type': 'other',
                'key_quotes': [],
                'summary': 'Analysis failed'
            }
            article['sentiment_method'] = 'llm_structured_error'
        
        return article
    
    def _convert_score_to_category(self, score: float) -> str:
        """Convert sentiment score to category"""
        if score > 0.1:
            return 'Positive'
        elif score < -0.1:
            return 'Negative'
        else:
            return 'Neutral'
    
    async def store_articles_in_pinecone_async(self, articles: List[Dict]) -> Dict[str, int]:
        """Store articles in Pinecone database asynchronously"""
        if not self.pinecone_db:
            logger.warning("Pinecone storage not enabled")
            return {'success_count': 0, 'error_count': 0, 'total_count': len(articles)}
        
        logger.info(f"Storing {len(articles)} articles in Pinecone database")
        
        # Use thread pool for database operations
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self._store_articles_batch,
                articles
            )
        
        return result
    
    def _store_articles_batch(self, articles: List[Dict]) -> Dict[str, int]:
        """Store articles in Pinecone database (helper method)"""
        success_count = 0
        error_count = 0
        
        for article in articles:
            try:
                # Create analysis result for storage
                analysis_result = {
                    'sentiment_analysis': article.get('sentiment_analysis', {}),
                    'risk_analysis': article.get('risk_analysis', {}),
                    'analysis_method': article.get('sentiment_method', 'unknown')
                }
                
                if self.pinecone_db.store_article(article, analysis_result):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error storing article in Pinecone: {e}")
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_count': len(articles)
        }
        
        logger.info(f"Pinecone storage complete: {success_count} successful, {error_count} errors")
        return result
    
    def run_daily_collection(self):
        """Run the daily news collection and analysis (synchronous wrapper)"""
        # Run the async function in a synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run_daily_collection_async())
        finally:
            loop.close()
            
    async def run_daily_collection_async(self):
        """Run the daily news collection and analysis asynchronously with performance optimizations"""
        logger.info("Starting enhanced daily news collection (async)")
        
        # Check if we have entities to monitor
        if not self.config.entities:
            logger.warning("No entities configured for monitoring")
            return
        
        # Get current timestamp for file naming
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        all_articles = []
        
        # Create tasks for collecting news for each entity
        entity_tasks = []
        for entity in self.config.entities:
            task = self.collect_entity_news_async(
                entity, 
                self.config.articles_per_entity
            )
            entity_tasks.append(task)
        
        # Run all entity collection tasks concurrently
        logger.info(f"Starting concurrent collection for {len(self.config.entities)} entities")
        entity_results = await asyncio.gather(*entity_tasks)
        
        # Combine results
        for entity_articles in entity_results:
            all_articles.extend(entity_articles)
        
        logger.info(f"Total articles collected: {len(all_articles)}")
        
        # Filter articles by keywords if specified
        if self.config.keywords:
            logger.info(f"Filtering articles by keywords: {self.config.keywords}")
            filtered_articles = []
            for article in all_articles:
                text = article.get('text', '').lower()
                title = article.get('title', '').lower()
                if any(keyword.lower() in text or keyword.lower() in title for keyword in self.config.keywords):
                    filtered_articles.append(article)
            all_articles = filtered_articles
            logger.info(f"Articles after keyword filtering: {len(all_articles)}")
        
        if not all_articles:
            logger.warning("No articles found after collection and filtering")
            return
        
        # Perform analysis with optimized batch processing
        logger.info("Starting optimized batch analysis")
        analyzed_articles = await self.analyzer.analyze_articles_async(
            all_articles, 
            sentiment_method='llm'
        )
        
        # Update all_articles with analysis results
        all_articles = analyzed_articles
        
        # Store results in database if enabled
        if self.config.enable_pinecone_storage and PINECONE_AVAILABLE:
            logger.info("Storing results in Pinecone database")
            storage_stats = await self.pinecone_db.store_articles_batch_async(
                all_articles, 
                all_articles  # Pass analyzed articles as analysis results
            )
            logger.info(f"Storage completed: {storage_stats}")
        
        # Generate summary
        summary = self._generate_collection_summary(all_articles)
        
        # Save results to file
        output_file = f"output/daily_collection_{timestamp}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save both summary and full article data
        full_data = {
            'summary': summary,
            'articles': all_articles,
            'timestamp': timestamp
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_data, f, indent=2, default=str)
        
        logger.info(f"Daily collection completed. Results saved to {output_file}")
        
        # Send email if enabled
        if self.config.email_enabled:
            await self.send_daily_email(summary, all_articles)
        
        return summary

    def _generate_collection_summary(self, articles: List[Dict]) -> Dict:
        """Generate a summary of the collection and analysis results."""
        summary = {
            'total_articles_collected': len(articles),
            'total_articles_analyzed': len(articles),
            'summary_sentiment': {},
            'summary_risk': {},
            'article_analysis_summary': {},
            'risk_analysis_summary': {}
        }

        # Calculate sentiment summary
        sentiment_scores = []
        sentiment_counts = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
        
        for article in articles:
            sentiment_analysis = article.get('sentiment_analysis', {})
            if isinstance(sentiment_analysis, dict) and 'score' in sentiment_analysis:
                sentiment_scores.append(sentiment_analysis['score'])
                category = sentiment_analysis.get('category', 'Neutral')
                sentiment_counts[category] = sentiment_counts.get(category, 0) + 1
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        summary['summary_sentiment'] = {
            'average_score': avg_sentiment,
            'positive_count': sentiment_counts['Positive'],
            'neutral_count': sentiment_counts['Neutral'],
            'negative_count': sentiment_counts['Negative']
        }

        # Calculate risk summary
        risk_scores = []
        for article in articles:
            risk_analysis = article.get('risk_analysis', {})
            if isinstance(risk_analysis, dict) and 'overall_risk_score' in risk_analysis:
                risk_scores.append(risk_analysis['overall_risk_score'])
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        summary['summary_risk'] = {
            'average_score': avg_risk,
            'total_articles': len(risk_scores)
        }

        return summary
    
    async def send_daily_email(self, summary: Dict, articles: List[Dict]):
        """Send daily email report with analysis results."""
        try:
            logger.info("Preparing daily email report")
            
            # Calculate executive summary metrics
            total_articles = len(articles)
            
            # Calculate average sentiment score
            sentiment_scores = []
            for article in articles:
                sentiment_analysis = article.get('sentiment_analysis', {})
                if isinstance(sentiment_analysis, dict) and 'score' in sentiment_analysis:
                    sentiment_scores.append(sentiment_analysis['score'])
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            # Calculate average risk score
            risk_scores = []
            for article in articles:
                risk_analysis = article.get('risk_analysis', {})
                if isinstance(risk_analysis, dict) and 'overall_risk_score' in risk_analysis:
                    risk_scores.append(risk_analysis['overall_risk_score'])
            
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            
            # Create executive summary
            exec_summary = {
                'total_articles': total_articles,
                'avg_sentiment': avg_sentiment,
                'avg_risk_score': avg_risk
            }
            
            # Get top negative articles (sorted by sentiment score)
            top_negative = sorted(articles, key=lambda x: x.get('sentiment_analysis', {}).get('score', 0))[:10]
            
            # Choose email format based on configuration
            if self.config.enable_detailed_email:
                html_body = format_detailed_email_html(exec_summary, top_negative, articles)
                subject = "Daily Risk Monitor Report - Detailed Analysis"
            else:
                html_body = format_daily_summary_html(exec_summary, top_negative)
                subject = "Daily Risk Monitor Report - Summary"
            
            # Send email
            send_html_email(
                subject=subject,
                html_body=html_body,
                recipients=self.config.email_recipients
            )
            
            logger.info("Daily summary email sent")
            
        except Exception as e:
            logger.error(f"Error sending daily email: {e}")
        
    def _filter_articles_by_keywords(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles by keywords (helper method for async operation)"""
        filtered_articles = []
        
        for article in articles:
            # Check if any keyword is in title or text
            title = article.get('title', '').lower()
            text = article.get('text', '').lower()
            
            for keyword in self.config.keywords:
                if keyword.lower() in title or keyword.lower() in text:
                    article['matched_keywords'] = article.get('matched_keywords', []) + [keyword]
                    filtered_articles.append(article)
                    break
                    
        return filtered_articles
        
    def _analyze_with_lexicon_structured(self, articles: List[Dict]) -> List[Dict]:
        """Analyze articles with lexicon-based structured sentiment analysis"""
        for article in articles:
            # Get title and text
            title = article.get('title', '')
            text = article.get('text', '')
            
            # Use the new structured lexicon analysis
            result = analyze_sentiment_lexicon_structured(text, title)
            
            # Convert structured result to legacy format for compatibility
            sentiment = {
                'score': result.get('sentiment_score', 0),
                'category': self._convert_score_to_category(result.get('sentiment_score', 0)),
                'justification': result.get('reasoning', ''),
                'entity': result.get('entity', 'Unknown'),
                'event_type': result.get('event_type', 'other'),
                'key_quotes': result.get('key_quotes', []),
                'summary': result.get('summary', '')
            }
            
            article['sentiment_analysis'] = sentiment
            article['sentiment_method'] = 'lexicon_structured'
            
        return articles
    
    def _analyze_with_lexicon(self, articles: List[Dict]) -> List[Dict]:
        """Legacy method: Analyze articles with basic lexicon-based sentiment analysis"""
        for article in articles:
            # Combine title and text for analysis
            text = f"{article.get('title', '')} {article.get('text', '')}"
            
            sentiment = analyze_sentiment_lexicon(text)
            article['sentiment_analysis'] = sentiment
            article['sentiment_method'] = 'lexicon'
            
        return articles
        

    
    def schedule_daily_run(self):
        """Schedule the daily news collection"""
        # Get run time from config
        run_time = self.config.run_time
        
        # Schedule the job
        schedule.every().day.at(run_time).do(self.run_daily_collection)
        logger.info(f"Scheduled enhanced daily news collection at {run_time} {self.config.timezone}")
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_now(self):
        """Run the news collection immediately"""
        logger.info("Running enhanced news collection immediately")
        self.run_daily_collection()
