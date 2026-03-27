# Scoring Patterns

Category-specific scoring formulas for ranking and classifying discovered places.

## Universal Signals

These apply to all categories:

| Signal | Source | Weight |
|--------|--------|--------|
| `query_hit_count` | Number of distinct queries that found this place | High -- indicates relevance |
| `rating` | Google Maps rating (0-5) | Medium |
| `review_count` | Google Maps review count | Medium -- proxy for popularity |
| `status` | Open/closed/temporarily closed | Filter (closed = borderline) |

## Category-Specific Scoring

### Coffee

```python
quality_signal = 0
if "specialty" in all_categories.lower() or "third wave" in highlights.lower():
    quality_signal += 3
if "roaster" in all_categories.lower() or "roastery" in place_name.lower():
    quality_signal += 2
if "pour over" in offerings.lower() or "single origin" in offerings.lower():
    quality_signal += 2
if rating >= 4.5 and review_count >= 50:
    quality_signal += 1
if "wifi" in highlights.lower():
    quality_signal += 1  # workspace signal

is_third_wave = quality_signal >= 3
```

**Filter pills:** Third Wave, WiFi, Roasters, High Rated, New
**Sort options:** Rating, Reviews, Third Wave Score, Name

### Restaurant

```python
quality_signal = 0
if "fine dining" in all_categories.lower():
    quality_signal += 3
if any(w in highlights.lower() for w in ("michelin", "james beard", "award")):
    quality_signal += 3
if "outdoor" in highlights.lower() or "patio" in highlights.lower():
    quality_signal += 1
if rating >= 4.5 and review_count >= 100:
    quality_signal += 2
if price_level and len(price_level) >= 3:  # $$$+
    quality_signal += 1

is_fine_dining = quality_signal >= 3
```

**Filter pills:** Fine Dining, Outdoor, High Rated, $$$$, New
**Sort options:** Rating, Reviews, Price, Name

### Bar

```python
quality_signal = 0
if "cocktail" in all_categories.lower() or "craft" in highlights.lower():
    quality_signal += 3
if "speakeasy" in all_categories.lower():
    quality_signal += 2
if "craft beer" in offerings.lower() or "natural wine" in offerings.lower():
    quality_signal += 2
if "rooftop" in highlights.lower() or "live music" in highlights.lower():
    quality_signal += 1
if rating >= 4.3 and review_count >= 50:
    quality_signal += 1

is_craft = quality_signal >= 3
```

**Filter pills:** Cocktails, Craft Beer, Wine, Rooftop, Live Music, High Rated
**Sort options:** Rating, Reviews, Craft Score, Name

### Gym / Fitness

```python
quality_signal = 0
if any(w in all_categories.lower() for w in ("crossfit", "boutique", "studio")):
    quality_signal += 2
if "personal training" in offerings.lower():
    quality_signal += 1
if "classes" in highlights.lower() or "group" in highlights.lower():
    quality_signal += 1
if rating >= 4.5 and review_count >= 30:
    quality_signal += 2

is_boutique = quality_signal >= 3
```

**Filter pills:** Boutique, Classes, Personal Training, High Rated
**Sort options:** Rating, Reviews, Name

### Generic (fallback)

```python
quality_signal = 0
if rating >= 4.5:
    quality_signal += 2
if review_count >= 100:
    quality_signal += 1
if query_hit_count >= 3:
    quality_signal += 1

is_notable = quality_signal >= 2
```

**Filter pills:** High Rated, Popular, New
**Sort options:** Rating, Reviews, Name

## Borderline Detection

Flag a place as `borderline = true` if:

```python
borderline = (
    status != "open" or
    rating < 3.0 or
    (rating == 0 and review_count == 0) or  # no data
    query_hit_count == 1  # only found by one query
)
```

Borderline places are KEPT in the dataset (never filtered) but flagged for the user.
