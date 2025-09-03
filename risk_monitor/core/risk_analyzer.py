"""
Risk analyzer module for the Risk Monitor application.
Analyzes news articles for potential risks and market sentiment using advanced LLM-based analysis.
"""

import re
import logging
import os
import json
import asyncio
from typing import List, Dict, Tuple, Any
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

from risk_monitor.config.settings import Config
from risk_monitor.utils.sentiment import analyze_sentiment_sync

# Try to import PineconeDB, but handle gracefully if not available
try:
    from risk_monitor.utils.pinecone_db import PineconeDB, AnalysisPineconeDB
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PineconeDB not available - Pinecone storage will be disabled")

class RiskAnalyzer:
    """Analyzes news articles for potential risks and market sentiment using advanced LLM analysis"""
    
    def __init__(self):
        self.setup_logging()
        self.config = Config()
        self.openai_client = None
        self._init_openai_client()
    
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = self.config.get_openai_api_key()
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                self.logger.info("OpenAI client initialized successfully")
            else:
                self.logger.warning("OpenAI API key not found - LLM analysis will be disabled")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    async def analyze_article_risk_llm(self, article: Dict) -> Dict:
        """
        Advanced LLM-based risk analysis for a single article
        Uses sophisticated prompts for comprehensive financial risk assessment
        """
        if not self.openai_client:
            return self._fallback_risk_analysis(article)
        
        try:
            title = article.get('title', '')
            text = article.get('text', '')
            source = self.extract_source(article.get('url', ''))
            
            # Create comprehensive risk analysis prompt
            system_prompt = """You are an expert financial risk analyst specializing in market risk assessment, economic analysis, and investment risk evaluation. Your role is to analyze financial news articles and provide comprehensive risk assessments.

ANALYSIS FRAMEWORK:
1. **Market Risk Assessment**: Evaluate potential market volatility, price movements, and trading risks
2. **Economic Risk Analysis**: Assess macroeconomic factors, policy changes, and economic indicators
3. **Sector-Specific Risk**: Identify industry-specific challenges and opportunities
4. **Company-Specific Risk**: Evaluate individual company performance and strategic risks
5. **Geopolitical Risk**: Consider international relations, trade policies, and political stability
6. **Regulatory Risk**: Assess compliance requirements and regulatory changes
7. **Operational Risk**: Evaluate business operations, supply chain, and execution risks
8. **Financial Risk**: Analyze liquidity, credit, and financial stability concerns

RISK SCORING METHODOLOGY:
- **Risk Score**: 0-10 scale (0=No Risk, 10=Extreme Risk)
- **Confidence Level**: 0-1 scale (0=Low Confidence, 1=High Confidence)
- **Risk Categories**: Market, Economic, Geopolitical, Sector, Company, Regulatory, Operational, Financial
- **Impact Assessment**: Immediate (0-3 months), Short-term (3-12 months), Long-term (1+ years)

Provide your analysis in the following JSON format:
{
  "overall_risk_score": <0-10>,
  "risk_confidence": <0-1>,
  "risk_categories": {
    "market_risk": {"score": <0-10>, "description": "<explanation>"},
    "economic_risk": {"score": <0-10>, "description": "<explanation>"},
    "geopolitical_risk": {"score": <0-10>, "description": "<explanation>"},
    "sector_risk": {"score": <0-10>, "description": "<explanation>"},
    "company_risk": {"score": <0-10>, "description": "<explanation>"},
    "regulatory_risk": {"score": <0-10>, "description": "<explanation>"},
    "operational_risk": {"score": <0-10>, "description": "<explanation>"},
    "financial_risk": {"score": <0-10>, "description": "<explanation>"}
  },
  "key_risk_indicators": ["<indicator1>", "<indicator2>", "<indicator3>"],
  "risk_summary": "<comprehensive risk assessment summary>",
  "recommendations": ["<recommendation1>", "<recommendation2>"],
  "impact_timeline": "<immediate/short-term/long-term>"
}"""

            user_prompt = f"""Please analyze the following financial news article for comprehensive risk assessment:

ARTICLE TITLE: {title}
SOURCE: {source}
ARTICLE TEXT: {text[:3000]}

Consider the following factors in your analysis:
- Market sentiment and potential price impacts
- Economic indicators and policy implications
- Industry-specific challenges and opportunities
- Company performance and strategic positioning
- Regulatory environment and compliance risks
- Operational efficiency and execution risks
- Financial health and stability concerns
- Geopolitical factors and international relations

Provide a detailed, nuanced risk assessment that considers both immediate and long-term implications."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                risk_analysis = json.loads(json_str)
                
                # Validate and normalize the analysis
                return self._validate_and_normalize_risk_analysis(risk_analysis, article)
            else:
                self.logger.warning("Could not extract JSON from LLM response, using fallback")
                return self._fallback_risk_analysis(article)
                
        except Exception as e:
            self.logger.error(f"Error in LLM risk analysis: {e}")
            return self._fallback_risk_analysis(article)
    
    def _validate_and_normalize_risk_analysis(self, risk_analysis: Dict, article: Dict) -> Dict:
        """Validate and normalize LLM risk analysis results"""
        try:
            # Ensure all required fields exist
            normalized = {
                'overall_risk_score': float(risk_analysis.get('overall_risk_score', 0)),
                'risk_confidence': float(risk_analysis.get('risk_confidence', 0.5)),
                'risk_categories': {},
                'key_risk_indicators': risk_analysis.get('key_risk_indicators', []),
                'risk_summary': risk_analysis.get('risk_summary', ''),
                'recommendations': risk_analysis.get('recommendations', []),
                'impact_timeline': risk_analysis.get('impact_timeline', 'short-term'),
                'analysis_method': 'llm',
                'article_metadata': {
                    'url': article.get('url', ''),
                    'title': article.get('title', ''),
                    'source': self.extract_source(article.get('url', '')),
                    'publish_date': article.get('publish_date', ''),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            # Normalize risk categories
            categories = risk_analysis.get('risk_categories', {})
            for category in ['market_risk', 'economic_risk', 'geopolitical_risk', 'sector_risk', 
                            'company_risk', 'regulatory_risk', 'operational_risk', 'financial_risk']:
                cat_data = categories.get(category, {})
                normalized['risk_categories'][category] = {
                    'score': float(cat_data.get('score', 0)),
                    'description': cat_data.get('description', 'No description available')
                }
            
            # Clamp scores to valid ranges
            normalized['overall_risk_score'] = max(0, min(10, normalized['overall_risk_score']))
            normalized['risk_confidence'] = max(0, min(1, normalized['risk_confidence']))
            
            for category in normalized['risk_categories']:
                normalized['risk_categories'][category]['score'] = max(0, min(10, 
                    normalized['risk_categories'][category]['score']))
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error validating risk analysis: {e}")
            return self._fallback_risk_analysis(article)
    
    def _fallback_risk_analysis(self, article: Dict) -> Dict:
        """Fallback risk analysis when LLM is not available"""
        return {
            'overall_risk_score': 5.0,
            'risk_confidence': 0.3,
            'risk_categories': {
                'market_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'economic_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'geopolitical_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'sector_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'company_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'regulatory_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'operational_risk': {'score': 5.0, 'description': 'Fallback analysis'},
                'financial_risk': {'score': 5.0, 'description': 'Fallback analysis'}
            },
            'key_risk_indicators': ['Fallback analysis - LLM not available'],
            'risk_summary': 'Fallback risk analysis performed due to LLM unavailability',
            'recommendations': ['Enable LLM analysis for comprehensive risk assessment'],
            'impact_timeline': 'unknown',
            'analysis_method': 'fallback',
            'article_metadata': {
                'url': article.get('url', ''),
                'title': article.get('title', ''),
                'source': self.extract_source(article.get('url', '')),
                'publish_date': article.get('publish_date', ''),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    def extract_source(self, url: str) -> str:
        """Extract source domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    async def analyze_articles_with_advanced_risk(self, articles: List[Dict], sentiment_method: str = 'llm') -> List[Dict]:
        """
        Analyze articles with advanced LLM-based risk analysis and sentiment analysis
        Returns comprehensive analysis results for each article
        """
        self.logger.info(f"Analyzing {len(articles)} articles with advanced LLM risk analysis")
        
        analysis_results = []
        
        for i, article in enumerate(articles):
            self.logger.info(f"Analyzing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
            
            # Perform advanced risk analysis
            risk_analysis = await self.analyze_article_risk_llm(article)
            
            # Perform sentiment analysis
            text = article.get('text', '')
            sentiment_analysis = analyze_sentiment_sync(text, sentiment_method, self.config.get_openai_api_key())
            
            # Create comprehensive analysis result
            comprehensive_analysis = {
                'article_metadata': risk_analysis['article_metadata'],
                'sentiment_analysis': sentiment_analysis,
                'risk_analysis': risk_analysis,
                'analysis_method': {
                    'sentiment': sentiment_method,
                    'risk': 'llm_advanced'
                },
                'risk_sentiment_correlation': self._analyze_risk_sentiment_correlation(
                    risk_analysis, sentiment_analysis
                )
            }
            
            analysis_results.append(comprehensive_analysis)
        
        return analysis_results
    
    def _analyze_risk_sentiment_correlation(self, risk_analysis: Dict, sentiment_analysis: Dict) -> Dict:
        """Analyze correlation between risk assessment and sentiment analysis"""
        risk_score = risk_analysis.get('overall_risk_score', 5.0)
        sentiment_score = sentiment_analysis.get('score', 0.0)
        
        # Normalize sentiment score to 0-10 scale for comparison
        normalized_sentiment = (sentiment_score + 1) * 5  # Convert from -1,1 to 0,10
        
        correlation_analysis = {
            'risk_score': risk_score,
            'sentiment_score': sentiment_score,
            'normalized_sentiment': normalized_sentiment,
            'correlation_type': self._determine_correlation_type(risk_score, normalized_sentiment),
            'alignment_score': self._calculate_alignment_score(risk_score, normalized_sentiment),
            'insights': self._generate_correlation_insights(risk_score, normalized_sentiment, sentiment_analysis)
        }
        
        return correlation_analysis
    
    def _determine_correlation_type(self, risk_score: float, sentiment_score: float) -> str:
        """Determine the type of correlation between risk and sentiment"""
        if abs(risk_score - sentiment_score) < 2:
            return "aligned"
        elif risk_score > sentiment_score + 2:
            return "risk_higher_than_sentiment"
        else:
            return "sentiment_higher_than_risk"
    
    def _calculate_alignment_score(self, risk_score: float, sentiment_score: float) -> float:
        """Calculate how well risk and sentiment scores align"""
        difference = abs(risk_score - sentiment_score)
        return max(0, 1 - (difference / 10))  # 1 = perfectly aligned, 0 = completely misaligned
    
    def _generate_correlation_insights(self, risk_score: float, sentiment_score: float, sentiment_analysis: Dict) -> List[str]:
        """Generate insights about the correlation between risk and sentiment"""
        insights = []
        
        if abs(risk_score - sentiment_score) < 2:
            insights.append("Risk assessment and sentiment analysis are well-aligned")
        elif risk_score > sentiment_score + 2:
            insights.append("Risk assessment indicates higher concerns than sentiment suggests")
            insights.append("Consider potential market risks not captured by sentiment")
        else:
            insights.append("Sentiment is more positive than risk assessment suggests")
            insights.append("Market sentiment may be overly optimistic")
        
        # Add sentiment-specific insights
        sentiment_category = sentiment_analysis.get('category', 'Neutral')
        if sentiment_category == 'Negative' and risk_score < 3:
            insights.append("Negative sentiment but low risk score - potential false alarm")
        elif sentiment_category == 'Positive' and risk_score > 7:
            insights.append("Positive sentiment but high risk score - underlying concerns exist")
        
        return insights
    
    async def analyze_and_store_advanced(self, articles: List[Dict], sentiment_method: str = 'llm') -> Dict[str, Any]:
        """
        Advanced analysis and storage with comprehensive risk assessment
        """
        try:
            # Perform advanced analysis
            analysis_results = await self.analyze_articles_with_advanced_risk(articles, sentiment_method)
            
            # Store in Pinecone if available
            storage_stats = {}
            storage_type = "local_only"
            
            if PINECONE_AVAILABLE:
                try:
                    # Use AnalysisPineconeDB for News Analysis (FORCED INSERTION into analysis-db)
                    self.logger.info(f"🔥 STARTING FORCED INSERTION into analysis-db for {len(articles)} articles")
                    analysis_pinecone_db = AnalysisPineconeDB()
                    self.logger.info("🔥 AnalysisPineconeDB initialized successfully")
                    
                    storage_stats = analysis_pinecone_db.store_articles_batch(articles, analysis_results)
                    storage_type = "analysis_pinecone"
                    self.logger.info(f"🔥 SUCCESSFULLY FORCED {storage_stats['success_count']} articles into analysis-db")
                    
                    if storage_stats['error_count'] > 0:
                        self.logger.warning(f"⚠️ {storage_stats['error_count']} articles failed to force into analysis-db")
                        
                except Exception as e:
                    self.logger.error(f"🔥 CRITICAL ERROR: Analysis-db storage failed: {e}")
                    # Try fallback to regular PineconeDB
                    try:
                        self.logger.info("🔄 Attempting fallback to sentiment-db...")
                        pinecone_db = PineconeDB()
                        storage_stats = pinecone_db.store_articles_batch(articles, analysis_results)
                        storage_type = "pinecone"
                        self.logger.info("Fallback to sentiment-db successful")
                    except Exception as fallback_error:
                        self.logger.error(f"❌ Fallback to sentiment-db also failed: {fallback_error}")
                        storage_type = "failed"
                        storage_stats = {'success_count': 0, 'error_count': len(articles), 'total_count': len(articles)}
            
            # Create comprehensive summary
            summary = {
                'analysis_summary': {
                    'total_articles': len(articles),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'sentiment_method': sentiment_method,
                    'risk_method': 'llm_advanced',
                    'storage_type': storage_type,
                    'storage_stats': storage_stats
                },
                'sentiment_summary': self._calculate_sentiment_summary(analysis_results),
                'risk_summary': self._calculate_advanced_risk_summary(analysis_results),
                'correlation_summary': self._calculate_correlation_summary(analysis_results),
                'source_summary': self._calculate_source_summary(articles, analysis_results),
                'individual_analyses': analysis_results
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in advanced analysis and storage: {e}")
            raise
    
    def _calculate_advanced_risk_summary(self, analysis_results: List[Dict]) -> Dict:
        """Calculate comprehensive risk summary from advanced analysis"""
        risk_scores = [result['risk_analysis']['overall_risk_score'] for result in analysis_results]
        confidence_scores = [result['risk_analysis']['risk_confidence'] for result in analysis_results]
        
        # Calculate risk category averages
        category_averages = {}
        for category in ['market_risk', 'economic_risk', 'geopolitical_risk', 'sector_risk', 
                        'company_risk', 'regulatory_risk', 'operational_risk', 'financial_risk']:
            scores = [result['risk_analysis']['risk_categories'][category]['score'] 
                     for result in analysis_results]
            category_averages[category] = sum(scores) / len(scores) if scores else 0
        
        return {
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'risk_distribution': {
                'low_risk': len([score for score in risk_scores if score < 3]),
                'medium_risk': len([score for score in risk_scores if 3 <= score <= 7]),
                'high_risk': len([score for score in risk_scores if score > 7])
            },
            'category_averages': category_averages,
            'top_risk_categories': sorted(category_averages.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def _calculate_correlation_summary(self, analysis_results: List[Dict]) -> Dict:
        """Calculate summary of risk-sentiment correlations"""
        alignment_scores = [result['risk_sentiment_correlation']['alignment_score'] 
                           for result in analysis_results]
        correlation_types = [result['risk_sentiment_correlation']['correlation_type'] 
                           for result in analysis_results]
        
        type_counts = Counter(correlation_types)
        
        return {
            'average_alignment_score': sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0,
            'correlation_distribution': dict(type_counts),
            'well_aligned_count': type_counts.get('aligned', 0),
            'risk_higher_count': type_counts.get('risk_higher_than_sentiment', 0),
            'sentiment_higher_count': type_counts.get('sentiment_higher_than_risk', 0)
        }
    
    def _calculate_sentiment_summary(self, analysis_results: List[Dict]) -> Dict:
        """Calculate sentiment summary across all articles"""
        sentiment_scores = [result['sentiment_analysis']['score'] for result in analysis_results]
        sentiment_categories = [result['sentiment_analysis']['category'] for result in analysis_results]
        
        category_counts = Counter(sentiment_categories)
        
        return {
            'average_sentiment_score': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            'sentiment_distribution': dict(category_counts),
            'positive_count': category_counts.get('Positive', 0),
            'negative_count': category_counts.get('Negative', 0),
            'neutral_count': category_counts.get('Neutral', 0)
        }
    
    def _calculate_source_summary(self, articles: List[Dict], analysis_results: List[Dict]) -> Dict:
        """Calculate source summary across all articles"""
        source_analysis = {}
        
        for article, analysis in zip(articles, analysis_results):
            source = analysis['risk_analysis']['article_metadata']['source']
            
            if source not in source_analysis:
                source_analysis[source] = {
                    'article_count': 0,
                    'avg_sentiment_score': 0,
                    'avg_risk_score': 0,
                    'avg_confidence': 0,
                    'total_sentiment_score': 0,
                    'total_risk_score': 0,
                    'total_confidence': 0
                }
            
            source_analysis[source]['article_count'] += 1
            source_analysis[source]['total_sentiment_score'] += analysis['sentiment_analysis']['score']
            source_analysis[source]['total_risk_score'] += analysis['risk_analysis']['overall_risk_score']
            source_analysis[source]['total_confidence'] += analysis['risk_analysis']['risk_confidence']
        
        # Calculate averages
        for source in source_analysis:
            count = source_analysis[source]['article_count']
            if count > 0:
                source_analysis[source]['avg_sentiment_score'] = (
                    source_analysis[source]['total_sentiment_score'] / count
                )
                source_analysis[source]['avg_risk_score'] = (
                    source_analysis[source]['total_risk_score'] / count
                )
                source_analysis[source]['avg_confidence'] = (
                    source_analysis[source]['total_confidence'] / count
                )
        
        return source_analysis
    
    def save_analysis(self, analysis: Dict, filename: str = None) -> str:
        """Save analysis results to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"advanced_risk_analysis_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved advanced risk analysis to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving analysis: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text using the configured sentiment method
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        return analyze_sentiment_sync(text, 'llm', self.config.get_openai_api_key())
    
    def analyze_risk(self, text: str) -> Dict:
        """
        Analyze risk of text using LLM-based analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with risk analysis results
        """
        # Create a mock article for analysis
        mock_article = {
            'title': 'Text Analysis',
            'text': text,
            'url': 'text-analysis'
        }
        
        # Use the fallback analysis for text-only input
        return self._fallback_risk_analysis(mock_article)

    # Legacy methods for backward compatibility
    def analyze_articles(self, articles: List[Dict]) -> Dict:
        """Legacy method - now uses advanced LLM analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.analyze_and_store_advanced(articles))
            return result
        finally:
            loop.close()
    
    def analyze_articles_with_sentiment(self, articles: List[Dict], sentiment_method: str = 'llm') -> List[Dict]:
        """Legacy method - now uses advanced LLM analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.analyze_articles_with_advanced_risk(articles, sentiment_method))
            return result
        finally:
            loop.close()
    
    def analyze_and_store_in_pinecone(self, articles: List[Dict], sentiment_method: str = 'llm', store_in_db: bool = True) -> Dict[str, Any]:
        """
        Analyze articles with optional database storage
        Args:
            articles: List of articles to analyze
            sentiment_method: Method for sentiment analysis ('llm' or 'lexicon')
            store_in_db: Whether to store results in database (default: True)
        """
        if store_in_db:
            # Use the advanced method that includes FORCED INSERTION into analysis-db
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.analyze_and_store_advanced(articles, sentiment_method))
                return result
            finally:
                loop.close()
        else:
            # Analyze without storing in database
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Perform analysis without storage
                analysis_results = loop.run_until_complete(self.analyze_articles_with_advanced_risk(articles, sentiment_method))
                
                # Create summary without storage stats
                summary = {
                    'analysis_summary': {
                        'total_articles': len(articles),
                        'analysis_timestamp': datetime.now().isoformat(),
                        'sentiment_method': sentiment_method,
                        'risk_method': 'llm_advanced',
                        'storage_type': 'analysis_only',
                        'storage_stats': {'success_count': 0, 'error_count': 0, 'total_count': len(articles)}
                    },
                    'sentiment_summary': self._calculate_sentiment_summary(analysis_results),
                    'risk_summary': self._calculate_advanced_risk_summary(analysis_results),
                    'correlation_summary': self._calculate_correlation_summary(analysis_results),
                    'source_summary': self._calculate_source_summary(articles, analysis_results),
                    'individual_analyses': analysis_results
                }
                
                return summary
            finally:
                loop.close()
