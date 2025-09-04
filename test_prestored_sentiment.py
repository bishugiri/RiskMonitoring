#!/usr/bin/env python3
"""
Test script to verify pre-stored sentiment score usage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_prestored_sentiment():
    """Test that LLM uses pre-stored sentiment scores"""
    
    print("🔍 Testing Pre-Stored Sentiment Score Usage")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test with the specific article that showed discrepancy
    test_query = "provide the sentiment score on Apple's Expanding Game Content to Aid Services Growth: What's Ahead?"
    
    print(f"Query: {test_query}")
    print("-" * 60)
    
    try:
        # Test with entity filter for Apple articles
        response = rag_service.chat_with_agent(
            user_query=test_query,
            entity_filter="AAPL",
            date_filter="2025-09-02"
        )
        
        print(f"✅ Response generated")
        response_text = response.get('response', '')
        print(f"Response: {response_text}")
        
        # Check if the response contains the correct sentiment score
        if '0.3' in response_text:
            print("✅ Correct pre-stored sentiment score (0.3) found in response")
        elif '0.778' in response_text:
            print("❌ Incorrect real-time sentiment score (0.778) found - should be 0.3")
        elif '0' in response_text and 'sentiment' in response_text.lower():
            print("❌ Incorrect sentiment score (0) found - should be 0.3")
        else:
            print("⚠️ Sentiment score not clearly identified in response")
            
        # Check if response mentions real-time analysis
        if 'analyze' in response_text.lower() or 'analysis' in response_text.lower():
            print("⚠️ Response mentions analysis - may be doing real-time sentiment analysis")
        else:
            print("✅ Response appears to use pre-stored data")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_prestored_sentiment()
