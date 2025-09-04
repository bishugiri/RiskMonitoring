#!/usr/bin/env python3
"""
Test script to verify sentiment score extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_sentiment_extraction():
    """Test sentiment score extraction from article data"""
    
    print("🔍 Testing Sentiment Score Extraction")
    print("=" * 50)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test with a specific query that should return the correct sentiment score
    test_query = "what is the sentiment score of The Art of Valuation: Discovering Apple Inc's Intrinsic Value"
    
    print(f"Query: {test_query}")
    print("-" * 50)
    
    try:
        # Test with entity filter for Apple articles
        response = rag_service.chat_with_agent(
            user_query=test_query,
            entity_filter="AAPL",
            date_filter="2025-09-02"
        )
        
        print(f"✅ Response generated")
        print(f"Response: {response.get('response', 'No response')}")
        
        # Check if the response contains the correct sentiment score
        response_text = response.get('response', '')
        if '-0.2' in response_text:
            print("✅ Correct sentiment score (-0.2) found in response")
        elif '0' in response_text and 'sentiment' in response_text.lower():
            print("❌ Incorrect sentiment score (0) found - should be -0.2")
        else:
            print("⚠️ Sentiment score not clearly identified in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sentiment_extraction()
