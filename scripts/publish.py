import os
import feedparser
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

RSS_FEED_URL = "https://news.google.com/rss/search?q=trending+movies&hl=en-US&gl=US&ceid=US:en"
BLOG_LABEL = "Trending Movies"
MAX_ITEMS = 8

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.6-flash')

creds = Credentials(
    token=None,
    refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["BLOGGER_CLIENT_ID"],
    client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/blogger"]
)
blogger_service = build('blogger', 'v3', credentials=creds)
BLOG_ID = os.environ["BLOGGER_BLOG_ID"]


def process_entry(entry):
    title = entry.title
    description = entry.get('summary', '')
    link = entry.link
    print(f"Processing: {title}")

    prompt = f"""
You are a professional entertainment journalist and content writer. Your task is to rewrite the provided movie news into a completely new, original, and engaging blog article.

Follow these strict rules:
1. Output ONLY the final article. Do not include any explanations, intro text, or markdown.
2. Create a NEW, catchy, SEO-friendly TITLE related to movies. The title must be plain text only - NO HTML tags.
3. The FIRST line of your output must be the title (plain text), followed by a blank line.
4. After the title, write the article body of about 300-400 words in clean HTML using only <p>, <h2>, <h3>, <strong>, and <ul> tags. Do NOT use <h1> or <title> in the body.
5. Focus on movie-specific details: box office, cast, director, release date, reviews, or plot (whichever is relevant).
6. Do not copy sentences from the source. Completely rewrite the information in your own words.
7. At the end, add a single line: "Source: {link}".
8. Return ONLY the title and HTML body. Nothing else.

Here is the source news item:
Original Title: {title}
Original Description: {description}
"""
    try:
        response = model.generate_content(prompt)
        full_content = response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return

    lines = full_content.split('\n', 1)
    if len(lines) < 2:
        print("Error: no title/body in response")
        return
    new_title = lines[0].strip()
    new_body = lines[1].strip()

    post_body = {
        "kind": "blogger#post",
        "title": new_title,
        "content": new_body,
        "labels": [BLOG_LABEL]
    }
    try:
        posts = blogger_service.posts()
        posts.insert(blogId=BLOG_ID, body=post_body, isDraft=False).execute()
        print(f"Posted: {new_title}")
    except Exception as e:
        print(f"Blogger error: {e}")


def main():
    print(f"Fetching: {RSS_FEED_URL}")
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        print("No entries found")
        return
    count = min(MAX_ITEMS, len(feed.entries))
    for i in range(count):
        process_entry(feed.entries[i])
        print(f"--- {i+1}/{count} done ---")


if __name__ == "__main__":
    main()
