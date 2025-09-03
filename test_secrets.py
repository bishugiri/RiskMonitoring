
import streamlit as st
import os

print(f"Current directory: {os.getcwd()}")
print(f"Secrets file exists: {os.path.exists('.streamlit/secrets.toml')}")

if hasattr(st, 'secrets'):
    print("st.secrets exists")
    try:
        serpapi_key = st.secrets.get("SERPAPI_KEY")
        if serpapi_key:
            print(f"SERPAPI_KEY found: {serpapi_key[:10]}...")
        else:
            print("SERPAPI_KEY not found")
    except Exception as e:
        print(f"Error accessing secrets: {e}")
else:
    print("st.secrets does not exist")
