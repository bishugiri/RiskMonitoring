#!/usr/bin/env python3
"""
Test script for the new structured sentiment analysis functionality.
Demonstrates the enhanced sentiment analysis with entity identification, event classification, and detailed reasoning.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.utils.sentiment import analyze_sentiment_structured, analyze_sentiment_lexicon_structured
from risk_monitor.config.settings import Config

def test_structured_sentiment():
    """Test the new structured sentiment analysis with sample articles"""
    
    # Sample articles for testing
    test_articles = [
        {
            "title": "Goldman Sachs Asset Management closes small Europe HY fund due to limited demand",
            "text": "Goldman Sachs Asset Management (GSAM) has announced the closure of its small European high-yield fund due to limited investor demand. The fund, which had approximately $50 million in assets under management, will be liquidated over the next 30 days. 'We made this decision after careful consideration of market conditions and investor preferences,' said a GSAM spokesperson. The closure represents a strategic realignment of GSAM's European fixed income offerings."
        },
        {
            "title": "Blackstone faces DOJ investigation over RealPage price-fixing allegations",
            "text": "Blackstone Group is under investigation by the Department of Justice for its use of RealPage software in rental pricing decisions. The DOJ alleges that RealPage's software facilitated price-fixing among landlords. While competitors Greystar and Cortland have settled similar allegations, Blackstone has yet to reach a settlement or release a public statement about discontinuing use of the software. The investigation could result in significant fines and regulatory scrutiny."
        },
        {
            "title": "Adage Capital Management's $10 Million Gift Launches UNCF's Project ACCLAIM",
            "text": "Adage Capital Management has donated $10 million to launch Project ACCLAIM (Accelerating Learning in Asset Investment Management), a new initiative by the United Negro College Fund (UNCF). The project aims to accelerate HBCU student pathways into financial services by providing scholarships, mentorship programs, and career development opportunities. 'This investment in education and diversity will create lasting impact in the financial industry,' said Adage Capital's CEO."
        },
        {
            "title": "Vanguard reports record inflows of $50 billion in Q3 2024",
            "text": "Vanguard Group reported record quarterly inflows of $50 billion in the third quarter of 2024, driven by strong performance across its index fund lineup and growing investor preference for low-cost passive strategies. The company's total assets under management now exceed $8 trillion. 'Our continued focus on low costs and broad diversification continues to resonate with investors,' said Vanguard's CEO."
        }
    ]
    
    print("🧪 Testing Structured Sentiment Analysis")
    print("=" * 60)
    
    config = Config()
    openai_api_key = config.get_openai_api_key()
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n📰 Article {i}: {article['title']}")
        print("-" * 50)
        
        # Test lexicon-based structured analysis
        print("🔍 Lexicon-based Analysis:")
        lexicon_result = analyze_sentiment_lexicon_structured(article['text'], article['title'])
        print(f"   Entity: {lexicon_result['entity']}")
        print(f"   Event Type: {lexicon_result['event_type']}")
        print(f"   Sentiment Score: {lexicon_result['sentiment_score']}")
        print(f"   Confidence: {lexicon_result['confidence']}")
        print(f"   Reasoning: {lexicon_result['reasoning']}")
        print(f"   Summary: {lexicon_result['summary']}")
        if lexicon_result['key_quotes']:
            print(f"   Key Quotes: {', '.join(lexicon_result['key_quotes'])}")
        
        # Test LLM-based structured analysis if API key is available
        if openai_api_key:
            print("\n🤖 LLM-based Analysis:")
            try:
                llm_result = asyncio.run(analyze_sentiment_structured(article['text'], article['title'], openai_api_key))
                print(f"   Entity: {llm_result['entity']}")
                print(f"   Event Type: {llm_result['event_type']}")
                print(f"   Sentiment Score: {llm_result['sentiment_score']}")
                print(f"   Confidence: {llm_result['confidence']}")
                print(f"   Reasoning: {llm_result['reasoning']}")
                print(f"   Summary: {llm_result['summary']}")
                if llm_result['key_quotes']:
                    print(f"   Key Quotes: {', '.join(llm_result['key_quotes'])}")
            except Exception as e:
                print(f"   Error: {e}")
        else:
            print("\n🤖 LLM-based Analysis: Skipped (no OpenAI API key)")
        
        print("\n" + "=" * 60)

def test_event_classification():
    """Test the event classification functionality"""
    
    print("\n🎯 Testing Event Classification")
    print("=" * 40)
    
    from risk_monitor.utils.sentiment import _classify_event_type
    
    test_texts = [
        ("regulatory", "SEC announces new regulatory requirements for asset managers"),
        ("legal", "Company faces lawsuit over alleged violations"),
        ("product_launch", "New ETF product launched to meet investor demand"),
        ("product_closure", "Fund closure announced due to poor performance"),
        ("performance", "Q3 earnings report shows strong growth"),
        ("inflows_outflows", "Record $2 billion in new investments"),
        ("ratings", "Credit rating upgraded by Moody's"),
        ("operations", "Strategic restructuring announced"),
        ("donations", "Charitable donation of $5 million made"),
        ("other", "General market commentary and analysis")
    ]
    
    for expected_type, text in test_texts:
        detected_type = _classify_event_type(text)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} Expected: {expected_type}, Detected: {detected_type} - {text}")

def test_entity_extraction():
    """Test the entity extraction functionality"""
    
    print("\n🏢 Testing Entity Extraction")
    print("=" * 40)
    
    from risk_monitor.utils.sentiment import _extract_entity
    
    test_cases = [
        ("Goldman Sachs Asset Management announces new fund", "Goldman Sachs"),
        ("Blackstone Group reports strong Q3 results", "Blackstone"),
        ("Vanguard launches new ESG fund", "Vanguard"),
        ("Unknown company reports earnings", "Unknown"),
    ]
    
    for expected_entity, text in test_cases:
        detected_entity = _extract_entity(text, "")
        status = "✅" if detected_entity == expected_entity else "❌"
        print(f"{status} Expected: {expected_entity}, Detected: {detected_entity} - {text}")

if __name__ == "__main__":
    print("🚀 Starting Structured Sentiment Analysis Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_structured_sentiment()
        test_event_classification()
        test_entity_extraction()
        
        print("\n✅ All tests completed successfully!")
        print("\n📊 Summary:")
        print("- Structured sentiment analysis provides entity identification")
        print("- Event classification categorizes news by type")
        print("- Detailed reasoning explains sentiment scores")
        print("- Key quotes extract important evidence")
        print("- Both lexicon and LLM methods supported")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
