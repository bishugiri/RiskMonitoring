#!/usr/bin/env python3
"""
Test script to verify text_area key conflicts are resolved
"""

import re
import sys
import os

def test_unique_keys():
    """Test that all text_area widgets have unique keys"""
    
    print("🔍 Testing text_area key uniqueness...")
    
    with open('risk_monitor/api/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Find all text_area keys
    key_pattern = r'key=["\']([^"\']+)["\']'
    keys = re.findall(key_pattern, content)
    
    # Check for duplicate keys
    duplicate_keys = [key for key in set(keys) if keys.count(key) > 1]
    
    if duplicate_keys:
        print("⚠️ Found duplicate keys:")
        for key in duplicate_keys:
            print(f"   {key}")
        return False
    else:
        print("✅ All keys are unique")
        
        # Show all unique keys
        unique_keys = list(set(keys))
        print(f"📋 All unique keys found ({len(unique_keys)}):")
        for key in sorted(unique_keys):
            print(f"   - {key}")
        return True

def test_rag_keys():
    """Test specifically for RAG article content keys"""
    
    print("\n🔍 Testing RAG article content keys...")
    
    with open('risk_monitor/api/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Find all RAG article content keys
    rag_key_pattern = r'key=["\']article_content_rag_(\d+)_([^"\']+)["\']'
    rag_keys = re.findall(rag_key_pattern, content)
    
    if rag_keys:
        print(f"📊 Found {len(rag_keys)} RAG article content keys:")
        for index, hash_val in rag_keys:
            print(f"   - article_content_rag_{index}_{hash_val}")
        
        # Check if they have indices
        indices = [index for index, _ in rag_keys]
        if len(set(indices)) == len(indices):
            print("✅ All RAG keys have unique indices")
            return True
        else:
            print("⚠️ Some RAG keys have duplicate indices")
            return False
    else:
        print("❌ No RAG article content keys found")
        return False

if __name__ == "__main__":
    success1 = test_unique_keys()
    success2 = test_rag_keys()
    
    if success1 and success2:
        print("\n🎉 All text_area key conflicts resolved!")
    else:
        print("\n❌ Some key conflicts still exist")
