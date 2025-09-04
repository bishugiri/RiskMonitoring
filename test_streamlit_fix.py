#!/usr/bin/env python3
"""
Test script to verify Streamlit text_area key conflicts are resolved
"""

import streamlit as st
import sys
import os
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_text_area_keys():
    """Test that all text_area widgets have unique keys"""
    
    print("🔍 Testing Streamlit text_area key uniqueness...")
    
    # Import the streamlit app to check for key conflicts
    try:
        from risk_monitor.api import streamlit_app
        print("✅ Streamlit app imports successfully")
        
        # Check if there are any obvious key conflicts in the code
        with open('risk_monitor/api/streamlit_app.py', 'r') as f:
            content = f.read()
            
        # Find all st.text_area calls with proper regex
        text_area_pattern = r'st\.text_area\s*\([^)]*\)'
        text_area_matches = re.findall(text_area_pattern, content, re.DOTALL)
        
        print(f"📊 Found {len(text_area_matches)} st.text_area widgets")
        
        # Check for widgets without keys
        widgets_without_keys = []
        for match in text_area_matches:
            if 'key=' not in match:
                widgets_without_keys.append(match.strip())
        
        if widgets_without_keys:
            print("⚠️ Found text_area widgets without keys:")
            for widget in widgets_without_keys:
                print(f"   {widget[:100]}...")
        else:
            print("✅ All text_area widgets have keys")
            
        # Check for duplicate keys
        key_pattern = r'key=["\']([^"\']+)["\']'
        keys = re.findall(key_pattern, content)
        
        duplicate_keys = [key for key in set(keys) if keys.count(key) > 1]
        if duplicate_keys:
            print("⚠️ Found duplicate keys:")
            for key in duplicate_keys:
                print(f"   {key}")
        else:
            print("✅ All keys are unique")
            
        # Show all unique keys for verification
        unique_keys = list(set(keys))
        print(f"📋 All unique keys found ({len(unique_keys)}):")
        for key in sorted(unique_keys):
            print(f"   - {key}")
            
        return len(widgets_without_keys) == 0 and len(duplicate_keys) == 0
        
    except Exception as e:
        print(f"❌ Error testing Streamlit app: {e}")
        return False

if __name__ == "__main__":
    success = test_text_area_keys()
    if success:
        print("\n🎉 All Streamlit text_area key conflicts resolved!")
    else:
        print("\n❌ Some key conflicts still exist")
