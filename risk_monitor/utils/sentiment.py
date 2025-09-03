"""
Sentiment analysis utilities for the Risk Monitor application.
Enhanced for advanced financial risk analysis.
"""

from typing import Dict, List
import re
import json

# Enhanced Financial Sentiment Analysis Configuration
FINANCE_POSITIVE_WORDS = [
    "profit", "growth", "revenue", "earnings", "surge", "rally", "bullish", "optimistic",
    "strong", "robust", "healthy", "expansion", "investment", "opportunity", "recovery",
    "bounce", "positive", "gain", "increase", "rise", "climb", "soar", "jump", "leap",
    "success", "achievement", "breakthrough", "innovation", "leadership", "excellence",
    "outperform", "beat", "exceed", "outpace", "accelerate", "boost", "enhance", "improve",
    "strengthen", "solidify", "stabilize", "secure", "confident", "assured", "promising",
    "bright", "upward", "ascending", "prosperous", "thriving", "flourishing", "booming",
    "dividend", "buyback", "acquisition", "merger", "partnership", "alliance", "synergy",
    "efficiency", "optimization", "streamline", "restructure", "turnaround", "resilient",
    "sustainable", "scalable", "profitable", "lucrative", "valuable", "premium", "premium"
]

FINANCE_NEGATIVE_WORDS = [
    "loss", "decline", "drop", "fall", "crash", "bearish", "pessimistic", "weak",
    "poor", "unhealthy", "contraction", "recession", "downturn", "slump", "plunge",
    "negative", "decrease", "reduce", "diminish", "shrink", "contract", "deteriorate",
    "worsen", "fail", "bankruptcy", "default", "crisis", "panic", "fear", "anxiety",
    "uncertainty", "volatility", "risk", "danger", "threat", "concern", "worry",
    "stress", "pressure", "strain", "burden", "liability", "debt", "losses", "deficit",
    "shortfall", "gap", "hole", "weakness", "vulnerability", "exposure", "susceptible",
    "fragile", "unstable", "unreliable", "unpredictable", "chaotic", "turbulent",
    "layoff", "restructuring", "downsizing", "closure", "shutdown", "discontinuation",
    "write-down", "impairment", "dilution", "downgrade", "downturn", "bear market",
    "correction", "bubble", "burst", "meltdown", "collapse", "implosion", "freefall"
]

def analyze_sentiment_lexicon(text: str) -> Dict:
    """
    Analyze sentiment using enhanced lexicon-based approach
    Returns: {'score': float, 'category': str, 'positive_count': int, 'negative_count': int, 'confidence': float}
    """
    if not text:
        return {
            'score': 0.0, 
            'category': 'Neutral', 
            'positive_count': 0, 
            'negative_count': 0,
            'confidence': 0.0,
            'justification': 'No text provided for analysis'
        }
    
    # Convert to lowercase for matching
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count positive and negative words
    positive_count = sum(1 for word in FINANCE_POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in FINANCE_NEGATIVE_WORDS if word in text_lower)
    
    # Calculate total relevant words
    total_relevant = positive_count + negative_count
    
    if total_relevant == 0:
        return {
            'score': 0.0, 
            'category': 'Neutral', 
            'positive_count': 0, 
            'negative_count': 0,
            'confidence': 0.0,
            'justification': 'No financial sentiment indicators found in text'
        }
    
    # Calculate sentiment score: (Positive - Negative) / Total
    score = (positive_count - negative_count) / total_relevant
    
    # Calculate confidence based on number of indicators
    confidence = min(1.0, total_relevant / 20)  # Higher confidence with more indicators
    
    # Categorize sentiment
    if score > 0.1:
        category = 'Positive'
    elif score < -0.1:
        category = 'Negative'
    else:
        category = 'Neutral'
    
    # Generate justification
    justification = f"Found {positive_count} positive and {negative_count} negative financial indicators"
    
    return {
        'score': round(score, 3),
        'category': category,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'total_relevant': total_relevant,
        'confidence': round(confidence, 3),
        'justification': justification
    }

async def analyze_sentiment_llm(text: str, openai_api_key: str) -> Dict:
    """
    Analyze sentiment using OpenAI GPT-4o with enhanced financial context
    Returns: {'score': float, 'category': str, 'justification': str, 'confidence': float}
    """
    from openai import OpenAI
    
    if not text:
        return {
            'score': 0.0, 
            'category': 'Neutral', 
            'justification': 'No text provided',
            'confidence': 0.0
        }
    
    try:
        client = OpenAI(api_key=openai_api_key)
        
        system_prompt = """You are an expert financial sentiment analyst specializing in market sentiment analysis, investor psychology, and financial news interpretation. Your role is to analyze financial news articles and provide nuanced sentiment assessments.

ANALYSIS FRAMEWORK:
1. **Market Sentiment**: Evaluate overall market mood and investor sentiment
2. **Financial Performance**: Assess earnings, revenue, and financial health indicators
3. **Strategic Positioning**: Consider company strategy, competitive position, and future outlook
4. **Risk Perception**: Evaluate how the news affects risk perception and market volatility
5. **Investor Confidence**: Assess impact on investor confidence and market participation

SENTIMENT SCORING METHODOLOGY:
- **Score Range**: -1.0 to 1.0 (-1.0 = Extremely Negative, 0 = Neutral, 1.0 = Extremely Positive)
- **Confidence Level**: 0.0 to 1.0 (0 = Low Confidence, 1 = High Confidence)
- **Categories**: Positive (>0.1), Neutral (-0.1 to 0.1), Negative (<-0.1)

Provide your analysis in the following JSON format:
{
  "score": <numerical score between -1.0 and 1.0>,
  "confidence": <confidence level between 0.0 and 1.0>,
  "justification": "<detailed explanation of your sentiment analysis>",
  "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
  "market_impact": "<assessment of potential market impact>"
}

Focus on financial and market sentiment. Consider:
- Market reaction potential
- Investor sentiment indicators
- Financial performance implications
- Strategic positioning impact
- Risk perception changes
- Overall market outlook"""

        user_prompt = f"""Please analyze the sentiment of the following financial news article:

ARTICLE TEXT:
{text[:3000]}

Provide a comprehensive sentiment analysis that considers:
- Market sentiment and investor psychology
- Financial performance implications
- Strategic positioning and competitive dynamics
- Risk perception and market volatility
- Overall market outlook and confidence

Consider both immediate and longer-term sentiment implications."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.2,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            llm_result = json.loads(json_str)
            score = float(llm_result['score'])
            confidence = float(llm_result.get('confidence', 0.8))
            justification = llm_result['justification']
            
            # Categorize sentiment
            if score > 0.1:
                category = 'Positive'
            elif score < -0.1:
                category = 'Negative'
            else:
                category = 'Neutral'
                
            return {
                'score': round(score, 3),
                'category': category,
                'confidence': round(confidence, 3),
                'justification': justification,
                'key_factors': llm_result.get('key_factors', []),
                'market_impact': llm_result.get('market_impact', 'Not specified')
            }
        else:
            # Fallback to lexicon-based analysis
            return analyze_sentiment_lexicon(text)
            
    except Exception as e:
        # Fallback to lexicon-based analysis
        return analyze_sentiment_lexicon(text)

def analyze_sentiment_sync(text: str, method: str = 'llm', openai_api_key: str = None) -> Dict:
    """
    Synchronous wrapper for sentiment analysis with enhanced error handling
    """
    if method == 'lexicon':
        return analyze_sentiment_lexicon(text)
    elif method == 'llm' and openai_api_key:
        import asyncio
        try:
            # Run the async function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(analyze_sentiment_llm(text, openai_api_key))
            loop.close()
            return result
        except Exception as e:
            # Fallback to lexicon-based analysis with error logging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM sentiment analysis failed, falling back to lexicon: {e}")
            return analyze_sentiment_lexicon(text)
    else:
        return analyze_sentiment_lexicon(text)

def analyze_sentiment_with_context(text: str, context: Dict = None, method: str = 'llm', openai_api_key: str = None) -> Dict:
    """
    Enhanced sentiment analysis with additional context
    Context can include: company, sector, market conditions, etc.
    """
    if not context:
        return analyze_sentiment_sync(text, method, openai_api_key)
    
    # For now, use the standard analysis but could be enhanced with context-aware prompts
    base_analysis = analyze_sentiment_sync(text, method, openai_api_key)
    
    # Add context information to the analysis
    base_analysis['context'] = context
    base_analysis['context_aware'] = True
    
    return base_analysis
