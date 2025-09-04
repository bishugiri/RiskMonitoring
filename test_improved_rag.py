#!/usr/bin/env python3
"""
Test script for improved RAG service functionality
Demonstrates different query types and their specialized handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService
import json

def test_query_classification():
    """Test the query classification system"""
    print("🧪 TESTING QUERY CLASSIFICATION")
    print("=" * 50)
    
    rag_service = RAGService()
    
    test_queries = [
        "What's the overall sentiment trend for Apple?",
        "Which articles have the highest risk scores?",
        "Compare the sentiment between different entities",
        "Show me all headlines from yesterday",
        "What are the main risk indicators mentioned?",
        "Give me the full article about Apple's AI strategy",
        "What is the article about Apple's new iPhone?",
        "How many articles do we have about Tesla?",
        "Show me the trend in risk scores over time",
        "Compare Apple vs Microsoft sentiment",
        "Give me article headline of this day"
    ]
    
    for query in test_queries:
        classification = rag_service.classify_query_type(query)
        print(f"Query: '{query}'")
        print(f"  Type: {classification['query_type']}")
        print(f"  Confidence: {classification['confidence']:.2f}")
        print(f"  Patterns: {classification['matched_patterns']}")
        print()

def test_specialized_prompts():
    """Test the specialized prompt generation"""
    print("🧪 TESTING SPECIALIZED PROMPTS")
    print("=" * 50)
    
    rag_service = RAGService()
    
    test_cases = [
        ("sentiment_trend", "What's the overall sentiment trend for Apple?"),
        ("risk_analysis", "Which articles have the highest risk scores?"),
        ("headlines", "Show me all headlines from yesterday"),
        ("full_article", "Give me the full article about Apple's AI strategy"),
        ("comparison", "Compare Apple vs Microsoft sentiment")
    ]
    
    for query_type, query in test_cases:
        prompt = rag_service.create_specialized_system_prompt(query_type, query)
        print(f"Query Type: {query_type}")
        print(f"Query: '{query}'")
        print(f"Prompt Length: {len(prompt)} characters")
        print(f"Prompt Preview: {prompt[:200]}...")
        print()

def test_context_formatting():
    """Test the context formatting for different query types"""
    print("🧪 TESTING CONTEXT FORMATTING")
    print("=" * 50)
    
    rag_service = RAGService()
    
    # Mock articles for testing
    mock_articles = [
        {
            'title': 'Apple Bets On Air Power Over AI',
            'source': 'Benzinga',
            'entity': 'AAPL',
            'sentiment_score': 0.2,
            'sentiment_category': 'Positive',
            'risk_score': 10.0,
            'text': 'This article discusses Apple\'s strategy of focusing on a new iPhone Air model rather than AI advancements...',
            'url': 'https://example.com/article1',
            'publish_date': '2025-09-02'
        },
        {
            'title': 'Tesla Faces Regulatory Challenges',
            'source': 'Reuters',
            'entity': 'TSLA',
            'sentiment_score': -0.3,
            'sentiment_category': 'Negative',
            'risk_score': 15.0,
            'text': 'Tesla is facing new regulatory challenges in multiple markets...',
            'url': 'https://example.com/article2',
            'publish_date': '2025-09-02'
        }
    ]
    
    query_types = ['sentiment_trend', 'risk_analysis', 'headlines', 'full_article', 'comparison']
    
    for query_type in query_types:
        context = rag_service.format_context_for_query_type(mock_articles, query_type)
        print(f"Query Type: {query_type}")
        print(f"Context Length: {len(context)} characters")
        print(f"Context Preview: {context[:300]}...")
        print()

def test_full_rag_flow():
    """Test the complete RAG flow with different query types"""
    print("🧪 TESTING FULL RAG FLOW")
    print("=" * 50)
    
    rag_service = RAGService()
    
    test_queries = [
        "What's the overall sentiment trend for Apple?",
        "Which articles have the highest risk scores?",
        "Show me all headlines from yesterday",
        "Give me the full article about Apple's AI strategy"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing Query: '{query}'")
        print("-" * 40)
        
        try:
            # Test the complete flow
            response = rag_service.chat_with_agent(
                user_query=query,
                entity_filter="AAPL",
                date_filter="2025-09-02"
            )
            
            print(f"✅ Response generated successfully")
            print(f"   Query Type: {response.get('query_type', 'Unknown')}")
            print(f"   Articles Used: {response.get('articles_used', 0)}")
            print(f"   Response Length: {len(response.get('response', ''))} characters")
            print(f"   Response Preview: {response.get('response', '')[:200]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 IMPROVED RAG SERVICE TESTING")
    print("=" * 60)
    
    # Test query classification
    test_query_classification()
    
    # Test specialized prompts
    test_specialized_prompts()
    
    # Test context formatting
    test_context_formatting()
    
    # Test full RAG flow (this will require actual database connection)
    print("\n⚠️  Note: Full RAG flow test requires database connection")
    print("   Run this test when the database is available")
    
    # Uncomment to test with actual database
    # test_full_rag_flow()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
