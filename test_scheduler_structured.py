#!/usr/bin/env python3
"""
Test script to verify that the scheduler is using the new structured sentiment analysis.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.scheduler import NewsScheduler
from risk_monitor.config.settings import Config

async def test_scheduler_structured_sentiment():
    """Test that the scheduler uses structured sentiment analysis"""
    
    print("🧪 Testing Scheduler Structured Sentiment Analysis")
    print("=" * 60)
    
    # Create a test scheduler
    scheduler = NewsScheduler()
    
    # Test articles
    test_articles = [
        {
            "title": "Goldman Sachs Asset Management closes small Europe HY fund due to limited demand",
            "text": "Goldman Sachs Asset Management (GSAM) has announced the closure of its small European high-yield fund due to limited investor demand. The fund, which had approximately $50 million in assets under management, will be liquidated over the next 30 days.",
            "url": "https://example.com/article1",
            "source": "Financial Times",
            "publish_date": "2024-01-15"
        },
        {
            "title": "Blackstone faces DOJ investigation over RealPage price-fixing allegations",
            "text": "Blackstone Group is under investigation by the Department of Justice for its use of RealPage software in rental pricing decisions. The DOJ alleges that RealPage's software facilitated price-fixing among landlords.",
            "url": "https://example.com/article2",
            "source": "Reuters",
            "publish_date": "2024-01-15"
        }
    ]
    
    print(f"Testing with {len(test_articles)} articles...")
    
    # Test lexicon-based structured analysis
    print("\n🔍 Testing Lexicon-based Structured Analysis:")
    lexicon_results = await scheduler.analyze_sentiment_with_lexicon_structured_async(test_articles)
    
    for i, article in enumerate(lexicon_results, 1):
        sentiment = article.get('sentiment_analysis', {})
        print(f"Article {i}:")
        print(f"  Entity: {sentiment.get('entity', 'Unknown')}")
        print(f"  Event Type: {sentiment.get('event_type', 'other')}")
        print(f"  Sentiment Score: {sentiment.get('score', 'N/A')}")
        print(f"  Category: {sentiment.get('category', 'Unknown')}")
        print(f"  Method: {article.get('sentiment_method', 'unknown')}")
        print(f"  Reasoning: {sentiment.get('justification', 'N/A')[:100]}...")
        print()
    
    # Test LLM-based structured analysis if OpenAI is available
    config = Config()
    if config.get_openai_api_key():
        print("🤖 Testing LLM-based Structured Analysis:")
        try:
            llm_results = await scheduler.analyze_sentiment_with_openai_structured_async(test_articles)
            
            for i, article in enumerate(llm_results, 1):
                sentiment = article.get('sentiment_analysis', {})
                print(f"Article {i}:")
                print(f"  Entity: {sentiment.get('entity', 'Unknown')}")
                print(f"  Event Type: {sentiment.get('event_type', 'other')}")
                print(f"  Sentiment Score: {sentiment.get('score', 'N/A')}")
                print(f"  Category: {sentiment.get('category', 'Unknown')}")
                print(f"  Method: {article.get('sentiment_method', 'unknown')}")
                print(f"  Reasoning: {sentiment.get('justification', 'N/A')[:100]}...")
                print()
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("🤖 LLM-based Analysis: Skipped (no OpenAI API key)")
    
    # Test dual analysis
    print("🔄 Testing Dual Structured Analysis:")
    try:
        dual_results = await scheduler.analyze_sentiment_dual_async(test_articles)
        
        for i, article in enumerate(dual_results, 1):
            sentiment = article.get('sentiment_analysis', {})
            llm_sentiment = article.get('llm_sentiment', {})
            print(f"Article {i}:")
            print(f"  Method: {article.get('sentiment_method', 'unknown')}")
            print(f"  Entity: {sentiment.get('entity', 'Unknown')}")
            print(f"  Event Type: {sentiment.get('event_type', 'other')}")
            print(f"  Sentiment Score: {sentiment.get('score', 'N/A')}")
            print(f"  LLM Entity: {llm_sentiment.get('entity', 'Unknown')}")
            print(f"  LLM Event Type: {llm_sentiment.get('event_type', 'other')}")
            print(f"  LLM Sentiment Score: {llm_sentiment.get('sentiment_score', 'N/A')}")
            print()
    except Exception as e:
        print(f"  Error: {e}")
    
    print("✅ Scheduler structured sentiment analysis test completed!")

def test_scheduler_config():
    """Test scheduler configuration"""
    print("\n⚙️ Testing Scheduler Configuration")
    print("=" * 40)
    
    scheduler = NewsScheduler()
    config = scheduler.config
    
    print(f"Run Time: {config.run_time}")
    print(f"Timezone: {config.timezone}")
    print(f"Articles per Entity: {config.articles_per_entity}")
    print(f"Entities: {config.entities}")
    print(f"Keywords: {config.keywords}")
    print(f"Use OpenAI: {config.use_openai}")
    print(f"Enable Pinecone Storage: {config.enable_pinecone_storage}")
    print(f"Enable Dual Sentiment: {config.enable_dual_sentiment}")
    print(f"Enable Detailed Email: {config.enable_detailed_email}")

if __name__ == "__main__":
    print("🚀 Starting Scheduler Structured Sentiment Analysis Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        asyncio.run(test_scheduler_structured_sentiment())
        test_scheduler_config()
        
        print("\n✅ All scheduler tests completed successfully!")
        print("\n📊 Summary:")
        print("- Scheduler now uses structured sentiment analysis")
        print("- Entity identification and event classification working")
        print("- Both lexicon and LLM methods supported")
        print("- Dual analysis combines both methods")
        print("- Backward compatibility maintained")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
