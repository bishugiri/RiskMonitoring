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

# Event type categories for structured analysis
EVENT_TYPES = [
    "regulatory", "legal", "product_launch", "product_closure", "performance", 
    "inflows_outflows", "ratings", "operations", "donations", "other"
]

async def analyze_sentiment_lexicon(text: str) -> Dict:
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
        import httpx
        client = OpenAI(api_key=openai_api_key, http_client=httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        ))
        
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

async def analyze_sentiment_structured(text: str, title: str = "", openai_api_key: str = None) -> Dict:
    """
    Enhanced structured sentiment analysis following the reputation risk tracking approach
    Returns comprehensive analysis with entity identification, event classification, and detailed reasoning
    """
    if not text:
        return {
            'entity': 'Unknown',
            'headline': title or 'No title provided',
            'event_type': 'other',
            'sentiment_score': 0,
            'reasoning': 'No text provided for analysis',
            'confidence': 0.0,
            'key_quotes': [],
            'summary': 'No content to analyze'
        }
    
    if not openai_api_key:
        # Fallback to lexicon-based analysis
        return analyze_sentiment_lexicon_structured(text, title)
    
    try:
        from openai import OpenAI
        import httpx
        
        client = OpenAI(api_key=openai_api_key, http_client=httpx.Client(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        ))
        
        system_prompt = """You are an intelligent agent that helps track reputation risk for financial entities and provides relevant sentiment scores based on news articles.

ANALYSIS STEPS:
1. Identify the main financial entity mentioned (company, fund, institution)
2. Summarize the key event in 1-2 sentences (what happened and why it matters)
3. Determine the event type from: regulatory, legal, product_launch, product_closure, performance, inflows_outflows, ratings, operations, donations, other
4. Extract 1-3 direct evidence quotes or numbers from the article
5. Assign a sentiment score from -1 to +1 based on tone and materiality
6. Provide detailed reasoning explaining why the score was chosen, balancing positives/negatives

SENTIMENT SCALE:
- -1: Severe negative - legal/ethical crises, large fines, flagship fund closure
- -0.8 to -0.6: Significant negative - major losses, regulatory issues, significant downgrades
- -0.5 to -0.2: Moderate negative - minor setbacks, underperformance, small fines
- -0.1 to 0.1: Neutral - mixed news, no clear impact, routine announcements
- 0.2 to 0.5: Moderate positive - good performance, minor upgrades, positive developments
- 0.6 to 0.8: Significant positive - strong performance, major upgrades, successful launches
- 1: Exceptional positive - transformational deals, record inflows, major upgrades, significant donations

OUTPUT FORMAT (JSON):
{
  "entity": "string - main financial entity mentioned",
  "headline": "string - article headline",
  "event_type": "string - one of the predefined event types",
  "sentiment_score": "number between -1 and 1",
  "reasoning": "string - detailed explanation of why this score was chosen, referencing specific text",
  "confidence": "number between 0 and 1",
  "key_quotes": ["quote1", "quote2", "quote3"],
  "summary": "string - 1-2 sentence summary of the key event"
}

Focus on:
- Financial impact and materiality
- Reputation and brand implications
- Market reaction potential
- Regulatory and legal implications
- Operational and strategic significance"""

        user_prompt = f"""Please analyze the following financial news article:

HEADLINE: {title}
CONTENT: {text[:3000]}

Provide a comprehensive structured analysis following the specified format and methodology."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.2,
        )
        
        response_text = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            # Validate and normalize the result
            return _validate_structured_result(result, title)
        else:
            # Fallback to lexicon-based analysis
            return analyze_sentiment_lexicon_structured(text, title)
            
    except Exception as e:
        # Fallback to lexicon-based analysis
        return analyze_sentiment_lexicon_structured(text, title)

def analyze_sentiment_lexicon_structured(text: str, title: str = "") -> Dict:
    """
    Lexicon-based structured sentiment analysis as fallback
    """
    if not text:
        return {
            'entity': 'Unknown',
            'headline': title or 'No title provided',
            'event_type': 'other',
            'sentiment_score': 0,
            'reasoning': 'No text provided for analysis',
            'confidence': 0.0,
            'key_quotes': [],
            'summary': 'No content to analyze'
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
            'entity': 'Unknown',
            'headline': title or 'No title provided',
            'event_type': 'other',
            'sentiment_score': 0,
            'reasoning': 'No financial sentiment indicators found in text',
            'confidence': 0.0,
            'key_quotes': [],
            'summary': 'No significant financial events detected'
        }
    
    # Calculate sentiment score: (Positive - Negative) / Total
    score = (positive_count - negative_count) / total_relevant
    
    # Convert to -1 to 1 scale
    sentiment_score = max(-1, min(1, score * 2))  # Scale from [-0.5, 0.5] to [-1, 1]
    
    # Determine event type based on keywords
    event_type = _classify_event_type(text_lower)
    
    # Generate reasoning
    reasoning = f"Found {positive_count} positive and {negative_count} negative financial indicators. "
    if positive_count > negative_count:
        reasoning += "Overall positive sentiment due to favorable financial indicators."
    elif negative_count > positive_count:
        reasoning += "Overall negative sentiment due to concerning financial indicators."
    else:
        reasoning += "Mixed sentiment with balanced positive and negative indicators."
    
    # Calculate confidence
    confidence = min(1.0, total_relevant / 15)
    
    return {
        'entity': _extract_entity(text, title),
        'headline': title or 'No title provided',
        'event_type': event_type,
        'sentiment_score': round(sentiment_score, 2),
        'reasoning': reasoning,
        'confidence': round(confidence, 2),
        'key_quotes': _extract_key_quotes(text),
        'summary': _generate_summary(text, sentiment_score)
    }

def _validate_structured_result(result: Dict, title: str) -> Dict:
    """Validate and normalize structured analysis result"""
    try:
        # Ensure all required fields exist with defaults
        validated = {
            'entity': result.get('entity', 'Unknown'),
            'headline': result.get('headline', title or 'No title provided'),
            'event_type': result.get('event_type', 'other'),
            'sentiment_score': float(result.get('sentiment_score', 0)),
            'reasoning': result.get('reasoning', 'No reasoning provided'),
            'confidence': float(result.get('confidence', 0.5)),
            'key_quotes': result.get('key_quotes', []),
            'summary': result.get('summary', 'No summary provided')
        }
        
        # Clamp sentiment score to valid range
        validated['sentiment_score'] = max(-1, min(1, validated['sentiment_score']))
        validated['confidence'] = max(0, min(1, validated['confidence']))
        
        # Ensure event_type is valid
        if validated['event_type'] not in EVENT_TYPES:
            validated['event_type'] = 'other'
        
        # Round scores for consistency
        validated['sentiment_score'] = round(validated['sentiment_score'], 2)
        validated['confidence'] = round(validated['confidence'], 2)
        
        return validated
        
    except Exception as e:
        # Return safe fallback
        return {
            'entity': 'Unknown',
            'headline': title or 'No title provided',
            'event_type': 'other',
            'sentiment_score': 0,
            'reasoning': f'Error in analysis: {str(e)}',
            'confidence': 0.0,
            'key_quotes': [],
            'summary': 'Analysis failed'
        }

def _classify_event_type(text: str) -> str:
    """Classify event type based on keywords in text"""
    text_lower = text.lower()
    
    # Regulatory events
    if any(word in text_lower for word in ['regulatory', 'regulation', 'compliance', 'fcc', 'sec', 'federal']):
        return 'regulatory'
    
    # Legal events
    if any(word in text_lower for word in ['legal', 'lawsuit', 'litigation', 'court', 'judge', 'settlement', 'fine']):
        return 'legal'
    
    # Product launch
    if any(word in text_lower for word in ['launch', 'introduce', 'new product', 'announce', 'release']):
        return 'product_launch'
    
    # Product closure
    if any(word in text_lower for word in ['close', 'closure', 'discontinue', 'shutdown', 'terminate', 'fund closure']):
        return 'product_closure'
    
    # Performance
    if any(word in text_lower for word in ['performance', 'earnings', 'profit', 'loss', 'revenue', 'quarterly']):
        return 'performance'
    
    # Inflows/outflows
    if any(word in text_lower for word in ['inflow', 'outflow', 'investment', 'fund', 'assets under management']):
        return 'inflows_outflows'
    
    # Ratings
    if any(word in text_lower for word in ['rating', 'upgrade', 'downgrade', 'credit', 'moody', 's&p']):
        return 'ratings'
    
    # Operations
    if any(word in text_lower for word in ['operation', 'operational', 'management', 'strategy', 'restructure', 'strategic restructuring']):
        return 'operations'
    
    # Donations
    if any(word in text_lower for word in ['donation', 'charity', 'philanthropy', 'gift', 'contribution']):
        return 'donations'
    
    return 'other'

def _extract_entity(text: str, title: str) -> str:
    """Extract main financial entity from text"""
    # Common financial entities to look for
    entities = [
        'Goldman Sachs', 'Blackstone', 'BlackRock', 'Vanguard', 'Fidelity',
        'Morgan Stanley', 'JPMorgan', 'Bank of America', 'Wells Fargo',
        'Citigroup', 'Credit Suisse', 'UBS', 'Deutsche Bank', 'Barclays',
        'State Street', 'PIMCO', 'T. Rowe Price', 'Franklin Templeton',
        'Invesco', 'Schwab', 'Ameriprise', 'Raymond James'
    ]
    
    # Check title first, then text
    search_text = f"{title} {text}"
    search_text_lower = search_text.lower()
    
    for entity in entities:
        if entity.lower() in search_text_lower:
            return entity
    
    # Try to extract from common patterns
    import re
    patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Asset Management|Investment|Capital|Group|Corp|Inc|LLC)',
        r'(?:from|at|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, search_text)
        if match:
            return match.group(1)
    
    return 'Unknown'

def _extract_key_quotes(text: str) -> List[str]:
    """Extract key quotes or numbers from text"""
    quotes = []
    
    # Look for quoted text
    import re
    quote_pattern = r'"([^"]+)"'
    quotes.extend(re.findall(quote_pattern, text))
    
    # Look for numbers with context
    number_pattern = r'(\$[\d,]+(?:\.\d+)?\s+(?:million|billion|trillion)?)'
    numbers = re.findall(number_pattern, text)
    quotes.extend(numbers[:2])  # Limit to 2 numbers
    
    # Look for percentage changes
    percent_pattern = r'([+-]?\d+(?:\.\d+)?%\s+(?:increase|decrease|growth|decline))'
    percents = re.findall(percent_pattern, text)
    quotes.extend(percents[:1])  # Limit to 1 percentage
    
    return quotes[:3]  # Return max 3 quotes

def _generate_summary(text: str, sentiment_score: float) -> str:
    """Generate a brief summary of the key event"""
    if sentiment_score > 0.3:
        return "Positive development with favorable implications for the entity."
    elif sentiment_score < -0.3:
        return "Negative development with concerning implications for the entity."
    else:
        return "Mixed or neutral development with unclear impact on the entity."

def analyze_sentiment_sync(text: str, method: str = 'llm', openai_api_key: str = None) -> Dict:
    """
    Synchronous wrapper for sentiment analysis with enhanced error handling
    """
    if method == 'lexicon':
        return analyze_sentiment_lexicon(text)
    elif method == 'llm' and openai_api_key:
        import asyncio
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, analyze_sentiment_llm(text, openai_api_key))
                    return future.result()
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(analyze_sentiment_llm(text, openai_api_key))
                    return result
                finally:
                    loop.close()
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
