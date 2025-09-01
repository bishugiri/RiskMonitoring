#!/usr/bin/env python3
"""
Script to find the correct Pinecone environment
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from risk_monitor.config.settings import Config

def find_pinecone_environment():
    """Find the correct Pinecone environment"""
    
    print("🔍 Finding Correct Pinecone Environment...")
    
    try:
        import pinecone
        
        # Get API key
        config = Config()
        api_key = config.get_pinecone_api_key()
        
        if not api_key:
            print("❌ No Pinecone API key found")
            return False
        
        print(f"✅ Found Pinecone API key: {api_key[:10]}...")
        
        # Try different environment patterns
        environments_to_try = [
            "us-east-1",
            "us-east-1-aws", 
            "us-west-1",
            "us-west-2",
            "us-central-1",
            "eu-west-1",
            "aped-4627-b74a",
            "us-east1-gcp",
            "us-west1-gcp",
            "us-central1-gcp",
            "gcp-starter"
        ]
        
        working_env = None
        
        for env in environments_to_try:
            try:
                print(f"🔄 Testing environment: {env}")
                pinecone.init(api_key=api_key, environment=env)
                
                # Try to list indexes
                indexes = pinecone.list_indexes()
                print(f"✅ Environment {env} works! Found {len(indexes)} indexes: {indexes}")
                
                if "sentiment-db" in indexes:
                    print(f"🎉 SUCCESS! Found sentiment-db index in environment: {env}")
                    working_env = env
                    break
                else:
                    print(f"⚠️ sentiment-db not found in this environment")
                    
            except Exception as e:
                print(f"❌ Environment {env} failed: {str(e)[:100]}...")
                continue
        
        if working_env:
            print(f"\n📝 Update your config to use:")
            print(f"PINECONE_ENVIRONMENT = \"{working_env}\"")
            return True
        else:
            print("\n❌ Could not find working environment")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = find_pinecone_environment()
    sys.exit(0 if success else 1)
