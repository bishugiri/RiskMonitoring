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

from risk_monitor.core.news_collector import NewsCollector
from risk_monitor.core.risk_analyzer import RiskAnalyzer
from risk_monitor.config.settings import Config
from risk_monitor.utils.sentiment import analyze_sentiment_lexicon
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
        """Collect news for a specific entity asynchronously"""
        logger.info(f"Collecting news for entity: {entity} (async)")
        try:
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
        """Analyze sentiment using both LLM and lexicon methods"""
        logger.info(f"Performing dual sentiment analysis for {len(articles)} articles")
        
        # Create tasks for both LLM and lexicon analysis
        llm_task = self.analyze_sentiment_with_openai_async(articles) if self.config.use_openai else None
        lexicon_task = self.analyze_sentiment_with_lexicon_async(articles)
        
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
                    article['sentiment_method'] = 'dual'
                else:
                    article['sentiment_method'] = 'lexicon_only'
        else:
            for article in lexicon_results:
                article['sentiment_method'] = 'lexicon_only'
        
        return lexicon_results
    
    async def analyze_sentiment_with_lexicon_async(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment using lexicon-based method asynchronously"""
        logger.info(f"Analyzing sentiment for {len(articles)} articles using lexicon (async)")
        
        # Use thread pool for CPU-bound lexicon analysis
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            processed_articles = await loop.run_in_executor(
                executor,
                self._analyze_with_lexicon,
                articles
            )
        
        return processed_articles
    
    async def analyze_sentiment_with_openai_async(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment of articles using OpenAI API asynchronously"""
        import openai
        
        # Get OpenAI API key from config
        openai.api_key = Config.get_openai_api_key()
        
        logger.info(f"Analyzing sentiment for {len(articles)} articles using OpenAI (async)")
        
        # Create a list to store tasks
        tasks = []
        
        # Create a task for each article
        for i, article in enumerate(articles):
            task = asyncio.create_task(self._analyze_article_sentiment(article, i, len(articles)))
            tasks.append(task)
        
        # Process all articles concurrently (with rate limiting)
        processed_articles = await asyncio.gather(*tasks)
        
        # Return the processed articles
        return processed_articles
        
    async def _analyze_article_sentiment(self, article: Dict, index: int, total: int) -> Dict:
        """Analyze sentiment for a single article asynchronously"""
        import openai
        
        try:
            # Combine title and text for analysis
            text = f"{article.get('title', '')} {article.get('text', '')}"
            
            # Truncate text if too long (OpenAI has token limits)
            if len(text) > 4000:
                text = text[:4000]
            
            # Create prompt for sentiment analysis
            prompt = f"""
            You are a financial news sentiment analysis assistant. Analyze the sentiment of the following financial news article text. 
            Provide your analysis in JSON format with the following structure:
            {{
              "score": <numerical score between -1.0 and 1.0>,
              "category": "<Positive, Neutral, or Negative>",
              "justification": "<brief explanation of your sentiment analysis>"
            }}

            Article text:
            {text}

            Focus on financial and market sentiment. Consider factors like:
            - Market impact and investor sentiment
            - Financial performance indicators
            - Risk and opportunity assessment
            - Overall market outlook
            """
            
            # Call OpenAI API (using a thread pool since the OpenAI client is not async)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor,
                    lambda: openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300,
                        temperature=0.2,
                    )
                )
            
            # Extract response
            response_text = response.choices[0].message.content
            
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                sentiment = json.loads(json_str)
                
                # Add sentiment analysis to article
                article['sentiment_analysis'] = sentiment
                article['sentiment_method'] = 'llm'
                
                logger.info(f"Analyzed article {index+1}/{total}: {sentiment['category']} ({sentiment['score']})")
            else:
                logger.warning(f"Could not parse JSON from OpenAI response for article {index+1}")
                # Add default sentiment
                article['sentiment_analysis'] = {
                    'score': 0.0,
                    'category': 'Neutral',
                    'justification': 'Could not analyze sentiment'
                }
                article['sentiment_method'] = 'llm_failed'
            
            # Add a small delay to avoid rate limits (but allow other tasks to run)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for article {index+1}: {e}")
            # Add default sentiment
            article['sentiment_analysis'] = {
                'score': 0.0,
                'category': 'Neutral',
                'justification': f'Error analyzing sentiment: {str(e)}'
            }
            article['sentiment_method'] = 'llm_error'
        
        return article
    
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
        """Run the daily news collection and analysis asynchronously"""
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
        entity_results = await asyncio.gather(*entity_tasks)
        
        # Combine results
        for entity_articles in entity_results:
            all_articles.extend(entity_articles)
        
        # Filter articles by keywords if specified
        if self.config.keywords:
            original_count = len(all_articles)
            filtered_articles = []
            
            # Create a task for filtering (can be done in a thread pool for better performance)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                filtered_articles = await loop.run_in_executor(
                    executor,
                    self._filter_articles_by_keywords,
                    all_articles
                )
            
            all_articles = filtered_articles
            logger.info(f"Filtered articles from {original_count} to {len(all_articles)} using keywords")
        
        # Perform dual sentiment analysis
        if self.config.enable_dual_sentiment:
            all_articles = await self.analyze_sentiment_dual_async(all_articles)
        elif self.config.use_openai:
            all_articles = await self.analyze_sentiment_with_openai_async(all_articles)
        else:
            # Use built-in lexicon-based sentiment analysis
            all_articles = await self.analyze_sentiment_with_lexicon_async(all_articles)
        
        # Run risk analysis
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                analysis = await loop.run_in_executor(
                    executor,
                    self.analyzer.analyze_articles,
                    all_articles
                )
            
            # Add risk analysis to articles
            # Create a mapping from URL to analysis for easy lookup
            article_analysis_mapping = {}
            for article_analysis in analysis.get('article_analysis', []):
                url = article_analysis.get('url', '')
                if url:
                    article_analysis_mapping[url] = article_analysis
            
            # Add risk analysis to each article
            for article in all_articles:
                url = article.get('url', '')
                if url in article_analysis_mapping:
                    article['risk_analysis'] = article_analysis_mapping[url]
                else:
                    article['risk_analysis'] = {}
            
            logger.info("Risk analysis completed")
        except Exception as e:
            logger.error(f"Error in risk analysis: {e}")
            # Add empty risk analysis to articles if analysis fails
            for article in all_articles:
                article['risk_analysis'] = {}
        
        # Store articles in Pinecone database
        if self.config.enable_pinecone_storage:
            storage_result = await self.store_articles_in_pinecone_async(all_articles)
            logger.info(f"Pinecone storage: {storage_result['success_count']}/{storage_result['total_count']} articles stored")
        
        # Save articles to local files
        if all_articles:
            # Save to output directory
            output_dir = self.config.config.OUTPUT_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            # Create filename with timestamp
            filename = f"scheduled_news_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Save to file (using a thread pool since file operations are blocking)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    self._save_articles_to_file,
                    all_articles,
                    filepath
                )
            
            logger.info(f"Saved {len(all_articles)} articles to {filepath}")
            
            # Save analysis to file
            analysis_filename = f"scheduled_analysis_{timestamp}.json"
            analysis_filepath = os.path.join(output_dir, analysis_filename)
            
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(
                    executor,
                    self._save_json_to_file,
                    analysis,
                    analysis_filepath
                )
            
            logger.info(f"Saved risk analysis to {analysis_filepath}")

            # Enhanced Email reporting
            try:
                if self.config.email_enabled:
                    # Prepare summary
                    summary = analysis.get('summary', {})
                    
                    # Identify top 10 most negative articles overall (by sentiment score ascending)
                    articles_with_sentiment = [a for a in all_articles if a.get('sentiment_analysis')]
                    top_negative = sorted(
                        articles_with_sentiment,
                        key=lambda a: a.get('sentiment_analysis', {}).get('score', 0)
                    )[:10]

                    if self.config.enable_detailed_email:
                        html = format_detailed_email_html(summary, top_negative, all_articles)
                    else:
                        html = format_daily_summary_html(summary, top_negative)
                    
                    send_html_email(
                        subject=f"Daily Risk Monitor Summary {timestamp}",
                        html_body=html,
                        recipients=self.config.email_recipients or Config.get_email_recipients(),
                    )
                    logger.info("Enhanced daily summary email sent")
            except Exception as e:
                logger.error(f"Failed to send daily email: {e}")
        else:
            logger.warning("No articles collected")
            
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
        
    def _analyze_with_lexicon(self, articles: List[Dict]) -> List[Dict]:
        """Analyze articles with lexicon-based sentiment analysis"""
        for article in articles:
            # Combine title and text for analysis
            text = f"{article.get('title', '')} {article.get('text', '')}"
            
            sentiment = analyze_sentiment_lexicon(text)
            article['sentiment_analysis'] = sentiment
            article['sentiment_method'] = 'lexicon'
            
        return articles
        
    def _save_articles_to_file(self, articles: List[Dict], filepath: str) -> None:
        """Save articles to a file (helper method for async operation)"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
            
    def _save_json_to_file(self, data: Any, filepath: str) -> None:
        """Save JSON data to a file (helper method for async operation)"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
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
