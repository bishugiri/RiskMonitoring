#!/usr/bin/env python3
"""
Test script for improved RAG service response mechanism
Demonstrates efficient handling of specific queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_improved_rag_responses():
    """Test the improved RAG service with specific query types"""
    
    print("🚀 Testing Improved RAG Service Response Mechanism")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries that should get precise, efficient responses
    test_queries = [
        {
            "query": "provide me the article headline of this day",
            "expected": "List of article titles only",
            "type": "headline_request"
        },
        {
            "query": "provide the metrics and link to this article Apple Shifts Automation Costs to Suppliers Amid China Exit",
            "expected": "Exact sentiment score, risk score, and URL only",
            "type": "metric_request"
        },
        {
            "query": "what is the sentiment score of it? Apple: The AI Race Loser (NASDAQ )",
            "expected": "Exact numeric sentiment score only",
            "type": "sentiment_score_request"
        },
        {
            "query": "is there any article with negative sentiment, if so then what is the sentiment score of it?",
            "expected": "Article title and exact sentiment score",
            "type": "sentiment_filter_request"
        }
    ]
    
    print("\n📋 Test Queries:")
    for i, test in enumerate(test_queries, 1):
        print(f"   {i}. {test['query']}")
        print(f"      Expected: {test['expected']}")
        print(f"      Type: {test['type']}")
        print()
    
    print("🔍 Running tests with optimized response mechanism...")
    print("=" * 60)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test['type']}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        print("-" * 40)
        
        try:
            # Test with entity filter for Apple articles
            response = rag_service.chat_with_agent(
                user_query=test['query'],
                entity_filter="AAPL",
                date_filter="2025-09-02"
            )
            
            print(f"✅ Response generated")
            print(f"Response length: {len(response.get('response', ''))} characters")
            print(f"Articles used: {response.get('articles_used', 0)}")
            
            # Show response preview
            response_text = response.get('response', '')
            if response_text:
                print(f"Response preview: {response_text[:200]}...")
            else:
                print("❌ No response generated")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_improved_rag_responses()
