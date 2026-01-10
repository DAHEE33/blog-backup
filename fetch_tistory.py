import feedparser
import os
from datetime import datetime

RSS_URL = os.environ.get('TISTORY_RSS_URL', '')

def fetch_and_save():
    if not RSS_URL:
        print("TISTORY_RSS_URL is not set!")
        return
    
    print(f"📡 Fetching from: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    posts_dir = 'posts'
    os.makedirs(posts_dir, exist_ok=True)
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        published = entry.get('published', '')
        content = entry.get('description', entry.get('summary', ''))
        
        # 안전한 파일명 생성
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        filename = f"{safe_title}.md"
        
        filepath = os.path.join(posts_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**발행일:** {published}\n\n")
            f.write(f"**링크:** {link}\n\n")
            f.write("---\n\n")
            f.write(content)
    
    print(f"{len(feed.entries)}개의 포스트가 동기화되었습니다!")

if __name__ == '__main__':
    fetch_and_save()
