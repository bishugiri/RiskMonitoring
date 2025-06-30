#!/usr/bin/env python3
"""
Debug script for news collection
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_collection():
    """Test basic news collection"""
    print("🔍 Testing basic news collection...")
    
    try:
        from news_collector import NewsCollector
        from config import Config
        
        print(f"API Key: {'Set' if Config.get_serpapi_key() else 'Not set'}")
        
        collector = NewsCollector()
        print("✅ NewsCollector created")
        
        # Test search first
        articles = collector.search_news("Apple Inc", 3)
        print(f"✅ Search found {len(articles)} articles")
        
        if articles:
            print("Sample article:")
            print(f"  Title: {articles[0].get('title', 'No title')}")
            print(f"  Source: {articles[0].get('source', 'No source')}")
        
        # Test full collection
        collected = collector.collect_articles("Apple Inc", 2)
        print(f"✅ Collection returned {len(collected)} articles")
        
        if collected:
            print("Collected article:")
            print(f"  Title: {collected[0].get('title', 'No title')}")
            print(f"  Text length: {len(collected[0].get('text', ''))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_function():
    """Test the Streamlit collect_news function"""
    print("\n🌐 Testing Streamlit collect_news function...")
    
    try:
        from streamlit_app import collect_news
        from config import Config
        
        # Mock controls
        controls = {
            'search_mode': 'Custom Query',
            'custom_query': 'Apple Inc',
            'num_articles': 2,
            'api_key': Config.get_serpapi_key(),
            'auto_save': False
        }
        
        print("✅ collect_news function imported")
        print(f"Controls: {controls}")
        
        # Test the function
        result = collect_news(controls)
        print(f"✅ collect_news returned: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("🐛 Debugging News Collection")
    print("=" * 50)
    
    # Test basic collection
    if not test_basic_collection():
        print("❌ Basic collection test failed")
        return 1
    
    # Test Streamlit function
    if not test_streamlit_function():
        print("❌ Streamlit function test failed")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ Debug complete!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 