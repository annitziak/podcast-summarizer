import feedparser, difflib

def parse_episode(entry):
    """Extract title and mp3 URL from a feed entry."""
    title = entry.get("title", "Untitled Episode")
    mp3_url = None
    if "enclosures" in entry and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("audio/"):
                mp3_url = enc.get("href")
                break
    return {"title": title, "mp3_url": mp3_url}

def find_episode(rss_url: str, query: str = None):
    """Fetch and parse RSS feed, returning episode matching query or closest match."""
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        raise RuntimeError(f"Invalid RSS feed: {rss_url}")

    if query is None:
        return [parse_episode(e) for e in feed.entries]

    query_lower = query.lower()
    for entry in feed.entries:
        if query_lower in entry.get("title", "").lower():
            return parse_episode(entry)

    titles = [e.get("title", "Untitled") for e in feed.entries]
    best = difflib.get_close_matches(query, titles, n=1, cutoff=0.4) # sometimes the titles are long and not exact
    if best:
        return parse_episode(next(e for e in feed.entries if e["title"] == best[0]))

    return None
