import feedparser
import os

# Secrets에서 주소를 가져오되, /rss가 없으면 자동으로 붙여줍니다.
RAW_URL = os.environ.get('TISTORY_RSS_URL', '')
RSS_URL = RAW_URL if RAW_URL.endswith('/rss') else RAW_URL.rstrip('/') + '/rss'

def fetch_and_save():
    if not RAW_URL:
        print("TISTORY_RSS_URL is not set!")
        return
    
    print(f"📡 Fetching from: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ 가져올 포스트가 없습니다. RSS 주소를 확인해주세요.")
        return

    posts_dir = 'posts'
    os.makedirs(posts_dir, exist_ok=True)
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        published = entry.get('published', entry.get('updated', ''))
        content = entry.get('description', entry.get('summary', '내용 없음'))
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        filename = f"{safe_title}.md"
        filepath = os.path.join(posts_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**발행일:** {published}\n\n")
            f.write(f"**링크:** {link}\n\n")
            f.write("---\n\n")
            f.write(content)
    
    print(f"✅ {len(feed.entries)}개의 포스트가 성공적으로 동기화되었습니다!")

if __name__ == '__main__':
    fetch_and_save()
