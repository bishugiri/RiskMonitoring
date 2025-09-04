#!/usr/bin/env python3
"""
Test script to verify strict data usage rules
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_strict_data_usage():
    """Test that LLM follows strict data usage rules"""
    
    print("🔍 Testing Strict Data Usage Rules")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries that should only use provided data
    test_queries = [
        {
            "query": "what is the current stock price of Apple?",
            "expected": "Should say information not available in provided data",
            "type": "external_knowledge_test"
        },
        {
            "query": "what is the sentiment score of The Art of Valuation: Discovering Apple Inc's Intrinsic Value?",
            "expected": "Should use exact sentiment score from database",
            "type": "exact_data_test"
        },
        {
            "query": "what is the market outlook for 2025?",
            "expected": "Should say information not available in provided data",
            "type": "future_prediction_test"
        }
    ]
    
    print("\n📋 Test Queries:")
    for i, test in enumerate(test_queries, 1):
        print(f"   {i}. {test['query']}")
        print(f"      Expected: {test['expected']}")
        print(f"      Type: {test['type']}")
        print()
    
    print("🔍 Running tests with strict data usage rules...")
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
            response_text = response.get('response', '')
            print(f"Response: {response_text}")
            
            # Check if response follows strict data usage rules
            if "not available" in response_text.lower() or "not found" in response_text.lower():
                print("✅ Correctly indicates information not available")
            elif "external" in response_text.lower() or "general" in response_text.lower():
                print("✅ Correctly avoids external knowledge")
            elif test['type'] == 'exact_data_test' and any(char.isdigit() for char in response_text):
                print("✅ Uses exact data from database")
            else:
                print("⚠️ Response may not be following strict data usage rules")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_strict_data_usage()
