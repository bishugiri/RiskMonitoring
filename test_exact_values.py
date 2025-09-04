#!/usr/bin/env python3
"""
Test script to verify exact value extraction from database JSON structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_exact_values():
    """Test that LLM extracts exact values from database JSON structure"""
    
    print("🔍 Testing Exact Value Extraction from Database JSON")
    print("=" * 70)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries that should return exact values from database
    test_queries = [
        {
            "query": "give me risk score on Investors Heavily Search Apple Inc. (AAPL): Here is What You Need to Know",
            "expected_sentiment": "0.5",
            "expected_risk": "1.8889308651303365",
            "type": "exact_metrics_test"
        },
        {
            "query": "what is the sentiment score of Investors Heavily Search Apple Inc. (AAPL): Here is What You Need to Know",
            "expected_sentiment": "0.5",
            "expected_risk": "1.8889308651303365",
            "type": "sentiment_score_test"
        },
        {
            "query": "provide the metrics and link to this article Investors Heavily Search Apple Inc. (AAPL): Here is What You Need to Know",
            "expected_sentiment": "0.5",
            "expected_risk": "1.8889308651303365",
            "type": "metrics_and_link_test"
        }
    ]
    
    print("\n📋 Test Queries:")
    for i, test in enumerate(test_queries, 1):
        print(f"   {i}. {test['query']}")
        print(f"      Expected Sentiment: {test['expected_sentiment']}")
        print(f"      Expected Risk: {test['expected_risk']}")
        print(f"      Type: {test['type']}")
        print()
    
    print("🔍 Running tests with exact value extraction...")
    print("=" * 70)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test['type']}")
        print(f"Query: {test['query']}")
        print(f"Expected Sentiment: {test['expected_sentiment']}")
        print(f"Expected Risk: {test['expected_risk']}")
        print("-" * 50)
        
        try:
            # Test with entity filter for Apple articles
            response = rag_service.chat_with_agent(
                user_query=test['query'],
                entity_filter="AAPL",
                date_filter="2025-09-02"
            )
            
            print(f"✅ Response generated")
            response_text = response.get('response', '')
            print(f"Response: {response_text}")
            
            # Check if response contains the correct exact values
            sentiment_found = test['expected_sentiment'] in response_text
            risk_found = test['expected_risk'] in response_text
            
            if sentiment_found:
                print(f"✅ Correct sentiment score ({test['expected_sentiment']}) found")
            else:
                print(f"❌ Expected sentiment score ({test['expected_sentiment']}) not found")
                
            if risk_found:
                print(f"✅ Correct risk score ({test['expected_risk']}) found")
            else:
                print(f"❌ Expected risk score ({test['expected_risk']}) not found")
                
            # Check for incorrect default values
            if '0' in response_text and ('sentiment' in response_text.lower() or 'risk' in response_text.lower()):
                print("⚠️ Response contains '0' - may be using default values instead of exact values")
            else:
                print("✅ No default '0' values found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_exact_values()
