#!/usr/bin/env python3
"""
Test connection to existing Pinecone index
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from risk_monitor.config.settings import Config

def test_index_connection():
    """Test connection to existing Pinecone index"""
    
    print("🔍 Testing Connection to Existing Pinecone Index...")
    
    try:
        import pinecone
        
        # Get API key
        config = Config()
        api_key = config.get_pinecone_api_key()
        
        if not api_key:
            print("❌ No Pinecone API key found")
            return False
        
        print(f"✅ Found Pinecone API key: {api_key[:10]}...")
        
        # Try to initialize without environment first
        try:
            print("🔄 Trying to initialize without environment...")
            pinecone.init(api_key=api_key)
            print("✅ Initialized without environment")
        except Exception as e:
            print(f"❌ Failed without environment: {e}")
            print("🔄 Trying with configured environment...")
            pinecone.init(api_key=api_key, environment=config.PINECONE_ENVIRONMENT)
            print(f"✅ Initialized with environment: {config.PINECONE_ENVIRONMENT}")
        
        # List indexes
        indexes = pinecone.list_indexes()
        print(f"📋 Found {len(indexes)} indexes: {indexes}")
        
        # Try to connect to sentiment-db
        if "sentiment-db" in indexes:
            print("🎉 Found sentiment-db index!")
            
            # Get index stats
            index = pinecone.Index("sentiment-db")
            stats = index.describe_index_stats()
            
            print(f"📊 Index Stats:")
            print(f"   - Dimension: {stats.dimension}")
            print(f"   - Total vectors: {stats.total_vector_count}")
            print(f"   - Index fullness: {stats.index_fullness:.2%}")
            
            print("\n✅ SUCCESS! Index connection working!")
            return True
        else:
            print("❌ sentiment-db index not found in available indexes")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_index_connection()
    sys.exit(0 if success else 1)
