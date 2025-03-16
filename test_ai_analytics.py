#!/usr/bin/env python3
"""
Simple script to test the AI service integration with analytics.
This script will:
1. Send several requests to the AI service
2. Query the analytics service to verify the requests were logged

Usage:
    # Make the script executable
    chmod +x test_ai_analytics.py
    
    # Run with default settings (localhost)
    ./test_ai_analytics.py
    
    # Or specify custom service URLs
    ./test_ai_analytics.py --ai-url http://your-ai-service:8082/api/v1 --analytics-url http://your-analytics-service:8083/api/v1
    
    # Run with a specific user ID
    ./test_ai_analytics.py --user-id special_test_user
    
    # Test only specific endpoints
    ./test_ai_analytics.py --endpoints completion,embedding
"""

import requests
import json
import time
from datetime import datetime, timedelta
import argparse
import base64
import os

# Default service URLs
AI_SERVICE_URL = "http://localhost:8082/api/v1"
ANALYTICS_SERVICE_URL = "http://localhost:8083/api/v1"

def send_ai_completion_request(prompt, user_id="test_user", model="gpt-3.5-turbo-instruct"):
    """Send a completion request to the AI service"""
    url = f"{AI_SERVICE_URL}/completions"
    payload = {
        "prompt": prompt,
        "model": model,
        "max_tokens": 100,
        "temperature": 0.7,
        "user_id": user_id,
        "provider": "openai",
        "openai_params": {
            "max_tokens": 100,
            "temperature": 0.7
        }
    }
    
    # Add authentication headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "sk_test_analytics_key"  # Use a test API key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI completion request: {e}")
        return None

def send_ai_embedding_request(text, user_id="test_user", model="text-embedding-3-small"):
    """Send an embedding request to the AI service"""
    url = f"{AI_SERVICE_URL}/embeddings"
    payload = {
        "input": text,
        "model": model,
        "user_id": user_id,
        "provider": "openai"
    }
    
    # Add authentication headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "sk_test_analytics_key"  # Use a test API key
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI embedding request: {e}")
        return None

def send_ai_similarity_request(query, user_id="test_user", model="text-embedding-3-small"):
    """Send a similarity search request to the AI service"""
    url = f"{AI_SERVICE_URL}/similarity"
    payload = {
        "query": query,
        "model": model,
        "limit": 3,
        "threshold": 0.5,
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI similarity request: {e}")
        return None

def send_ai_image_request(prompt, image_url=None, user_id="test_user"):
    """Send an image processing request to the AI service"""
    url = f"{AI_SERVICE_URL}/images"
    
    # Use a standard image URL that's publicly accessible
    default_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2023_06_08_Raccoon1.jpg/1599px-2023_06_08_Raccoon1.jpg"
    
    payload = {
        "prompt": prompt,
        "image_url": image_url or default_image_url, 
        "user_id": user_id,
        "model": "gpt-4-vision"  # Updated model name
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI image request: {e}")
        return None

def send_ai_tts_request(text, user_id="test_user"):
    """Send a text-to-speech request to the AI service"""
    url = f"{AI_SERVICE_URL}/tts/synthesize"
    payload = {
        "text": text,
        "speaking_rate": 15.0,
        "mime_type": "audio/webm",
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # Don't return the audio bytes, just acknowledge success
        return {"success": True, "content_length": len(response.content)}
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI TTS request: {e}")
        return None

def send_ai_tts_emotion_request(text, user_id="test_user"):
    """Send a text-to-speech with emotion request to the AI service"""
    url = f"{AI_SERVICE_URL}/tts/emotion"
    
    # Create multipart form data
    data = {
        "text": text,
        "happiness": 0.8,
        "neutral": 0.4,
        "sadness": 0.1,
        "disgust": 0.1,
        "fear": 0.1,
        "surprise": 0.3,
        "anger": 0.1,
        "other": 0.5,
        "speaking_rate": 15.0,
        "mime_type": "audio/webm",
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        # Don't return the audio bytes, just acknowledge success
        return {"success": True, "content_length": len(response.content)}
    except requests.exceptions.RequestException as e:
        print(f"Error sending AI TTS with emotion request: {e}")
        return None

def check_analytics_data(user_id="test_user", minutes=5):
    """Query the analytics service for recent AI calls"""
    # Calculate start time (last N minutes)
    start_time = datetime.now() - timedelta(minutes=minutes)
    start_str = start_time.strftime("%Y-%m-%d")
    
    # Get AI stats
    url = f"{ANALYTICS_SERVICE_URL}/ai-stats"
    params = {"start": start_str}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Handle empty response
        data = response.json()
        if isinstance(data, list) and len(data) == 0:
            return {
                "totalAPICalls": 0,
                "completionCalls": 0,
                "averageResponseTime": 0,
                "tokensUsed": 0,
                "callTypeDistribution": {},
                "note": "No data returned from analytics service (empty array)"
            }
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error querying analytics: {e}")
        return None

def main():
    global AI_SERVICE_URL, ANALYTICS_SERVICE_URL
    
    parser = argparse.ArgumentParser(description="Test AI service integration with analytics")
    parser.add_argument("--ai-url", default=AI_SERVICE_URL, help="AI service URL")
    parser.add_argument("--analytics-url", default=ANALYTICS_SERVICE_URL, help="Analytics service URL")
    parser.add_argument("--user-id", default="test_user", help="User ID for the test")
    parser.add_argument("--endpoints", default="all", help="Comma-separated list of endpoints to test (completion,embedding,similarity,image,tts,tts_emotion) or 'all'")
    args = parser.parse_args()
    
    AI_SERVICE_URL = args.ai_url
    ANALYTICS_SERVICE_URL = args.analytics_url
    user_id = args.user_id
    
    # Determine which endpoints to test
    endpoints_to_test = args.endpoints.lower().split(',') if args.endpoints.lower() != 'all' else [
        "completion", "embedding", "similarity", "image", "tts", "tts_emotion"
    ]
    
    print("=== Testing AI Service Integration with Analytics ===")
    
    # Test Completion API
    if "completion" in endpoints_to_test:
        print("\n=== Testing Completion API ===")
        test_prompts = [
            "What is the capital of France?",
            "How do I prepare pasta?",
            "Write a short poem about technology"
        ]
        
        for i, prompt in enumerate(test_prompts):
            print(f"\nSending completion request {i+1}/{len(test_prompts)}:")
            print(f"Prompt: {prompt}")
            
            response = send_ai_completion_request(prompt, user_id)
            if response:
                print(f"AI Response: {response['choices'][0]['text'][:50]}...")
            
            # Short delay between requests
            time.sleep(1)
    
    # Test Embedding API
    if "embedding" in endpoints_to_test:
        print("\n=== Testing Embedding API ===")
        test_texts = [
            "This is a sample text to embed",
            "Neural networks are fascinating",
            "Machine learning is transforming industries"
        ]
        
        for i, text in enumerate(test_texts):
            print(f"\nSending embedding request {i+1}/{len(test_texts)}:")
            print(f"Text: {text}")
            
            response = send_ai_embedding_request(text, user_id)
            if response:
                print(f"Embedding created with ID: {response.get('id', 'unknown')}")
            
            # Short delay between requests
            time.sleep(1)
    
    # Test Similarity API
    if "similarity" in endpoints_to_test:
        print("\n=== Testing Similarity API ===")
        test_queries = [
            "artificial intelligence applications",
            "cloud computing technologies",
            "data science techniques"
        ]
        
        for i, query in enumerate(test_queries):
            print(f"\nSending similarity request {i+1}/{len(test_queries)}:")
            print(f"Query: {query}")
            
            response = send_ai_similarity_request(query, user_id)
            if response and 'results' in response:
                print(f"Found {len(response['results'])} similar results")
            
            # Short delay between requests
            time.sleep(1)
    
    # Test Image Processing API
    if "image" in endpoints_to_test:
        print("\n=== Testing Image Processing API ===")
        test_image_prompts = [
            "What is in this image?",
            "Describe this picture in detail",
            "What can you tell me about the animal in this photo?"
        ]
        
        for i, prompt in enumerate(test_image_prompts):
            print(f"\nSending image processing request {i+1}/{len(test_image_prompts)}:")
            print(f"Prompt: {prompt}")
            
            response = send_ai_image_request(prompt, user_id=user_id)
            if response:
                print(f"Image Analysis: {response.get('text', '')[:50]}...")
            
            # Short delay between requests
            time.sleep(1)
    
    # Test Text-to-Speech API
    if "tts" in endpoints_to_test:
        print("\n=== Testing TTS API ===")
        test_tts_texts = [
            "Hello, this is a test of the text-to-speech system.",
            "Artificial intelligence is revolutionizing how we interact with computers.",
            "Thank you for using our analytics integration system."
        ]
        
        for i, text in enumerate(test_tts_texts):
            print(f"\nSending TTS request {i+1}/{len(test_tts_texts)}:")
            print(f"Text: {text}")
            
            response = send_ai_tts_request(text, user_id)
            if response:
                print(f"TTS generated successfully. Audio size: {response.get('content_length', 0)} bytes")
            
            # Short delay between requests
            time.sleep(1)
    
    # Test Text-to-Speech with Emotion API
    if "tts_emotion" in endpoints_to_test:
        print("\n=== Testing TTS with Emotion API ===")
        test_tts_texts = [
            "I am very happy to see you today!",
            "This news makes me feel quite surprised and a bit worried.",
            "What an exciting development in artificial intelligence!"
        ]
        
        for i, text in enumerate(test_tts_texts):
            print(f"\nSending TTS with emotion request {i+1}/{len(test_tts_texts)}:")
            print(f"Text: {text}")
            
            response = send_ai_tts_emotion_request(text, user_id)
            if response:
                print(f"TTS with emotion generated successfully. Audio size: {response.get('content_length', 0)} bytes")
            
            # Short delay between requests
            time.sleep(1)
    
    # Give analytics service a moment to process
    print("\nWaiting for analytics service to process data...")
    time.sleep(2)
    
    # Check analytics data
    print("\nQuerying analytics service for AI usage data:")
    analytics_data = check_analytics_data(user_id)
    
    if analytics_data:
        print("\nAnalytics Data Summary:")
        print(f"Total API Calls: {analytics_data.get('totalAPICalls', 'N/A')}")
        print(f"Completion Calls: {analytics_data.get('completionCalls', 'N/A')}")
        print(f"Average Response Time: {analytics_data.get('averageResponseTime', 'N/A')}")
        print(f"Tokens Used: {analytics_data.get('tokensUsed', 'N/A')}")
        
        # Get detailed call distribution if available
        call_types = analytics_data.get('callTypeDistribution', {})
        if call_types:
            print("\nCall Type Distribution:")
            for call_type, count in call_types.items():
                print(f"  {call_type}: {count}")
        
        print("\nFull Analytics Response:")
        print(json.dumps(analytics_data, indent=2))
    else:
        print("Failed to retrieve analytics data")

if __name__ == "__main__":
    main() 