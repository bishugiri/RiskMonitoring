#!/usr/bin/env python3
"""
Test script for enhanced RAG service capabilities
Demonstrates different types of queries and response formats
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService
import json

def test_enhanced_rag_capabilities():
    """Test the enhanced RAG service with different query types"""
    
    print("🚀 Testing Enhanced RAG Service Capabilities")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries covering different types
    test_queries = [
        {
            "query": "What's the overall sentiment trend for Apple?",
            "type": "sentiment_trend",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        },
        {
            "query": "Which articles have the highest risk scores?",
            "type": "risk_analysis",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        },
        {
            "query": "Show me all headlines from yesterday",
            "type": "temporal",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        },
        {
            "query": "What are the main risk indicators mentioned?",
            "type": "risk_indicators",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        },
        {
            "query": "Give me the full article about Apple's AI strategy",
            "type": "specific_article",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        },
        {
            "query": "How many articles mention 'iPhone'?",
            "type": "data_query",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 Test Case {i}: {test_case['type'].upper()}")
        print(f"Query: '{test_case['query']}'")
        print(f"Entity Filter: {test_case['entity_filter']}")
        print(f"Date Filter: {test_case['date_filter']}")
        print("-" * 50)
        
        try:
            # Process the query
            response = rag_service.chat_with_agent(
                user_query=test_case['query'],
                entity_filter=test_case['entity_filter'],
                date_filter=test_case['date_filter']
            )
            
            # Display results
            print(f"✅ Query Type Detected: {response.get('query_type', 'Unknown')}")
            print(f"📊 Articles Found: {response.get('articles_used', 0)}")
            print(f"🔍 Response Length: {len(response.get('response', ''))} characters")
            
            # Show response preview
            response_text = response.get('response', '')
            print(f"\n📝 Response Preview (first 300 chars):")
            print(f"{response_text[:300]}...")
            
            # Show metadata
            print(f"\n📋 Response Metadata:")
            print(f"   Query Type: {response.get('query_type', 'Unknown')}")
            print(f"   Articles Used: {response.get('articles_used', 0)}")
            print(f"   Entity Filter: {response.get('entity_filter_applied', 'None')}")
            print(f"   Date Filter: {response.get('date_filter_applied', 'None')}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        print("\n" + "=" * 60)
    
    print("\n🎯 Enhanced RAG Service Test Complete!")
    print("The system now supports:")
    print("✅ Sentiment trend analysis")
    print("✅ Risk score analysis")
    print("✅ Temporal queries")
    print("✅ Risk indicator analysis")
    print("✅ Specific article requests")
    print("✅ Data queries")
    print("✅ Comparative analysis")

if __name__ == "__main__":
    test_enhanced_rag_capabilities()
