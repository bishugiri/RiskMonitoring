import re
import logging
from typing import List, Dict, Tuple
from collections import Counter
import json
from datetime import datetime

class RiskAnalyzer:
    """Analyzes news articles for potential risks and market sentiment"""
    
    def __init__(self):
        self.setup_logging()
        self.load_risk_keywords()
    
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    
    def load_risk_keywords(self):
        """Load risk-related keywords for analysis"""
        self.risk_keywords = {
            'market_risk': [
                'crash', 'bear market', 'recession', 'downturn', 'decline', 'fall', 'drop',
                'volatility', 'uncertainty', 'risk', 'danger', 'warning', 'concern',
                'sell-off', 'correction', 'bubble', 'burst', 'panic', 'fear'
            ],
            'economic_risk': [
                'inflation', 'deflation', 'stagflation', 'debt', 'default', 'bankruptcy',
                'liquidity', 'credit', 'interest rates', 'monetary policy', 'fiscal policy',
                'unemployment', 'layoffs', 'job losses', 'economic slowdown'
            ],
            'geopolitical_risk': [
                'war', 'conflict', 'sanctions', 'trade war', 'tariffs', 'embargo',
                'political instability', 'election', 'regulatory', 'policy change',
                'geopolitical', 'international relations', 'diplomatic'
            ],
            'sector_risk': [
                'tech bubble', 'real estate', 'housing market', 'oil prices', 'energy crisis',
                'supply chain', 'shortage', 'disruption', 'cybersecurity', 'data breach',
                'regulatory compliance', 'legal action', 'lawsuit'
            ],
            'positive_sentiment': [
                'rally', 'bull market', 'growth', 'profit', 'earnings', 'revenue',
                'expansion', 'investment', 'opportunity', 'recovery', 'bounce',
                'positive', 'optimistic', 'strong', 'robust', 'healthy'
            ]
        }
    
    def analyze_articles(self, articles: List[Dict]) -> Dict:
        """
        Analyze a list of articles for risks and sentiment
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Dictionary containing analysis results
        """
        self.logger.info(f"Analyzing {len(articles)} articles for risks")
        
        analysis = {
            'summary': {
                'total_articles': len(articles),
                'analysis_timestamp': datetime.now().isoformat(),
                'risk_score': 0,
                'sentiment_score': 0
            },
            'risk_categories': {},
            'top_risks': [],
            'article_analysis': [],
            'keyword_frequency': {},
            'source_analysis': {}
        }
        
        # Analyze each article
        for article in articles:
            article_analysis = self.analyze_single_article(article)
            analysis['article_analysis'].append(article_analysis)
        
        # Aggregate analysis
        analysis['risk_categories'] = self.aggregate_risk_categories(analysis['article_analysis'])
        analysis['top_risks'] = self.identify_top_risks(analysis['article_analysis'])
        analysis['keyword_frequency'] = self.calculate_keyword_frequency(analysis['article_analysis'])
        analysis['source_analysis'] = self.analyze_sources(articles, analysis['article_analysis'])
        
        # Calculate overall scores
        analysis['summary']['risk_score'] = self.calculate_overall_risk_score(analysis)
        analysis['summary']['sentiment_score'] = self.calculate_sentiment_score(analysis)
        
        return analysis
    
    def analyze_single_article(self, article: Dict) -> Dict:
        """
        Analyze a single article for risks and sentiment
        
        Args:
            article: Article dictionary
            
        Returns:
            Dictionary containing article analysis
        """
        text = article.get('text', '').lower()
        title = article.get('title', '').lower()
        
        # Combine title and text for analysis
        full_text = f"{title} {text}"
        
        analysis = {
            'url': article.get('url'),
            'title': article.get('title'),
            'source': self.extract_source(article.get('url', '')),
            'risk_categories': {},
            'risk_score': 0,
            'sentiment_score': 0,
            'keywords_found': [],
            'risk_indicators': []
        }
        
        # Check each risk category
        for category, keywords in self.risk_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword.lower() in full_text:
                    matches.append(keyword)
            
            if matches:
                analysis['risk_categories'][category] = {
                    'keywords_found': matches,
                    'count': len(matches),
                    'severity': self.calculate_category_severity(matches, len(full_text))
                }
                analysis['keywords_found'].extend(matches)
        
        # Calculate risk score for this article
        analysis['risk_score'] = self.calculate_article_risk_score(analysis['risk_categories'])
        analysis['sentiment_score'] = self.calculate_article_sentiment_score(analysis['risk_categories'])
        
        # Identify risk indicators
        analysis['risk_indicators'] = self.identify_risk_indicators(analysis['risk_categories'])
        
        return analysis
    
    def extract_source(self, url: str) -> str:
        """Extract source domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def calculate_category_severity(self, matches: List[str], text_length: int) -> float:
        """Calculate severity score for a risk category"""
        if text_length == 0:
            return 0
        
        # Normalize by text length and number of matches
        severity = (len(matches) * 10) / (text_length / 1000)  # per 1000 characters
        return min(severity, 10.0)  # Cap at 10
    
    def calculate_article_risk_score(self, risk_categories: Dict) -> float:
        """Calculate overall risk score for an article"""
        if not risk_categories:
            return 0
        
        total_score = 0
        weights = {
            'market_risk': 1.5,
            'economic_risk': 1.3,
            'geopolitical_risk': 1.2,
            'sector_risk': 1.0,
            'positive_sentiment': -0.5  # Negative weight for positive sentiment
        }
        
        for category, data in risk_categories.items():
            weight = weights.get(category, 1.0)
            total_score += data['severity'] * weight
        
        return min(total_score, 10.0)  # Cap at 10
    
    def calculate_article_sentiment_score(self, risk_categories: Dict) -> float:
        """Calculate sentiment score for an article (-10 to 10)"""
        positive_score = risk_categories.get('positive_sentiment', {}).get('severity', 0)
        negative_score = sum(
            data['severity'] for category, data in risk_categories.items()
            if category != 'positive_sentiment'
        )
        
        return positive_score - negative_score
    
    def identify_risk_indicators(self, risk_categories: Dict) -> List[str]:
        """Identify key risk indicators from the article"""
        indicators = []
        
        for category, data in risk_categories.items():
            if category != 'positive_sentiment' and data['count'] > 0:
                indicators.append(f"{category}: {', '.join(data['keywords_found'][:3])}")
        
        return indicators
    
    def aggregate_risk_categories(self, article_analyses: List[Dict]) -> Dict:
        """Aggregate risk categories across all articles"""
        aggregated = {}
        
        for analysis in article_analyses:
            for category, data in analysis['risk_categories'].items():
                if category not in aggregated:
                    aggregated[category] = {
                        'total_articles': 0,
                        'total_keywords': 0,
                        'avg_severity': 0,
                        'keywords_found': Counter()
                    }
                
                aggregated[category]['total_articles'] += 1
                aggregated[category]['total_keywords'] += data['count']
                aggregated[category]['avg_severity'] += data['severity']
                aggregated[category]['keywords_found'].update(data['keywords_found'])
        
        # Calculate averages
        for category in aggregated:
            if aggregated[category]['total_articles'] > 0:
                aggregated[category]['avg_severity'] /= aggregated[category]['total_articles']
        
        return aggregated
    
    def identify_top_risks(self, article_analyses: List[Dict]) -> List[Dict]:
        """Identify the top risks across all articles"""
        risk_scores = []
        
        for analysis in article_analyses:
            if analysis['risk_score'] > 0:
                risk_scores.append({
                    'title': analysis['title'],
                    'url': analysis['url'],
                    'source': analysis['source'],
                    'risk_score': analysis['risk_score'],
                    'risk_indicators': analysis['risk_indicators']
                })
        
        # Sort by risk score (highest first)
        risk_scores.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return risk_scores[:10]  # Top 10 risks
    
    def calculate_keyword_frequency(self, article_analyses: List[Dict]) -> Dict:
        """Calculate frequency of risk keywords across all articles"""
        keyword_counter = Counter()
        
        for analysis in article_analyses:
            keyword_counter.update(analysis['keywords_found'])
        
        return dict(keyword_counter.most_common(20))
    
    def analyze_sources(self, articles: List[Dict], article_analyses: List[Dict]) -> Dict:
        """Analyze risks by news source"""
        source_analysis = {}
        
        for article, analysis in zip(articles, article_analyses):
            source = analysis['source']
            
            if source not in source_analysis:
                source_analysis[source] = {
                    'article_count': 0,
                    'avg_risk_score': 0,
                    'total_risk_score': 0,
                    'articles': []
                }
            
            source_analysis[source]['article_count'] += 1
            source_analysis[source]['total_risk_score'] += analysis['risk_score']
            source_analysis[source]['articles'].append({
                'title': article.get('title'),
                'url': article.get('url'),
                'risk_score': analysis['risk_score']
            })
        
        # Calculate averages
        for source in source_analysis:
            count = source_analysis[source]['article_count']
            if count > 0:
                source_analysis[source]['avg_risk_score'] = (
                    source_analysis[source]['total_risk_score'] / count
                )
        
        return source_analysis
    
    def calculate_overall_risk_score(self, analysis: Dict) -> float:
        """Calculate overall risk score for all articles"""
        if not analysis['article_analysis']:
            return 0
        
        total_score = sum(article['risk_score'] for article in analysis['article_analysis'])
        return total_score / len(analysis['article_analysis'])
    
    def calculate_sentiment_score(self, analysis: Dict) -> float:
        """Calculate overall sentiment score for all articles"""
        if not analysis['article_analysis']:
            return 0
        
        total_score = sum(article['sentiment_score'] for article in analysis['article_analysis'])
        return total_score / len(analysis['article_analysis'])
    
    def save_analysis(self, analysis: Dict, filename: str = None) -> str:
        """Save analysis results to a file"""
        from config import Config
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_analysis_{timestamp}.json"
        
        filepath = f"{Config.OUTPUT_DIR}/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved risk analysis to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving analysis: {e}")
            raise 