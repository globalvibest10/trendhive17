import os
import feedparser
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

RSS_FEED_URL = "https://news.google.com/rss/search?q=trending+movies+2026&hl=en-US&gl=US&ceid=US:en"
BLOG_LABEL = "Trending Movies"

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash')

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


def main():
    print(f"Fetching RSS feed: {RSS_FEED_URL}")
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        print("No entries found in the feed.")
        return

    latest_entry = feed.entries[0]
    title = latest_entry.title
    description = latest_entry.get('summary', '')
    link = latest_entry.link
    print(f"Processing article: {title}")

    prompt = f"""
You are a professional news editor and content writer. Your task is to rewrite the provided news item into a completely new, original, and engaging blog article.

Follow these strict rules:
1. Output ONLY the final article. Do not include any explanations, intro text, or markdown.
2. Create a NEW, catchy, SEO-friendly TITLE. The title must be plain text only - NO HTML tags.
3. The FIRST line of your output must be the title (plain text), followed by a blank line.
4. After the title, write the article body of about 300-400 words in clean HTML using only <p>, <h2>, <h3>, <strong>, and <ul> tags. Do NOT use <h1> or <title> in the body.
5. Do not copy sentences from the source. Completely rewrite the information in your own words.
6. At the end, add a single line: "Source: {link}".
7. Return ONLY the title and HTML body. Nothing else.

Here is the source news item:
Original Title: {title}
Original Description: {description}
"""
    print("Generating content with Gemini...")
    response = model.generate_content(prompt)
    full_content = response.text

    lines = full_content.split('\n', 1)
    if len(lines) < 2:
        print("Error: Gemini response did not contain a title and body.")
        return
    new_title = lines[0].strip()
    new_body = lines[1].strip()

    print(f"Publishing to Blogger with label: {BLOG_LABEL}")
    post_body = {
        "kind": "blogger#post",
        "title": new_title,
        "content": new_body,
        "labels": [BLOG_LABEL]
    }
    try:
        posts = blogger_service.posts()
        posts.insert(blogId=BLOG_ID, body=post_body, isDraft=True).execute()
        print("Successfully created a new draft post on Blogger.")
    except Exception as e:
        print(f"An error occurred while posting to Blogger: {e}")


if __name__ == "__main__":
    main()
