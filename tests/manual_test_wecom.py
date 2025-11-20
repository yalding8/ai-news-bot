import logging
import os
import sys

# Add parent directory to path to import bot_wecom
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_wecom import get_news

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_get_news():
    print("Testing get_news for 'ai' topic (WeCom)...")
    
    result = get_news('ai')
    
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    print(result)
    print("="*50)
    
    if "❌" in result: 
        print("Error: News fetching failed.")
    elif "⚠️" in result:
        print("Warning: News fetching might have returned empty or partial results.")
    else:
        print("Success: News content generated.")

    # Check if links are present
    if "🔗 新闻原文链接" in result:
        print("Success: Links section found.")
    else:
        print("Failure: Links section missing.")

if __name__ == "__main__":
    test_get_news()
