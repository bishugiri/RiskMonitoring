"""
Sentiment analysis utilities for the Risk Monitor application.
"""

from typing import Dict, List

# Sentiment Analysis Configuration
FINANCE_POSITIVE_WORDS = [
    "profit", "growth", "revenue", "earnings", "surge", "rally", "bullish", "optimistic",
    "strong", "robust", "healthy", "expansion", "investment", "opportunity", "recovery",
    "bounce", "positive", "gain", "increase", "rise", "climb", "soar", "jump", "leap",
    "success", "achievement", "breakthrough", "innovation", "leadership", "excellence",
    "outperform", "beat", "exceed", "outpace", "accelerate", "boost", "enhance", "improve",
    "strengthen", "solidify", "stabilize", "secure", "confident", "assured", "promising",
    "bright", "upward", "ascending", "prosperous", "thriving", "flourishing", "booming"
]

FINANCE_NEGATIVE_WORDS = [
    "loss", "decline", "drop", "fall", "crash", "bearish", "pessimistic", "weak",
    "poor", "unhealthy", "contraction", "recession", "downturn", "slump", "plunge",
    "negative", "decrease", "reduce", "diminish", "shrink", "contract", "deteriorate",
    "worsen", "fail", "bankruptcy", "default", "crisis", "panic", "fear", "anxiety",
    "uncertainty", "volatility", "risk", "danger", "threat", "concern", "worry",
    "stress", "pressure", "strain", "burden", "liability", "debt", "losses", "deficit",
    "shortfall", "gap", "hole", "weakness", "vulnerability", "exposure", "susceptible",
    "fragile", "unstable", "unreliable", "unpredictable", "chaotic", "turbulent"
]

def analyze_sentiment_lexicon(text: str) -> Dict:
    """
    Analyze sentiment using lexicon-based approach
    Returns: {'score': float, 'category': str, 'positive_count': int, 'negative_count': int}
    """
    if not text:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    
    # Convert to lowercase for matching
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count positive and negative words
    positive_count = sum(1 for word in FINANCE_POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in FINANCE_NEGATIVE_WORDS if word in text_lower)
    
    # Calculate total relevant words
    total_relevant = positive_count + negative_count
    
    if total_relevant == 0:
        return {'score': 0.0, 'category': 'Neutral', 'positive_count': 0, 'negative_count': 0}
    
    # Calculate sentiment score: (Positive - Negative) / Total
    score = (positive_count - negative_count) / total_relevant
    
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
        'positive_count': positive_count,
        'negative_count': negative_count,
        'total_relevant': total_relevant
    }

async def analyze_sentiment_llm(text: str, openai_api_key: str) -> Dict:
    """
    Analyze sentiment using OpenAI GPT-4o
    Returns: {'score': float, 'category': str, 'justification': str}
    """
    import openai
    import re
    import json
    
    if not text:
        return {'score': 0.0, 'category': 'Neutral', 'justification': 'No text provided'}
    
    try:
        openai.api_key = openai_api_key
        prompt = f"""
        You are a financial news sentiment analysis assistant. Analyze the sentiment of the following financial news article text. 
        Provide your analysis in JSON format with the following structure:
        {{
          "score": <numerical score between -1.0 and 1.0>,
          "justification": "<brief explanation of your sentiment analysis>"
        }}

        Article text:
        {text[:2000]}

        Focus on financial and market sentiment. Consider factors like:
        - Market impact and investor sentiment
        - Financial performance indicators
        - Risk and opportunity assessment
        - Overall market outlook
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            llm_result = json.loads(json_str)
            score = float(llm_result['score'])
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
                'justification': justification
            }
        else:
            # Fallback to lexicon-based analysis
            return analyze_sentiment_lexicon(text)
            
    except Exception as e:
        # Fallback to lexicon-based analysis
        return analyze_sentiment_lexicon(text)

def analyze_sentiment_sync(text: str, method: str = 'lexicon', openai_api_key: str = None) -> Dict:
    """
    Synchronous wrapper for sentiment analysis
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
        except Exception:
            # Fallback to lexicon-based analysis
            return analyze_sentiment_lexicon(text)
    else:
        return analyze_sentiment_lexicon(text)
