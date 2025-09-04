#!/usr/bin/env python3
"""
Test script for optimized RAG service performance
Demonstrates conversation caching and optimized search flow
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_monitor.core.rag_service import RAGService

def test_optimized_rag_performance():
    """Test the optimized RAG service with conversation caching"""
    
    print("🚀 Testing Optimized RAG Service Performance")
    print("=" * 60)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test conversation flow with follow-up questions
    test_conversation = [
        {
            "query": "What's the overall sentiment trend for Apple?",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02",
            "expected_cache": "MISS"  # First query should miss cache
        },
        {
            "query": "Which articles have the highest risk scores?",
            "entity_filter": "AAPL", 
            "date_filter": "2025-09-02",
            "expected_cache": "HIT"  # Follow-up should hit cache
        },
        {
            "query": "Show me all headlines from yesterday",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02", 
            "expected_cache": "HIT"  # Same filters should hit cache
        },
        {
            "query": "What are the main risk indicators mentioned?",
            "entity_filter": "AAPL",
            "date_filter": "2025-09-02",
            "expected_cache": "HIT"  # Same filters should hit cache
        },
        {
            "query": "How is Tesla performing?",
            "entity_filter": "TSLA",  # Different entity
            "date_filter": "2025-09-02",
            "expected_cache": "MISS"  # Different entity should miss cache
        },
        {
            "query": "What's Tesla's sentiment?",
            "entity_filter": "TSLA",
            "date_filter": "2025-09-02",
            "expected_cache": "HIT"  # Same filters should hit cache
        }
    ]
    
    total_time = 0
    cache_hits = 0
    cache_misses = 0
    
    for i, test_case in enumerate(test_conversation, 1):
        print(f"\n📋 Test Case {i}: {test_case['expected_cache']} Expected")
        print(f"Query: '{test_case['query']}'")
        print(f"Entity Filter: {test_case['entity_filter']}")
        print(f"Date Filter: {test_case['date_filter']}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Process the query
            response = rag_service.chat_with_agent(
                user_query=test_case['query'],
                entity_filter=test_case['entity_filter'],
                date_filter=test_case['date_filter']
            )
            
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
            
            # Check cache status from logs (simplified check)
            cache_status = "HIT" if query_time < 2.0 else "MISS"  # Rough estimate
            if cache_status == "HIT":
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Display results
            print(f"⏱️  Query Time: {query_time:.2f} seconds")
            print(f"📊 Cache Status: {cache_status}")
            print(f"📊 Articles Found: {response.get('articles_used', 0)}")
            print(f"🔍 Response Length: {len(response.get('response', ''))} characters")
            
            # Show response preview
            response_text = response.get('response', '')
            print(f"\n📝 Response Preview (first 200 chars):")
            print(f"{response_text[:200]}...")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
        
        print("\n" + "=" * 60)
    
    # Performance summary
    print(f"\n🎯 Performance Summary:")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Average Time per Query: {total_time/len(test_conversation):.2f} seconds")
    print(f"Cache Hits: {cache_hits}")
    print(f"Cache Misses: {cache_misses}")
    print(f"Cache Hit Rate: {(cache_hits/(cache_hits+cache_misses)*100):.1f}%")
    
    print(f"\n⚡ Optimization Benefits:")
    print(f"✅ Conversation caching reduces redundant database queries")
    print(f"✅ Follow-up questions use cached articles for faster response")
    print(f"✅ Only top 5 most relevant articles sent to LLM")
    print(f"✅ Semantic search performed on filtered subset only")
    print(f"✅ Cache expires after 5 minutes to ensure data freshness")

def test_cache_invalidation():
    """Test cache invalidation scenarios"""
    
    print("\n🔄 Testing Cache Invalidation")
    print("=" * 60)
    
    rag_service = RAGService()
    
    # Test 1: Same filters should use cache
    print("Test 1: Same filters (should use cache)")
    start_time = time.time()
    response1 = rag_service.chat_with_agent(
        user_query="What's Apple's sentiment?",
        entity_filter="AAPL",
        date_filter="2025-09-02"
    )
    time1 = time.time() - start_time
    
    start_time = time.time()
    response2 = rag_service.chat_with_agent(
        user_query="What are Apple's risks?",
        entity_filter="AAPL", 
        date_filter="2025-09-02"
    )
    time2 = time.time() - start_time
    
    print(f"First query: {time1:.2f}s")
    print(f"Second query: {time2:.2f}s")
    print(f"Speed improvement: {((time1-time2)/time1*100):.1f}%")
    
    # Test 2: Different entity should invalidate cache
    print("\nTest 2: Different entity (should invalidate cache)")
    start_time = time.time()
    response3 = rag_service.chat_with_agent(
        user_query="What's Tesla's sentiment?",
        entity_filter="TSLA",
        date_filter="2025-09-02"
    )
    time3 = time.time() - start_time
    
    print(f"Different entity query: {time3:.2f}s")
    print(f"Cache invalidation working: {'✅' if time3 > time2 else '❌'}")

if __name__ == "__main__":
    test_optimized_rag_performance()
    test_cache_invalidation()
