import requests
from bs4 import BeautifulSoup, FeatureNotFound
import re
import argparse
from datetime import datetime
import pyperclip


def get_youtube_source_code(youtube_url):
    """Fetches the source code of a YouTube page."""
    try:
        response = requests.get(youtube_url)
        response.raise_for_status()  # Check for bad status codes
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None


def get_youtube_channel_id(source_code):
    """Extracts the channel ID from the YouTube source code."""
    if source_code is None:
        return None

    soup = BeautifulSoup(source_code, "html.parser")

    # Method 1: Meta tag (most reliable)
    meta_tag = soup.find("meta", property="og:url")
    if meta_tag:
        og_url = meta_tag.get("content")
        match = re.search(r"/channel/([UC][a-zA-Z0-9_-]+)", og_url)
        if match:
            return match.group(1)

    # Method 2: Script tags (fallback)
    script_tags = soup.find_all("script")
    for script in script_tags:
        script_content = str(script)
        match = re.search(r"\"channel_id\":\"([UC][a-zA-Z0-9_-]+)\"", script_content)
        if match:
            return match.group(1)

    return None


def create_rss_feed_url(channel_id):
    """Creates the RSS feed URL from the channel ID."""
    if channel_id:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return None


def fetch_rss_feed_content(rss_feed_url, limit=5):
    """Fetches and parses the RSS feed content, limited to the latest videos."""
    try:
        response = requests.get(rss_feed_url)
        response.raise_for_status()
        try:
            soup = BeautifulSoup(response.content, "xml")
        except FeatureNotFound:
            print("Error: Couldn't find a tree builder with the features you requested: xml. Please install the 'lxml' parser library using 'pip install lxml'.")
            return None
        entries = soup.find_all("entry")[:limit]
        return entries
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        return None


def filter_videos(entries, filter_by=None, filter_value=None):
    """Filters videos by date, title, or other metadata."""
    filtered_videos = []
    for entry in entries:
        title = entry.find("title").text
        published = entry.find("published").text
        link = entry.find("link")["href"]

        if filter_by == "date":
            entry_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S%z")
            filter_date = datetime.strptime(filter_value, "%Y-%m-%d")
            if entry_date.date() == filter_date.date():
                filtered_videos.append(
                    {"title": title, "published": published, "link": link}
                )
        elif filter_by == "title" and filter_value.lower() in title.lower():
            filtered_videos.append(
                {"title": title, "published": published, "link": link}
            )
        else:
            filtered_videos.append(
                {"title": title, "published": published, "link": link}
            )
    return filtered_videos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert YouTube channel URL to RSS feed URL and fetch latest videos.",
        epilog="Example usage: python main.py https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw --filter_by date --filter_value 2023-10-01",
    )
    parser.add_argument("youtube_url", help="The YouTube channel URL")
    parser.add_argument(
        "--filter_by", choices=["date", "title"], help="Filter videos by date or title"
    )
    parser.add_argument(
        "--filter_value",
        help="Value to filter videos by (e.g., date in YYYY-MM-DD format or title keyword)",
    )
    args = parser.parse_args()

    youtube_url = args.youtube_url

    source_code = get_youtube_source_code(youtube_url)
    if source_code:
        channel_id = get_youtube_channel_id(source_code)
        if channel_id:
            rss_feed_url = create_rss_feed_url(channel_id)
            if rss_feed_url:
                print(f"Channel ID: {channel_id}")
                print(f"RSS Feed URL: {rss_feed_url}")
                pyperclip.copy(rss_feed_url)  # Copy RSS feed URL to clipboard
                print("RSS feed URL has been copied to the clipboard.")

                entries = fetch_rss_feed_content(rss_feed_url)
                if entries:
                    filtered_videos = filter_videos(
                        entries, args.filter_by, args.filter_value
                    )
                    for video in filtered_videos:
                        print(f"Title: {video['title']}")
                        print(f"Published: {video['published']}")
                        print(f"Link: {video['link']}\n")
                else:
                    print("Could not fetch RSS feed content.")
            else:
                print("Could not create RSS feed URL.")
        else:
            print("Channel ID not found.")
