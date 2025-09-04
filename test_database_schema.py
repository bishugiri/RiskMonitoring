#!/usr/bin/env python3
"""
Test Database Schema Understanding
Verify that the LLM understands the Pinecone JSON structure and answers correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_database_schema_understanding():
    """Test that the LLM understands the database JSON structure"""
    print("🔍 Testing Database Schema Understanding")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries that require understanding of the JSON structure
    test_queries = [
        {
            "query": "what is the sentiment score of Shareholder Relations?",
            "expected_fields": ["sentiment_score", "sentiment_category"],
            "description": "Direct sentiment score lookup"
        },
        {
            "query": "give me the risk score for Shareholder Relations",
            "expected_fields": ["risk_score"],
            "description": "Direct risk score lookup"
        },
        {
            "query": "provide me the full article text for Shareholder Relations",
            "expected_fields": ["text"],
            "description": "Full article content request"
        },
        {
            "query": "what is the source of the Shareholder Relations article?",
            "expected_fields": ["source"],
            "description": "Metadata field lookup"
        },
        {
            "query": "give me the URL for Shareholder Relations",
            "expected_fields": ["url"],
            "description": "URL field lookup"
        }
    ]
    
    print("📋 Test Queries:")
    for i, test in enumerate(test_queries, 1):
        print(f"   {i}. {test['query']}")
        print(f"      Expected fields: {test['expected_fields']}")
        print(f"      Type: {test['description']}")
        print()
    
    print("🔍 Running tests with database schema understanding...")
    print("=" * 60)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Expected fields: {test['expected_fields']}")
        print("-" * 50)
        
        try:
            # Get response from RAG service
            response = rag_service.chat_with_agent(
                user_query=test['query'],
                entity_filter="NUM",  # Use the entity from the example
                date_filter="2025-09-04"  # Use the date from the example
            )
            
            print(f"✅ Response generated")
            print(f"Response: {response}")
            
            # Extract the actual response text from the dictionary
            response_text = response.get('response', str(response)) if isinstance(response, dict) else str(response)
            
            # Check if response indicates understanding of schema
            if "not available" in response_text.lower() or "not found" in response_text.lower():
                print("✅ Correctly indicates information not available")
            elif any(field in response_text.lower() for field in test['expected_fields']):
                print("✅ Response shows understanding of database fields")
            else:
                print("⚠️ Response may not be using database schema correctly")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🎯 Database Schema Understanding Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_database_schema_understanding()
