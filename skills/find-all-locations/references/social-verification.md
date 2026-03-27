# Social Verification Guide

How to discover and verify Instagram, Facebook, and TikTok profiles for local businesses.

## Why `site:instagram.com` Beats `include_domains`

The Nimble Search API's `focus: "social"` + `include_domains: ["instagram.com"]` combination frequently returns TikTok, YouTube, and other social platforms instead of Instagram. The fix: use `site:instagram.com` directly in the query text with `focus: "general"`. This forces Google's `site:` operator to filter at the index level, which is much more reliable.

```python
# BAD — returns mixed social results
{"query": f'"{name}" {location} instagram', "focus": "social", "include_domains": ["instagram.com"]}

# GOOD — reliably returns only instagram.com results
{"query": f'"{name}" {location} site:instagram.com', "focus": "general", "num_results": 5}
```

## 3-Platform Coverage

### Instagram & Facebook (Nimble Web Search with `site:` operator)

3-strategy fallback per platform:

```python
SOCIAL_SEARCH_STRATEGIES = {
    "instagram": [
        # Strategy 1: Quoted name (exact match)
        lambda name, loc: f'"{name}" {loc} site:instagram.com',
        # Strategy 2: Unquoted (handles name variations)
        lambda name, loc: f'{name} {loc} site:instagram.com',
        # Strategy 3: Broadest (drops site: prefix style)
        lambda name, loc: f'{name} {loc} instagram.com',
    ],
    "facebook": [
        lambda name, loc: f'"{name}" {loc} site:facebook.com',
        lambda name, loc: f'{name} {loc} site:facebook.com',
        lambda name, loc: f'{name} {loc} facebook.com',
    ],
}
```

Stop at the first strategy that returns results containing the target platform domain. Each strategy is a separate Nimble Search API call.

### TikTok (Nimble Social API)

Two-step approach using Nimble's dedicated social endpoints:

1. **Primary:** `nimble_social_tiktok_discover_users` with query `"{place_name}"` — finds matching user profiles directly.
2. **Fallback:** `nimble_social_tiktok_search_posts` with query `"{place_name} {neighborhood}"` — extracts author profile URL from matching posts.

In the generated script, call these via REST to the Nimble API:
```python
# TikTok user discovery
POST https://sdk.nimbleway.com/v1/social/tiktok/discover_users
{"query": "{place_name}", "num_results": 5}

# TikTok post search (fallback)
POST https://sdk.nimbleway.com/v1/social/tiktok/search_posts
{"query": "{place_name} {neighborhood}", "num_results": 5}
```

## Confidence Scoring Model

Weighted signals for matching a social profile to a place:

| Signal | Weight | Description |
|--------|--------|-------------|
| `domain_match` | 60 | IG/FB bio links to the same domain as `website_url` (**strongest**) |
| `name_match_title` | 40 | Fuzzy name match in profile display name / title |
| `name_match_url` | 30 | Fuzzy name match in URL path (username) |
| `location_match` | 20 | City/neighborhood appears in bio text |
| `profile_page` | 10 | URL is a profile page, not a post/reel |

**Thresholds:** high >= 70, medium >= 40, low < 40

```python
def compute_social_confidence(place_name, place_address, website_url,
                               social_url, social_title, social_bio=""):
    score = 0
    reasons = []
    evidence = []

    # STRONGEST: Domain match (bio links to same domain as website_url)
    if website_url:
        website_domain = domain_of(website_url)
        if website_domain and website_domain in (social_bio or ""):
            score += 60
            reasons.append("domain_match")
            evidence.append(f"bio_links_to:{website_domain}")

    # Name match in profile title/username
    if fuzzy_name_match(place_name, social_title):
        score += 40
        reasons.append("name_match_title")
        evidence.append(f"title:{social_title[:40]}")

    # Name match in URL path
    path = urlparse(social_url).path.strip("/").split("/")[0]
    if fuzzy_name_match(place_name, path):
        score += 30
        reasons.append("name_match_url")
        evidence.append(f"path:/{path}")

    # Location match in bio
    city = extract_city(place_address)
    if city and city.lower() in (social_bio or "").lower():
        score += 20
        reasons.append("location_match")
        evidence.append(f"bio_contains:{city}")

    # Profile page (not post/reel)
    if is_profile_page(social_url):
        score += 10
        reasons.append("profile_page")

    # Confidence level
    if score >= 70:
        confidence = "high"
    elif score >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    return confidence, "; ".join(reasons), " | ".join(evidence)
```

## Evidence Storage

Each match stores a human-readable evidence snippet in `{platform}_evidence` column for auditability:

```
"bio_links_to:seycoffee.com | title:SEY Coffee (@seycoffee)"
"name_match_title; name_match_url | title:Devocion Coffee | path:/devocionusa"
```

## Profile URL Validation Patterns

```python
def is_profile_page(url):
    """Check if URL is a profile page (not a post/reel/event)."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    host = parsed.hostname or ""

    if "instagram.com" in host:
        # Valid profile: single path segment, not a content type
        return (len(parts) == 1 and
                parts[0] not in ("p", "reel", "stories", "explore", "accounts", "directory"))

    if "facebook.com" in host:
        # Valid profile/page: not an event/post/photo/video subpath
        return not (len(parts) >= 2 and
                    parts[-1] in ("events", "posts", "photos", "videos", "groups", "reviews"))

    if "tiktok.com" in host:
        # Valid profile: @username format
        return len(parts) == 1 and parts[0].startswith("@")

    return False
```

## Verification Flow

```
For each place_id:
  For each platform (instagram, facebook, tiktok):
    1. Search → get candidate URLs + titles + snippets
    2. Pick best candidate (profile page preferred, name match preferred)
    3. Score confidence using compute_social_confidence()
    4. Store: {platform}_url, {platform}_verified, {platform}_confidence,
             {platform}_match_reason, {platform}_evidence
```

## Rerun Behavior

- **Skip:** place_ids where `{platform}_verified == true` AND `{platform}_confidence == "high"`
- **Retry:** place_ids where `{platform}_confidence == "low"` (may improve with new data or different search strategy)
- **Process:** place_ids where `{platform}_url` is empty or `social_status` is pending/error
