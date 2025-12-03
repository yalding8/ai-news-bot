import feedparser
import concurrent.futures
from news_fetcher import NewsFetcher

def test_feeds():
    fetcher = NewsFetcher()
    results = {}
    
    print("Testing RSS Feeds...")
    print("-" * 60)
    print(f"{'Source':<40} | {'Status':<10} | {'Items':<5} | {'Latest Date'}")
    print("-" * 60)

    def check_feed(url):
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                return url, "Error", 0, str(feed.bozo_exception)[:20]
            
            count = len(feed.entries)
            latest = ""
            if count > 0:
                latest = feed.entries[0].get('published', feed.entries[0].get('updated', 'N/A'))
            
            return url, "OK", count, latest
        except Exception as e:
            return url, "Fail", 0, str(e)[:20]

    all_feeds = []
    for topic, feeds in fetcher.rss_feeds.items():
        for feed in feeds:
            if feed not in all_feeds:
                all_feeds.append(feed)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_feed, url): url for url in all_feeds}
        for future in concurrent.futures.as_completed(future_to_url):
            url, status, count, latest = future.result()
            print(f"{url[:40]:<40} | {status:<10} | {count:<5} | {latest}")

if __name__ == "__main__":
    test_feeds()
