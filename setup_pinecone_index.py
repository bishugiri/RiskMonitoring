#!/usr/bin/env python3
"""
Script to help set up Pinecone index configuration
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from risk_monitor.config.settings import Config

def setup_pinecone_index():
    """Help set up Pinecone index configuration"""
    
    print("🔧 Pinecone Index Setup Helper")
    print("=" * 50)
    
    try:
        import pinecone
        
        # Get API key
        config = Config()
        api_key = config.get_pinecone_api_key()
        
        if not api_key:
            print("❌ No Pinecone API key found in configuration")
            print("💡 Add your Pinecone API key to .streamlit/secrets.toml")
            return False
        
        print(f"✅ Found Pinecone API key: {api_key[:10]}...")
        
        # Initialize with correct environment
        pinecone.init(api_key=api_key, environment=config.PINECONE_ENVIRONMENT)
        
        # List all indexes
        indexes = pinecone.list_indexes()
        
        if not indexes:
            print("\n❌ No existing indexes found")
            print("\n🔧 To fix this, you need to:")
            print("   1. Go to your Pinecone dashboard: https://app.pinecone.io/")
            print("   2. Create a new index with these settings:")
            print("      - Name: sentiment-db (or any name you prefer)")
            print("      - Dimension: 3072")
            print("      - Metric: cosine")
            print("      - Environment: us-east1-gcp")
            print("   3. Wait for the index to be ready")
            print("   4. Run this script again")
            
            # Ask if user wants to update config
            print(f"\n📝 Current configuration:")
            print(f"   - Index name: {config.PINECONE_INDEX_NAME}")
            print(f"   - Environment: {config.PINECONE_ENVIRONMENT}")
            
            return False
        
        print(f"\n✅ Found {len(indexes)} existing indexes: {indexes}")
        
        # Check each index
        compatible_indexes = []
        for index_name in indexes:
            try:
                index = pinecone.Index(index_name)
                stats = index.describe_index_stats()
                
                print(f"\n📊 Index: {index_name}")
                print(f"   - Dimension: {stats.dimension}")
                print(f"   - Total vectors: {stats.total_vector_count}")
                print(f"   - Index fullness: {stats.index_fullness:.2%}")
                
                # Check if this index can be used for our purpose
                if stats.dimension == 3072:
                    print(f"   ✅ Compatible with OpenAI text-embedding-3-large")
                    compatible_indexes.append(index_name)
                else:
                    print(f"   ⚠️ Different dimension ({stats.dimension}), not compatible")
                    
            except Exception as e:
                print(f"   ❌ Error checking index {index_name}: {e}")
        
        if compatible_indexes:
            print(f"\n🎉 Found {len(compatible_indexes)} compatible indexes!")
            print("💡 You can use any of these indexes:")
            for idx, index_name in enumerate(compatible_indexes, 1):
                print(f"   {idx}. {index_name}")
            
            # Ask user which index to use
            if len(compatible_indexes) > 1:
                print(f"\n📝 To use a different index, update your config:")
                print(f"   In risk_monitor/config/settings.py, change:")
                print(f"   PINECONE_INDEX_NAME = \"{compatible_indexes[0]}\"")
            
            return True
        else:
            print("\n❌ No compatible indexes found")
            print("💡 You need an index with dimension 3072")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_pinecone_index()
    sys.exit(0 if success else 1)
