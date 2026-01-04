#!/usr/bin/env python
"""Test script to verify Gemini API configuration"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

print("=" * 60)
print("GEMINI API CONFIGURATION TEST")
print("=" * 60)

# Check API key
api_key = os.getenv('GeminiApi')
if api_key:
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        print("✓ Gemini API configured successfully")
        
        # Test with a simple prompt
        print("\n📊 Testing Gemini model (gemini-1.5-flash)...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        test_prompt = "Briefly list the top 5 programming languages in 2024."
        response = model.generate_content(test_prompt)
        
        print("✓ Gemini connection successful!")
        print(f"\nTest Response:\n{response.text[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
else:
    print("❌ GeminiApi key not found in .env file")
    print("Please add 'GeminiApi=<your-api-key>' to .env file")

print("\n" + "=" * 60)
