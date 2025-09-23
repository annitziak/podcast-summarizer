import feedparser
import requests
import difflib


def _parse_episode(entry):
    """Helper function to parse a single episode entry."""
    title = entry.get("title", "Untitled Episode")
    pub_date = entry.get("published", "")
    
    # Get MP3 (audio enclosure)
    mp3_url = None
    if "enclosures" in entry and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("audio/"):
                mp3_url = enc.get("href")
                break

    # Look for transcript (podcast:transcript is a namespaced tag)
    transcript_url = None
    if "podcast_transcript" in entry:  # feedparser converts podcast:transcript → podcast_transcript
        t = entry.podcast_transcript
        if isinstance(t, list):
            transcript_url = t[0].get("url")
        elif isinstance(t, dict):
            transcript_url = t.get("url")

    return {
        "title": title,
        "date": pub_date,
        "mp3_url": mp3_url,
        "transcript_url": transcript_url,
    }


def fetch_castos_feed(rss_url: str):
    """
    Parse a Castos RSS feed.
    Returns a list of episodes with title, mp3 url, and transcript url (if available - not usual).
    """
    feed = feedparser.parse(rss_url)
    if feed.bozo: # feed.bozo is True if the feed is not well-formed
        raise RuntimeError(f"Invalid RSS feed: {rss_url}")

    show_title = feed.feed.get("title", "Unknown Show")
    print(f"Podcast: {show_title}\n")

    episodes = []
    for entry in feed.entries:
        episodes.append(_parse_episode(entry))

    return episodes

def find_episode(rss_url: str, query: str = None):
    """
    Efficiently find episodes from the RSS feed.
    
    Args:
        rss_url: The RSS feed URL
        query: Episode title to search for. If None, returns all episodes.
    
    Returns:
        If query is provided: Single episode dict or None
        If query is None: List of all episodes
    """
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        raise RuntimeError(f"Invalid RSS feed: {rss_url}")

    show_title = feed.feed.get("title", "Unknown Show")
    print(f"Podcast: {show_title}\n")
    
    # If no query, return all episodes (original behavior)
    if query is None:
        episodes = []
        for entry in feed.entries:
            episodes.append(_parse_episode(entry))
        return episodes
    
    # Search for specific episode efficiently
    query_lower = query.lower()
    
    # First pass: exact and partial matches (most efficient)
    for entry in feed.entries:
        title = entry.get("title", "Untitled Episode")
        title_lower = title.lower()
        
        # Exact match
        if query_lower == title_lower:
            return _parse_episode(entry)
        
        # Partial match - returns the first partial match found (can be enhanced later)
        if query_lower in title_lower:
            return _parse_episode(entry)
    
    # Second pass: fuzzy matching if no exact/partial match found
    titles = [entry.get("title", "Untitled Episode") for entry in feed.entries]
    best_matches = difflib.get_close_matches(query, titles, n=1, cutoff=0.4)
    
    if best_matches:
        best_title = best_matches[0]
        for entry in feed.entries:
            if entry.get("title", "Untitled Episode") == best_title:
                return _parse_episode(entry)
    
    return None


# Backward compatibility functions
def get_single_episode(rss_url: str, episode_title: str):
    """
    Fetch a single episode by title (backward compatibility).
    Use find_episode() for better fuzzy matching.
    """
    return find_episode(rss_url, episode_title)


def find_best_episode(rss_url: str, query: str):
    """
    Find best matching episode (backward compatibility).
    Use find_episode() instead.
    """
    return find_episode(rss_url, query)



if __name__ == "__main__":
    # Example Castos feed (replace with your target podcast endpoint)
    rss_url = "https://feeds.libsyn.com/452022/rss"  
    episode_title = "Azerbaijan GP Recap"

    if episode_title:
        episode = find_episode(rss_url, episode_title)
        if episode:
            print(f"Found episode: {episode['title']}")
            print(episode)
        else:
            print(f"No episode found matching: '{episode_title}'")
    else:
        episodes = find_episode(rss_url)  # No query = return all episodes
        for ep in episodes:
            print(f" {ep['title']} ({ep['date']})")
            print(f"   MP3: {ep['mp3_url']}")
            if ep["transcript_url"]:
                print(f"   Transcript: {ep['transcript_url']}")
            else:
                print("   Transcript: not available")
            print()
